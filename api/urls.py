from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import views as auth_views
from . import views

router = DefaultRouter()

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('docs/', views.api_docs_view, name='api_docs'),
    path('docs/curl/', views.api_docs_view, name='api_docs_curl'),

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register_view, name='register'),

    path('super/companies/', views.super_dashboard_companies, name='super_companies'),
    path('super/companies/add/', views.super_company_create, name='super_company_create'),
    path('super/companies/edit/<int:pk>/', views.super_company_edit, name='super_company_edit'),
    path('super/companies/delete/<int:pk>/', views.super_company_delete, name='super_company_delete'),
    path('super/users/', views.super_user_list, name='super_user_list'),
    path('super/users/add/', views.super_user_create, name='super_user_create'),
    path('super/users/edit/<int:pk>/', views.super_user_edit, name='super_user_edit'),
    path('super/users/delete/<int:pk>/', views.super_user_delete, name='super_user_delete'),
    path('super/plans/', views.super_dashboard_plans, name='super_plans'),
    path('super/plans/add/', views.super_plan_create, name='super_plan_create'),
    path('super/plans/edit/<int:pk>/', views.super_plan_edit, name='super_plan_edit'),

    path('team/', views.team_list, name='team_list'),
    path('team/add/', views.team_create, name='team_create'),
    path('team/edit/<int:pk>/', views.team_edit, name='team_edit'),
    path('team/delete/<int:pk>/', views.team_delete, name='team_delete'),

    path('branches/', views.branch_list, name='branch_list'),
    path('branches/add/', views.branch_create, name='branch_create'),
    path('branches/edit/<int:pk>/', views.branch_edit, name='branch_edit'),
    path('branches/delete/<int:pk>/', views.branch_delete, name='branch_delete'),

    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),

    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    # NUEVA RUTA PARA AJUSTE DE STOCK
    path('products/adjust_stock/<int:pk>/', views.product_adjust_stock, name='product_adjust_stock'),

    path('pos/', views.pos_view, name='pos'),
    path('pos/submit/', views.pos_submit, name='pos_submit'),
    path('sales/', views.sale_list, name='sale_list'),
    path('reports/', views.reports_view, name='reports'),
    path('subscription/', views.subscription_detail, name='subscription'),
    path('subscription/change/<int:plan_id>/', views.subscribe_plan, name='subscribe_plan'),

    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
]