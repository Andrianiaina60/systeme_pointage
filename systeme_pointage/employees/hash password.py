# Toujours utiliser set_password() pour enregistrer un mot de passe
from authentication.models import Authentication

# Récupérer l'utilisateur
auth = Authentication.objects.get(email="andry@gmail.com")

# Hasher le mot de passe correctement
auth.set_password("andry[1234]")

# Sauvegarder la modification
auth.save()

# Optionnel : Corriger tous les mots de passe non hashés
from authentication.models import Authentication

for auth in Authentication.objects.all():
    raw_pass = auth.password
    # Simple test pour voir si le password semble non hashé (ex: pas de "$" dans la chaine)
    if not raw_pass.startswith('pbkdf2_'):  
        # Exemple d'action: demander le nouveau mot de passe à l'utilisateur ou réinitialiser
        print(f"Attention: {auth.email} a un mot de passe non hashé.")
        # Tu peux choisir de forcer un reset ou autre...
