from django.urls import path

from . import views

app_name = 'empreendimentos'

urlpatterns = [
    path('', views.lista_view, name='lista'),
    path('<int:pk>/', views.perfil_view, name='perfil'),
    path('<int:pk>/editar/', views.editar_view, name='editar'),
]
