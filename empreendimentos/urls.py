from django.urls import path, re_path

from . import views

app_name = 'empreendimentos'

urlpatterns = [
    path('', views.lista_view, name='lista'),
    path('<int:pk>/', views.perfil_view, name='perfil'),
    path('<int:pk>/editar/', views.editar_view, name='editar'),
    re_path(
        r'^(?P<pk>\d+)/(?P<acao>desativar|reativar)/$',
        views.situacao_view,
        name='situacao',
    ),
    path('<int:pk>/contatos/novo/', views.contato_novo_view, name='contato_novo'),
    path('<int:pk>/contatos/<int:contato>/editar/', views.contato_editar_view, name='contato_editar'),
    path('<int:pk>/contatos/<int:contato>/responsavel/', views.contato_responsavel_view,
         name='contato_responsavel'),
    path('<int:pk>/contatos/<int:contato>/remover/', views.contato_remover_view,
         name='contato_remover'),
]
