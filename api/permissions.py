from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'super_admin'

class IsAdminCliente(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin_cliente'

class IsGerente(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin_cliente', 'gerente']

class IsVendedor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin_cliente', 'gerente', 'vendedor']

class CheckPlanLimits(permissions.BasePermission):
    """
    Ejemplo de validación de Plan:
    Si intenta crear una Sucursal (Branch), verificar si su plan lo permite.
    """
    message = "Su plan actual no permite realizar esta acción."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Solo aplicamos lógica si es AdminCliente intentando crear algo
        if view.basename == 'branches' and request.method == 'POST':
            company = request.user.company
            if not hasattr(company, 'subscription') or not company.subscription.active:
                return False
            
            plan = company.subscription.plan_name
            current_branches = company.branch_set.count()
            
            limits = {'basico': 1, 'estandar': 3, 'premium': 999}
            
            if current_branches >= limits.get(plan, 0):
                return False
                
        return True
