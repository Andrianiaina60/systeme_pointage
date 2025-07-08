# utils/face_recognition_utils.py
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import pickle
import os
import logging
from django.conf import settings
from typing import Optional, List, Tuple, Dict
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class FaceRecognitionHandler:
    """
    Gestionnaire de reconnaissance faciale utilisant MediaPipe
    """
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialiser les modèles MediaPipe
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        self.encodings_file = settings.FACE_RECOGNITION_SETTINGS['ENCODINGS_FILE']
        self.tolerance = settings.FACE_RECOGNITION_SETTINGS['TOLERANCE']
        
    def preprocess_image(self, image_data) -> Optional[np.ndarray]:
        """
        Préprocesser l'image pour la reconnaissance faciale.

        Gère les cas suivants :
        - Image en base64 (avec ou sans préfixe data:image)
        - Objet PIL.Image
        - Numpy array
        - Chemin de fichier image sur disque
        """
        try:
            image = None

            # Si image_data est un string (base64 ou chemin de fichier)
            if isinstance(image_data, str):
                # Si c'est un chemin de fichier valide
                if os.path.exists(image_data):
                    image = cv2.imread(image_data)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # Si c'est une image base64 (avec ou sans préfixe)
                elif image_data.startswith('data:image') or len(image_data) > 100:
                    try:
                        if image_data.startswith('data:image'):
                            image_data = image_data.split(',')[1]
                        image_bytes = base64.b64decode(image_data)
                        pil_image = Image.open(BytesIO(image_bytes)).convert('RGB')
                        image = np.array(pil_image)
                    except Exception as decode_error:
                        logger.error(f"Erreur lors du décodage de l'image base64: {decode_error}")
                        return None
                else:
                    logger.error("Chaîne reçue mais ni base64 ni chemin de fichier valide.")
                    return None

            # Si c'est un objet PIL
            elif isinstance(image_data, Image.Image):
                image = np.array(image_data)

            # Si c'est déjà un array numpy
            elif isinstance(image_data, np.ndarray):
                image = image_data

            else:
                logger.error("Format d'image non supporté")
                return None

            # Vérifie que l'image est bien un tableau 2D ou 3D
            if image is None or not isinstance(image, np.ndarray):
                logger.error("L'image n'a pas pu être convertie en array numpy")
                return None

            # Redimensionner si nécessaire
            max_size = settings.FACE_RECOGNITION_SETTINGS['MAX_IMAGE_SIZE']
            height, width = image.shape[:2]

            if max(height, width) > max_size:
                if height > width:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                else:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                image = cv2.resize(image, (new_width, new_height))

            logger.debug(f"Image prétraitée avec succès: shape = {image.shape}")
            return image

        except Exception as e:
            logger.error(f"Erreur lors du préprocessing de l'image: {e}")
            return None

    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Détecter les visages dans une image
        """
        try:
            # Convertir en RGB si nécessaire
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            results = self.face_detection.process(rgb_image)
            faces = []
            
            if results.detections:
                for detection in results.detections:
                    # Extraire les coordonnées du visage
                    bbox = detection.location_data.relative_bounding_box
                    h, w = image.shape[:2]
                    
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    faces.append({
                        'bbox': (x, y, width, height),
                        'confidence': detection.score[0],
                        'landmarks': None
                    })
            
            return faces
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection de visages: {e}")
            return []
    
    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extraire l'encodage facial d'une image
        """
        try:
            # Convertir en RGB si nécessaire
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # Utiliser FaceMesh pour extraire les landmarks
            results = self.face_mesh.process(rgb_image)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # Extraire les coordonnées des landmarks
                landmarks = []
                for landmark in face_landmarks.landmark:
                    landmarks.extend([landmark.x, landmark.y, landmark.z])
                
                return np.array(landmarks)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'encodage: {e}")
            return None
    
    def save_face_encoding(self, employee_id: int, encoding: np.ndarray) -> bool:
        """
        Sauvegarder l'encodage facial d'un employé
        """
        try:
            # Charger les encodages existants
            encodings_data = self.load_face_encodings()
            
            # Ajouter le nouvel encodage
            encodings_data[str(employee_id)] = encoding.tolist()
            
            # Sauvegarder
            os.makedirs(os.path.dirname(self.encodings_file), exist_ok=True)
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(encodings_data, f)
            
            logger.info(f"Encodage sauvegardé pour l'employé {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde d'encodage: {e}")
            return False
    
    def load_face_encodings(self) -> Dict:
        """
        Charger tous les encodages faciaux
        """
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    return pickle.load(f)
            return {}
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des encodages: {e}")
            return {}
    
    def compare_faces(self, known_encoding: np.ndarray, face_encoding: np.ndarray) -> float:
        """
        Comparer deux encodages faciaux et retourner la distance
        """
        try:
            # Calculer la distance euclidienne
            distance = np.linalg.norm(known_encoding - face_encoding)
            return distance
            
        except Exception as e:
            logger.error(f"Erreur lors de la comparaison: {e}")
            return float('inf')
    
    def recognize_face(self, image_data) -> Optional[int]:
        """
        Reconnaître un visage et retourner l'ID de l'employé
        """
        try:
            # Préprocesser l'image
            image = self.preprocess_image(image_data)
            if image is None:
                return None
            
            # Extraire l'encodage du visage
            face_encoding = self.extract_face_encoding(image)
            if face_encoding is None:
                logger.warning("Aucun visage détecté dans l'image")
                return None
            
            # Charger les encodages connus
            known_encodings = self.load_face_encodings()
            if not known_encodings:
                logger.warning("Aucun encodage facial enregistré")
                return None
            
            # Comparer avec tous les encodages connus
            best_match_id = None
            best_distance = float('inf')
            
            for employee_id, known_encoding in known_encodings.items():
                known_encoding = np.array(known_encoding)
                distance = self.compare_faces(known_encoding, face_encoding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_id = int(employee_id)
            
            # Vérifier si la distance est dans la tolérance
            if best_distance <= self.tolerance:
                logger.info(f"Visage reconnu: employé {best_match_id} (distance: {best_distance})")
                return best_match_id
            else:
                logger.warning(f"Visage non reconnu (meilleure distance: {best_distance})")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la reconnaissance faciale: {e}")
            return None
    
    def register_face(self, employee_id: int, image_data) -> bool:
        """
        Enregistrer un nouveau visage pour un employé
        """
        try:
            # Préprocesser l'image
            image = self.preprocess_image(image_data)
            if image is None:
                return False
            
            # Vérifier qu'il y a un visage dans l'image
            faces = self.detect_faces(image)
            if not faces:
                logger.error("Aucun visage détecté dans l'image")
                return False
            
            if len(faces) > 1:
                logger.error("Plusieurs visages détectés. Une seule personne doit être présente.")
                return False
            
            # Extraire l'encodage
            face_encoding = self.extract_face_encoding(image)
            if face_encoding is None:
                logger.error("Impossible d'extraire l'encodage facial")
                return False
            
            # Sauvegarder l'encodage
            success = self.save_face_encoding(employee_id, face_encoding)
            
            if success:
                # Sauvegarder aussi l'image
                image_path = os.path.join(
                    settings.FACE_IMAGES_DIR, 
                    f"employee_{employee_id}.jpg"
                )
                cv2.imwrite(image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
                
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du visage: {e}")
            return False
    
    def delete_face_encoding(self, employee_id: int) -> bool:
        """
        Supprimer l'encodage facial d'un employé
        """
        try:
            # Charger les encodages existants
            encodings_data = self.load_face_encodings()
            
            # Supprimer l'encodage
            if str(employee_id) in encodings_data:
                del encodings_data[str(employee_id)]
                
                # Sauvegarder
                with open(self.encodings_file, 'wb') as f:
                    pickle.dump(encodings_data, f)
                
                # Supprimer l'image associée
                image_path = os.path.join(
                    settings.FACE_IMAGES_DIR, 
                    f"employee_{employee_id}.jpg"
                )
                if os.path.exists(image_path):
                    os.remove(image_path)
                
                logger.info(f"Encodage supprimé pour l'employé {employee_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'encodage: {e}")
            return False
    
    def validate_image_quality(self, image_data) -> Dict[str, any]:
        """
        Valider la qualité d'une image pour la reconnaissance faciale
        """
        try:
            image = self.preprocess_image(image_data)
            if image is None:
                return {
                    'valid': False,
                    'message': 'Image invalide ou format non supporté'
                }
            
            # Vérifier la résolution
            height, width = image.shape[:2]
            if height < 200 or width < 200:
                return {
                    'valid': False,
                    'message': 'Résolution trop faible (minimum 200x200)'
                }
            
            # Détecter les visages
            faces = self.detect_faces(image)
            
            if not faces:
                return {
                    'valid': False,
                    'message': 'Aucun visage détecté'
                }
            
            if len(faces) > 1:
                return {
                    'valid': False,
                    'message': 'Plusieurs visages détectés. Une seule personne doit être présente.'
                }
            
            face = faces[0]
            
            # Vérifier la confiance de détection
            if face['confidence'] < 0.7:
                return {
                    'valid': False,
                    'message': 'Qualité de détection du visage insuffisante'
                }
            
            # Vérifier la taille du visage
            bbox = face['bbox']
            face_width = bbox[2]
            face_height = bbox[3]
            
            if face_width < 100 or face_height < 100:
                return {
                    'valid': False,
                    'message': 'Visage trop petit dans l\'image'
                }
            
            return {
                'valid': True,
                'message': 'Image valide pour la reconnaissance faciale',
                'face_confidence': face['confidence'],
                'face_size': (face_width, face_height)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {e}")
            return {
                'valid': False,
                'message': 'Erreur lors de la validation de l\'image'
            }

# Instance globale du gestionnaire
face_recognition_handler = FaceRecognitionHandler()

# Ajoutez ces fonctions à la fin de votre fichier face_recognition_utils.py

def extract_face_encoding(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Fonction wrapper qui utilise le gestionnaire principal
    """
    return face_recognition_handler.extract_face_encoding(image)

def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=None):
    """
    Fonction wrapper pour la compatibilité avec l'ancienne API
    Args:
        known_face_encodings: Liste d'encodages connus
        face_encoding_to_check: Encodage à vérifier
        tolerance: Seuil de tolérance (optionnel)
    Returns:
        Liste de booléens indiquant les correspondances
    """
    if tolerance is None:
        tolerance = face_recognition_handler.tolerance
    
    if not isinstance(known_face_encodings, list):
        known_face_encodings = [known_face_encodings]
    
    matches = []
    for known_encoding in known_face_encodings:
        distance = face_recognition_handler.compare_faces(
            np.array(known_encoding), 
            np.array(face_encoding_to_check)
        )
        matches.append(distance <= tolerance)
    
    return matches

def load_biometric_data(file_path: str) -> Optional[np.ndarray]:
    """
    Charger les données biométriques depuis un fichier
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Fichier biométrique introuvable: {file_path}")
            return None
        
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            return np.array(data) if data is not None else None
            
    except Exception as e:
        logger.error(f"Erreur lors du chargement des données biométriques: {e}")
        return None

def save_biometric_data(employee_id: int, face_encoding: np.ndarray) -> str:
    """
    Sauvegarder les données biométriques et retourner le chemin du fichier
    """
    try:
        # Créer le répertoire s'il n'existe pas
        biometric_dir = os.path.join(settings.MEDIA_ROOT, 'biometric_data')
        os.makedirs(biometric_dir, exist_ok=True)
        
        # Nom du fichier
        filename = f"employee_{employee_id}_biometric.pkl"
        file_path = os.path.join(biometric_dir, filename)
        
        # Sauvegarder l'encodage
        with open(file_path, 'wb') as f:
            pickle.dump(face_encoding.tolist(), f)
        
        # Retourner le chemin relatif pour Django
        return os.path.join('biometric_data', filename)
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des données biométriques: {e}")
        raise

def process_face_image(image_data) -> Optional[np.ndarray]:
    """
    Traiter une image de visage (wrapper pour preprocess_image)
    """
    return face_recognition_handler.preprocess_image(image_data)
