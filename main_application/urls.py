
from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/treasurer/', views.treasurer_dashboard, name='treasurer_dashboard'),
    path('dashboard/secretary/', views.secretary_dashboard, name='secretary_dashboard'),
    path('dashboard/member/', views.member_dashboard, name='member_dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
]