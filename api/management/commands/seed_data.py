from django.core.management.base import BaseCommand
from api.models import User, Company, Plan, Branch, Product, Inventory, Supplier
from django.utils import timezone

class Command(BaseCommand):
    help = 'Poblar base de datos con datos de prueba iniciales'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando carga de datos...')

        # 1. Crear Planes
        plan_basic, _ = Plan.objects.get_or_create(name='Básico', defaults={'price': 0, 'max_branches': 1, 'max_users': 2})
        plan_std, _ = Plan.objects.get_or_create(name='Estándar', defaults={'price': 25000, 'max_branches': 3, 'max_users': 5})
        plan_pro, _ = Plan.objects.get_or_create(name='Premium', defaults={'price': 60000, 'max_branches': 999, 'max_users': 999})
        self.stdout.write(self.style.SUCCESS('✔ Planes creados'))

        # 2. Crear Super Admin
        if not User.objects.filter(email='admin@temucosoft.com').exists():
            User.objects.create_superuser('admin@temucosoft.com', 'admin123', first_name='Super', last_name='Admin')
            self.stdout.write(self.style.SUCCESS('✔ SuperAdmin creado (admin@temucosoft.com / admin123)'))

        # 3. Crear Cliente de Prueba (Dueño de Farmacia)
        if not User.objects.filter(email='cliente@farmacia.com').exists():
            company = Company.objects.create(name='Farmacia Los Pinos', rut='76123456-7', address='Av. Alemania 123')
            
            # Suscribir al plan Estándar
            from api.models import Subscription
            Subscription.objects.create(company=company, plan=plan_std, start_date=timezone.now(), end_date=timezone.now() + timezone.timedelta(days=30))

            user = User.objects.create_user('cliente@farmacia.com', 'cliente123', role='admin_cliente', company=company, first_name='Juan', last_name='Pérez', rut='12345678-9')
            
            # Crear Sucursal y Proveedor
            branch = Branch.objects.create(company=company, name='Sucursal Centro', address='Calle Bulnes 555', phone='+56911111111')
            Supplier.objects.create(company=company, name='Laboratorio Chile', rut='99555444-3', contact_name='Pedro', phone='222333444', email='contacto@lab.cl')

            # Crear Productos y Stock
            p1 = Product.objects.create(company=company, sku='PAR-500', name='Paracetamol 500mg', description='Caja 16 comp.', price=1500, cost=800)
            p2 = Product.objects.create(company=company, sku='IBU-400', name='Ibuprofeno 400mg', description='Caja 20 comp.', price=2500, cost=1200)
            
            Inventory.objects.create(branch=branch, product=p1, stock=100, min_stock=10)
            Inventory.objects.create(branch=branch, product=p2, stock=50, min_stock=5)

            self.stdout.write(self.style.SUCCESS('✔ Cliente de prueba creado (cliente@farmacia.com / cliente123)'))

        self.stdout.write(self.style.SUCCESS('★ ¡Datos cargados exitosamente! Listo para probar.'))