# pointage/serializers.py
from rest_framework import serializers
from .models import Pointage

class PointageSerializer(serializers.ModelSerializer):
    heure_entree_str = serializers.SerializerMethodField()
    heure_sortie_str = serializers.SerializerMethodField()
    temps_travaille_str = serializers.SerializerMethodField()

    class Meta:
        model = Pointage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'temps_travaille', 'heures_supplementaires', 'retard']

    def get_heure_entree_str(self, obj):
        return obj.heure_entree.strftime('%H:%M') if obj.heure_entree else None

    def get_heure_sortie_str(self, obj):
        return obj.heure_sortie.strftime('%H:%M') if obj.heure_sortie else None

    def get_temps_travaille_str(self, obj):
        if obj.temps_travaille:
            total_seconds = int(obj.temps_travaille.total_seconds())
            heures = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{heures}h {minutes}min"
        return None
