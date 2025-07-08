
from rest_framework import serializers
from .models import Department

# ✅ Champ personnalisé pour filtrer les managers
class ManagerPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        from employees.models import Employee  # import dynamique pour éviter les imports circulaires
        return Employee.objects.filter(poste='manager')

# ✅ Serializer simple (ex: pour listes)
class SimpleDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'nom']

# ✅ Serializer principal avec validation manager unique
class DepartmentSerializer(serializers.ModelSerializer):
    employees_count = serializers.SerializerMethodField()
    manager = serializers.SerializerMethodField()  # lecture seule
    manager_id = ManagerPrimaryKeyRelatedField(   # écriture uniquement
        source='manager',
        write_only=True,
        required=False
    )

    class Meta:
        model = Department
        fields = [
            'id', 'nom', 'description',
            'manager', 'manager_id',
            'employees_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'employees_count', 'manager'
        ]

    def get_employees_count(self, obj):
        return obj.employees.filter(is_active_employee=True).count()

    def get_manager(self, obj):
        from employees.serializers import SimpleEmployeeSerializer  # import dynamique
        if obj.manager:
            return SimpleEmployeeSerializer(obj.manager).data
        return None

    # 🔒 Validation pour qu’un manager ne soit assigné qu’à un seul département
    def validate(self, data):
        manager = data.get('manager')
        instance = getattr(self, 'instance', None)

        if manager:
            existing = Department.objects.filter(manager=manager)
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError({
                    'manager_id': "Ce manager est déjà affecté à un autre département."
                })

        return data

# ✅ Serializer simplifié pour la création
class DepartmentCreateSerializer(serializers.ModelSerializer):
    manager_id = ManagerPrimaryKeyRelatedField(
        source='manager',
        write_only=True,
        required=False
    )

    class Meta:
        model = Department
        fields = ['nom', 'description', 'manager_id']

    # 🔒 Même validation que ci-dessus
    def validate(self, data):
        manager = data.get('manager')
        if manager and Department.objects.filter(manager=manager).exists():
            raise serializers.ValidationError({
                'manager_id': "Ce manager est déjà affecté à un autre département."
            })
        return data







# from rest_framework import serializers
# from .models import Department

# # ✅ Champ personnalisé pour éviter queryset statique au moment du chargement
# class ManagerPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
#     def get_queryset(self):
#         from employees.models import Employee  # import dynamique pour éviter les imports circulaires
#         return Employee.objects.filter(poste='manager')

# # ✅ Serializer simple (pour Employee) importé dynamiquement pour éviter ImportError
# class SimpleDepartmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Department
#         fields = ['id', 'nom']

# class DepartmentSerializer(serializers.ModelSerializer):
#     employees_count = serializers.SerializerMethodField()
#     manager = serializers.SerializerMethodField()
#     manager_id = ManagerPrimaryKeyRelatedField(  # ✅ utilisé ici
#         source='manager',
#         write_only=True,
#         required=False
#     )

#     class Meta:
#         model = Department
#         fields = [
#             'id', 'nom', 'description',
#             'manager', 'manager_id',
#             'employees_count', 'created_at', 'updated_at'
#         ]
#         read_only_fields = [
#             'id', 'created_at', 'updated_at',
#             'employees_count', 'manager'
#         ]

#     def get_employees_count(self, obj):
#         return obj.employees.filter(is_active_employee=True).count()

#     def get_manager(self, obj):
#         from employees.serializers import SimpleEmployeeSerializer  # import dynamique
#         if obj.manager:
#             return SimpleEmployeeSerializer(obj.manager).data
#         return None

# class DepartmentCreateSerializer(serializers.ModelSerializer):
#     manager_id = ManagerPrimaryKeyRelatedField(
#         source='manager',
#         write_only=True,
#         required=False
#     )

#     class Meta:
#         model = Department
#         fields = ['nom', 'description', 'manager_id']
