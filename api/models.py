from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator
from .validators import validar_rut_chileno, validar_positivo, validar_fecha_pasada

# ==========================================
# MÓDULO 1: NÚCLEO Y MULTI-TENANCY
# ==========================================

class Company(models.Model):
    name = models.CharField(max_length=100)
    # Aplicamos validador de RUT
    rut = models.CharField(max_length=12, validators=[validar_rut_chileno]) 
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Plan(models.Model):
    name = models.CharField(max_length=50)
    max_branches = models.IntegerField(default=1, validators=[validar_positivo])
    max_users = models.IntegerField(default=5, validators=[validar_positivo])
    price = models.DecimalField(max_digits=10, decimal_places=0, validators=[validar_positivo])

    def __str__(self):
        return self.name

class Subscription(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        # Validación lógica: Fecha fin no puede ser antes que fecha inicio
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("La fecha de término debe ser posterior a la de inicio.")

    def __str__(self):
        return f"{self.company.name} - {self.plan.name}"

# TABLA USUARIO
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLES = (
        ('super_admin', 'Super Admin'), 
        ('admin_cliente', 'Admin Cliente'), 
        ('gerente', 'Gerente'), 
        ('vendedor', 'Vendedor'), 
        ('cliente_final', 'Cliente Ecommerce'),
    )
    username = None 
    email = models.EmailField(unique=True)
    rut = models.CharField(max_length=12, blank=True, null=True, validators=[validar_rut_chileno]) # Validador
    role = models.CharField(max_length=20, choices=ROLES, default='cliente_final')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='users')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

# ==========================================
# MÓDULO 2: LOGÍSTICA Y PRODUCTOS
# ==========================================

class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, validators=[validar_rut_chileno]) # Validador
    contact_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # Precios no negativos
    price = models.DecimalField(max_digits=10, decimal_places=0, validators=[validar_positivo])
    cost = models.DecimalField(max_digits=10, decimal_places=0, validators=[validar_positivo])
    
    class Meta:
        unique_together = ('company', 'sku')

    def __str__(self):
        return self.name

class Inventory(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0, validators=[validar_positivo]) # Stock no negativo
    min_stock = models.IntegerField(default=5, validators=[validar_positivo])

    class Meta:
        unique_together = ('branch', 'product')

# ==========================================
# MÓDULO 3: COMPRAS
# ==========================================

class Purchase(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    invoice_number = models.CharField(max_length=50)
    date = models.DateTimeField(default=timezone.now, validators=[validar_fecha_pasada]) # No futuro
    total = models.DecimalField(max_digits=12, decimal_places=0, validators=[validar_positivo])

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)]) # Mínimo 1
    unit_cost = models.DecimalField(max_digits=10, decimal_places=0, validators=[validar_positivo])

# ==========================================
# MÓDULO 4: VENTAS
# ==========================================

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, blank=True, validators=[validar_rut_chileno])
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    
    def __str__(self):
        return self.name

class Sale(models.Model):
    PAYMENT_TYPES = (('cash', 'Efectivo'), ('debit', 'Débito'), ('credit', 'Crédito'), ('transfer', 'Transferencia'))
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=0, validators=[validar_positivo])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='cash')
    created_at = models.DateTimeField(auto_now_add=True) # Automático (no valida futuro porque es 'now')

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price_at_moment = models.DecimalField(max_digits=10, decimal_places=0, validators=[validar_positivo])
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, validators=[validar_positivo])