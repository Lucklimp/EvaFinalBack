from rest_framework import serializers
from .models import User, Company, Subscription, Product, Branch, Sale

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    company_name = serializers.CharField(write_only=True, required=False) # Para crear empresa al registrarse

    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'rut', 'company_name')

    def create(self, validated_data):
        company_name = validated_data.pop('company_name', None)
        password = validated_data.pop('password')
        
        # 1. Crear Usuario
        user = User(**validated_data)
        user.set_password(password)
        user.role = 'admin_cliente' # Por defecto quien se registra es Admin
        
        # 2. Crear Company si viene el nombre
        if company_name:
            company = Company.objects.create(name=company_name, rut=validated_data.get('rut', ''))
            user.company = company
        
        user.save()
        return user

class UserManagementSerializer(serializers.ModelSerializer):
    """ Para que el AdminCliente cree Gerentes/Vendedores """
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'role', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        # El company se asigna en la vista basado en el request.user
        return user

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('company',) # Company se asigna auto

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ('company',)