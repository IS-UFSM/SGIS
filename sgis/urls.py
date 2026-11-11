from django.contrib import admin
from django.urls import include, path

from usuarios import views

from .views import admin_login_view, robots_view, saude_view

urlpatterns = [
    path('admin/login/', admin_login_view, name='admin_login'),  # antes do admin (decisão 7.1)
    path('admin/', admin.site.urls),
    path('saude/', saude_view, name='saude'),
    path('robots.txt', robots_view, name='robots'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/novo/', views.criar_usuario_view, name='criar_usuario'),
    path('conta/senha/', views.trocar_senha_view, name='trocar_senha'),
    path('trilhas/', include('trilhas.urls')),
    path('', views.home_view, name='home'),
]
