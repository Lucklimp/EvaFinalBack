from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F
from django.db import transaction, IntegrityError
from django.http import JsonResponse
import json

# IMPORTANTE: Agregamos Purchase al import
from .models import Branch, Supplier, Product, User, Sale, SaleItem, Plan, Subscription, Company, Inventory, Purchase
from .forms import (BranchForm, SupplierForm, ProductForm, TeamMemberForm, 
                    RegistroClienteForm, PlanForm, CompanyForm, SuperUserForm)

PLAN_DEFAULTS = {'Básico': {'products': 500, 'suppliers': 5}, 'Estándar': {'products': 1000, 'suppliers': 20}, 'Premium': {'products': 999999, 'suppliers': 999}}

def get_usage_info(user, metric_key, model_class):
    if user.role == 'super_admin': return {'current': 0, 'limit': 999, 'percent': 0, 'is_unlimited': True, 'plan_name': 'SuperAdmin'}
    company = user.company
    plan = company.subscription.plan if hasattr(company, 'subscription') and company.subscription.is_active else None
    plan_name = plan.name if plan else 'Sin Plan'
    limit = 0
    if metric_key == 'branches': limit = plan.max_branches if plan else 0
    elif metric_key == 'users': limit = plan.max_users if plan else 0
    else: limit = PLAN_DEFAULTS.get(plan_name, {'products': 0, 'suppliers': 0}).get(metric_key, 0)
    current = User.objects.filter(company=company).count() if metric_key == 'users' else model_class.objects.filter(company=company).count()
    is_unlimited = limit >= 999
    percent = 0 if (is_unlimited or limit == 0) else (current / limit) * 100
    return {'current': current, 'limit': limit, 'percent': min(percent, 100), 'is_unlimited': is_unlimited, 'plan_name': plan_name}

def check_limit_block(request, metric_key, model_class):
    usage = get_usage_info(request.user, metric_key, model_class)
    if not usage['is_unlimited'] and usage['current'] >= usage['limit']:
        messages.error(request, f"⚠️ Límite del plan {usage['plan_name']} alcanzado ({usage['current']}/{usage['limit']}).")
        return False
    return True

# --- GENERAL ---
def home_redirect(request): return redirect('dashboard') if request.user.is_authenticated else redirect('login')
@login_required
def dashboard_view(request): return render(request, 'dashboard.html')
def register_view(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid(): form.save(); messages.success(request, f'Cuenta creada. Inicia sesión.'); return redirect('login')
    else: form = RegistroClienteForm()
    return render(request, 'registration/register.html', {'form': form})

# --- SUPER ADMIN ---
@login_required
def super_dashboard_companies(request):
    if request.user.role != 'super_admin': return redirect('dashboard')
    return render(request, 'superadmin/company_list.html', {'companies': Company.objects.all().order_by('-created_at')})
@login_required
def super_company_create(request):
    if request.user.role != 'super_admin': return redirect('dashboard')
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid(): form.save(); messages.success(request, 'Empresa creada.'); return redirect('super_companies')
    else: form = RegistroClienteForm()
    return render(request, 'superadmin/company_form.html', {'form': form, 'title': 'Nueva Empresa'})
@login_required
def super_company_edit(request, pk):
    c = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=c)
        if form.is_valid(): form.save(); messages.success(request, 'Actualizada.'); return redirect('super_companies')
    else: form = CompanyForm(instance=c)
    return render(request, 'superadmin/company_form.html', {'form': form, 'title': 'Editar'})
@login_required
def super_company_delete(request, pk):
    c = get_object_or_404(Company, pk=pk)
    if request.method == 'POST': c.delete(); messages.success(request, 'Eliminada.'); return redirect('super_companies')
    return render(request, 'generic_delete.html', {'object': c, 'cancel_url': 'super_companies'})

@login_required
def super_user_list(request):
    if request.user.role != 'super_admin': return redirect('dashboard')
    return render(request, 'superadmin/user_list.html', {'users': User.objects.all().select_related('company').order_by('-date_joined')})
@login_required
def super_user_create(request):
    if request.method == 'POST':
        form = SuperUserForm(request.POST)
        if form.is_valid(): form.save(); messages.success(request, 'Usuario creado.'); return redirect('super_user_list')
    else: form = SuperUserForm()
    return render(request, 'superadmin/user_form.html', {'form': form, 'title': 'Nuevo Usuario'})
