from django import forms
from django.contrib.auth import get_user_model
from .models import Company, Branch, Supplier, Product, Plan

User = get_user_model()

# --- REGISTRO ---
class RegistroClienteForm(forms.ModelForm):
    company_name = forms.CharField(label="Nombre Empresa", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    company_rut = forms.CharField(label="RUT Empresa", max_length=12, widget=forms.TextInput(attrs={'class': 'form-control'}))
    company_address = forms.CharField(label="Dirección", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email Admin", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Nombre", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellido", widget=forms.TextInput(attrs={'class': 'form-control'}))
    rut = forms.CharField(label="RUT Admin", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'rut']

    def save(self, commit=True):
        company = Company.objects.create(name=self.cleaned_data['company_name'], rut=self.cleaned_data['company_rut'], address=self.cleaned_data.get('company_address', ''))
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.company = company
        user.role = 'admin_cliente'
        user.username = user.email
        if commit: user.save()
        return user

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'rut', 'address', 'phone', 'is_active']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'}), 'rut': forms.TextInput(attrs={'class': 'form-control'}), 'address': forms.TextInput(attrs={'class': 'form-control'}), 'phone': forms.TextInput(attrs={'class': 'form-control'}), 'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})}

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'price', 'max_branches', 'max_users']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'}), 'price': forms.NumberInput(attrs={'class': 'form-control'}), 'max_branches': forms.NumberInput(attrs={'class': 'form-control'}), 'max_users': forms.NumberInput(attrs={'class': 'form-control'})}

class SuperUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, label="Contraseña")
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'rut', 'role', 'company', 'is_active', 'password']
        widgets = {'email': forms.EmailInput(attrs={'class': 'form-control'}), 'first_name': forms.TextInput(attrs={'class': 'form-control'}), 'last_name': forms.TextInput(attrs={'class': 'form-control'}), 'rut': forms.TextInput(attrs={'class': 'form-control'}), 'role': forms.Select(attrs={'class': 'form-select'}), 'company': forms.Select(attrs={'class': 'form-select'}), 'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})}
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'): user.set_password(self.cleaned_data['password'])
        user.username = user.email
        if commit: user.save()
        return user

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'address', 'phone']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'}), 'address': forms.TextInput(attrs={'class': 'form-control'}), 'phone': forms.TextInput(attrs={'class': 'form-control'})}

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'rut', 'contact_name', 'phone', 'email']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'}), 'rut': forms.TextInput(attrs={'class': 'form-control'}), 'contact_name': forms.TextInput(attrs={'class': 'form-control'}), 'phone': forms.TextInput(attrs={'class': 'form-control'}), 'email': forms.EmailInput(attrs={'class': 'form-control'})}

# --- PRODUCT FORM CORREGIDO ---
class ProductForm(forms.ModelForm):
    # Campo manual para capturar stock inicial al crear
    initial_stock = forms.IntegerField(
        label="Stock Inicial", 
        min_value=0, 
        initial=0, 
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Product
        # Quitamos 'category' de la lista
        fields = ['sku', 'name', 'description', 'price', 'cost']
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TeamMemberForm(forms.ModelForm):
    ROLE_CHOICES = (('gerente', 'Gerente'), ('vendedor', 'Vendedor'))
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol", widget=forms.Select(attrs={'class': 'form-select'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, label="Contraseña")
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'rut', 'role', 'password']
        widgets = {'email': forms.EmailInput(attrs={'class': 'form-control'}), 'first_name': forms.TextInput(attrs={'class': 'form-control'}), 'last_name': forms.TextInput(attrs={'class': 'form-control'}), 'rut': forms.TextInput(attrs={'class': 'form-control'})}
    def save(self, commit=True, company=None):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'): user.set_password(self.cleaned_data['password'])
        if company: user.company = company
        user.username = user.email
        if commit: user.save()
        return user