@login_required
def super_user_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = SuperUserForm(request.POST, instance=u)
        if form.is_valid(): form.save(); messages.success(request, 'Actualizado.'); return redirect('super_user_list')
    else: form = SuperUserForm(instance=u)
    return render(request, 'superadmin/user_form.html', {'form': form, 'title': 'Editar Usuario'})
@login_required
def super_user_delete(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u.id == request.user.id: messages.error(request, 'No puedes borrarte.'); return redirect('super_user_list')
    if request.method == 'POST': u.delete(); messages.success(request, 'Eliminado.'); return redirect('super_user_list')
    return render(request, 'generic_delete.html', {'object': u, 'cancel_url': 'super_user_list'})

@login_required
def super_dashboard_plans(request):
    if request.user.role != 'super_admin': return redirect('dashboard')
    return render(request, 'superadmin/plan_list.html', {'plans': Plan.objects.all().order_by('price')})
@login_required
def super_plan_create(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid(): form.save(); return redirect('super_plans')
    else: form = PlanForm()
    return render(request, 'superadmin/plan_form.html', {'form': form, 'title': 'Nuevo Plan'})
@login_required
def super_plan_edit(request, pk):
    p = get_object_or_404(Plan, pk=pk)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=p)
        if form.is_valid(): form.save(); return redirect('super_plans')
    else: form = PlanForm(instance=p)
    return render(request, 'superadmin/plan_form.html', {'form': form, 'title': 'Editar Plan'})

# --- PRODUCTOS ---
@login_required
def product_list(request):
    usage = get_usage_info(request.user, 'products', Product)
    return render(request, 'products/list.html', {'products': Product.objects.filter(company=request.user.company), 'usage': usage})

@login_required
def product_create(request):
    if not check_limit_block(request, 'products', Product): return redirect('product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid(): 
            try:
                p = form.save(commit=False)
                p.company = request.user.company
                p.save()
                stock_val = form.cleaned_data.get('initial_stock', 0)
                first_branch = Branch.objects.filter(company=request.user.company).first()
                if first_branch: Inventory.objects.create(branch=first_branch, product=p, stock=stock_val)
                else: messages.warning(request, "Producto creado sin inventario (Falta sucursal).")
                messages.success(request, 'Producto creado exitosamente.')
                return redirect('product_list')
            except IntegrityError:
                messages.error(request, f'Error: El SKU "{form.cleaned_data.get("sku")}" ya existe.')
    else: form = ProductForm()
    return render(request, 'products/form.html', {'form': form, 'title': 'Nuevo'})

@login_required
def product_edit(request, pk):
    p = get_object_or_404(Product, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=p)
        if form.is_valid(): 
            try: form.save(); messages.success(request, 'Actualizado.'); return redirect('product_list')
            except IntegrityError: messages.error(request, 'Error: SKU duplicado.')
    else: form = ProductForm(instance=p)
    return render(request, 'products/form.html', {'form': form, 'title': 'Editar'})

@login_required
def product_delete(request, pk):
    p = get_object_or_404(Product, pk=pk, company=request.user.company)
    if request.method == 'POST': p.delete(); return redirect('product_list')
    return render(request, 'generic_delete.html', {'object': p, 'cancel_url': 'product_list'})

@login_required
def product_adjust_stock(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 0))
            op = request.POST.get('operation', 'add')
            branch = Branch.objects.filter(company=request.user.company).first()
            if branch:
                inv, _ = Inventory.objects.get_or_create(branch=branch, product=product)
                if op == 'add': inv.stock += qty
                elif op == 'subtract' and inv.stock >= qty: inv.stock -= qty
                inv.save()
                messages.success(request, 'Stock actualizado.')
        except: pass
    return redirect('product_list')

# --- MANTENEDORES ---
@login_required
def team_list(request):
    usage = get_usage_info(request.user, 'users', User)
    return render(request, 'team/list.html', {'members': User.objects.filter(company=request.user.company).exclude(id=request.user.id), 'usage': usage})
@login_required
def team_create(request):
    if not check_limit_block(request, 'users', User): return redirect('team_list')
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid(): form.save(company=request.user.company); messages.success(request, 'Creado.'); return redirect('team_list')
    else: form = TeamMemberForm()
    return render(request, 'team/form.html', {'form': form, 'title': 'Nuevo'})
@login_required
def team_edit(request, pk):
    m = get_object_or_404(User, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=m)
        if form.is_valid(): form.save(commit=False).save(); return redirect('team_list')
    else: form = TeamMemberForm(instance=m)
    return render(request, 'team/form.html', {'form': form, 'title': 'Editar'})
@login_required
def team_delete(request, pk):
    m = get_object_or_404(User, pk=pk, company=request.user.company)
    if request.method == 'POST': m.delete(); return redirect('team_list')
    return render(request, 'generic_delete.html', {'object': m, 'cancel_url': 'team_list'})

@login_required
def branch_list(request):
    usage = get_usage_info(request.user, 'branches', Branch)
    return render(request, 'branches/list.html', {'branches': Branch.objects.filter(company=request.user.company), 'usage': usage})
@login_required
def branch_create(request):
    if not check_limit_block(request, 'branches', Branch): return redirect('branch_list')
    if request.method == 'POST':
        f = BranchForm(request.POST)
        if f.is_valid(): b=f.save(commit=False); b.company=request.user.company; b.save(); return redirect('branch_list')
    else: f = BranchForm()
    return render(request, 'branches/form.html', {'form': f, 'title': 'Nueva'})
@login_required
def branch_edit(request, pk):
    b = get_object_or_404(Branch, pk=pk, company=request.user.company)
    if request.method == 'POST':
        f = BranchForm(request.POST, instance=b)
        if f.is_valid(): f.save(); return redirect('branch_list')
    else: f = BranchForm(instance=b)
    return render(request, 'branches/form.html', {'form': f, 'title': 'Editar'})
@login_required
def branch_delete(request, pk):
    b = get_object_or_404(Branch, pk=pk, company=request.user.company)
    if request.method == 'POST': b.delete(); return redirect('branch_list')
    return render(request, 'generic_delete.html', {'object': b, 'cancel_url': 'branch_list'})

@login_required
def supplier_list(request):
    usage = get_usage_info(request.user, 'suppliers', Supplier)
    return render(request, 'suppliers/list.html', {'suppliers': Supplier.objects.filter(company=request.user.company), 'usage': usage})
@login_required
def supplier_create(request):
    if not check_limit_block(request, 'suppliers', Supplier): return redirect('supplier_list')
    if request.method == 'POST':
        f = SupplierForm(request.POST)
        if f.is_valid(): s=f.save(commit=False); s.company=request.user.company; s.save(); return redirect('supplier_list')
    else: f = SupplierForm()
    return render(request, 'suppliers/form.html', {'form': f, 'title': 'Nuevo'})
@login_required
def supplier_edit(request, pk):
    s = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    if request.method == 'POST':
        f = SupplierForm(request.POST, instance=s)
        if f.is_valid(): f.save(); return redirect('supplier_list')
    else: f = SupplierForm(instance=s)
    return render(request, 'suppliers/form.html', {'form': f, 'title': 'Editar'})
@login_required
def supplier_delete(request, pk):
    s = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    if request.method == 'POST': s.delete(); return redirect('supplier_list')
    return render(request, 'generic_delete.html', {'object': s, 'cancel_url': 'supplier_list'})

# --- VENTAS Y REPORTES ---
@login_required
def pos_view(request):
    return render(request, 'sales/pos.html', {'products': Product.objects.filter(company=request.user.company)})
@login_required
def pos_submit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            if not items: return JsonResponse({'error': 'Carrito vacío'}, status=400)
            with transaction.atomic():
                sale = Sale.objects.create(company=request.user.company, seller=request.user, total=0)
                total = 0
                for i in items:
                    p = Product.objects.get(id=i['id'], company=request.user.company)
                    qty = int(i['qty'])
                    inv = Inventory.objects.filter(product=p, stock__gte=qty).first()
                    if not inv: raise ValueError(f"Sin stock para {p.name}")
                    inv.stock -= qty
                    inv.save()
                    subtotal = p.price * qty
                    total += subtotal
                    SaleItem.objects.create(sale=sale, product=p, quantity=qty, price_at_moment=p.price, subtotal=subtotal)
                sale.total = total
                sale.save()
            return JsonResponse({'success': True})
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Error'}, status=405)
@login_required
def sale_list(request):
    return render(request, 'sales/list.html', {'sales': Sale.objects.filter(company=request.user.company).order_by('-created_at')})

@login_required
def reports_view(request):
    """Genera reportes detallados de gestión"""
    c = request.user.company
    now = timezone.now()
    plan_name = c.subscription.plan.name if hasattr(c, 'subscription') else 'Básico'
    can_see_details = plan_name in ['Estándar', 'Premium']

    # KPIs Generales
    total_sales = Sale.objects.filter(company=c).count()
    total_money = Sale.objects.filter(company=c).aggregate(Sum('total'))['total__sum'] or 0
    total_products = Product.objects.filter(company=c).count()
    
    # Inventario Global
    total_stock = Inventory.objects.filter(branch__company=c).aggregate(Sum('stock'))['stock__sum'] or 0
    inventory_value = Inventory.objects.filter(branch__company=c).annotate(val=F('stock') * F('product__cost')).aggregate(Sum('val'))['val__sum'] or 0
    low_stock_count = Inventory.objects.filter(branch__company=c, stock__lte=F('min_stock')).count()

    # Ventas por periodo (Global)
    sales_today = Sale.objects.filter(company=c, created_at__date=now.date()).aggregate(Sum('total'))['total__sum'] or 0
    sales_month = Sale.objects.filter(company=c, created_at__month=now.month, created_at__year=now.year).aggregate(Sum('total'))['total__sum'] or 0

    # 1. Reporte Stock y Ventas por Sucursal
    stock_by_branch = []
    if can_see_details:
        branches = Branch.objects.filter(company=c)
        for b in branches:
            b_stock = Inventory.objects.filter(branch=b).aggregate(Sum('stock'))['stock__sum'] or 0
            b_sales_today = Sale.objects.filter(branch=b, created_at__date=now.date()).aggregate(Sum('total'))['total__sum'] or 0
            b_sales_month = Sale.objects.filter(branch=b, created_at__month=now.month).aggregate(Sum('total'))['total__sum'] or 0
            stock_by_branch.append({
                'name': b.name,
                'stock': b_stock,
                'sales_today': b_sales_today,
                'sales_month': b_sales_month
            })

    # 2. Reporte de Proveedores
    suppliers_report = []
    for s in Supplier.objects.filter(company=c):
        # Última compra
        last_p = Purchase.objects.filter(supplier=s).order_by('-date').first()
        purchases_count = Purchase.objects.filter(supplier=s).count()
        suppliers_report.append({
            'name': s.name,
            'contact': s.contact_name,
            'rut': s.rut,
            'purchases_count': purchases_count,
            'last_purchase': last_p.date if last_p else None
        })

    return render(request, 'reports/index.html', {
        'total_sales': total_sales,
        'total_money': total_money,
        'total_products': total_products,
        'total_stock': total_stock,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'sales_today': sales_today,
        'sales_month': sales_month,
        'plan_name': plan_name,
        'can_see_details': can_see_details,
        'stock_by_branch': stock_by_branch,
        'suppliers_report': suppliers_report
    })

@login_required
def subscription_detail(request):
    return render(request, 'subscription/detail.html', {'subscription': getattr(request.user.company, 'subscription', None), 'plans': Plan.objects.all().order_by('price')})
@login_required
def subscribe_plan(request, plan_id):
    if request.method == 'POST':
        p = get_object_or_404(Plan, id=plan_id)
        Subscription.objects.update_or_create(company=request.user.company, defaults={'plan': p, 'start_date': timezone.now(), 'end_date': timezone.now() + timezone.timedelta(days=30), 'is_active': True})
        messages.success(request, f'Plan {p.name} activado.')
    return redirect('subscription')
@login_required
def api_docs_view(request):
    base_url = request.build_absolute_uri('/')[:-1]
    docs = [
        {"category": "1. Autenticación", "endpoints": [{"title": "Token", "method": "POST", "url": "/api/token/", "desc": "Login", "body": json.dumps({"email":"admin@test.com","password":"123"}, indent=2)}]},
        {"category": "2. Productos", "endpoints": [{"title": "Listar", "method": "GET", "url": "/api/products/", "desc": "Ver productos", "body": None}]},
    ]
    return render(request, 'docs/api_reference.html', {'docs': docs, 'base_url': base_url})