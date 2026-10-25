from django.urls import path, re_path

from . import views

app_name = 'trilhas'

urlpatterns = [
    path('', views.minhas_trilhas_view, name='minhas'),
    path('todas/', views.todas_trilhas_view, name='todas'),
    path('inscritas/', views.trilhas_inscritas_view, name='inscritas'),
    path('nova/', views.criar_trilha_view, name='criar'),
    path('<int:pk>/', views.detalhe_trilha_view, name='detalhe'),
    path('<int:pk>/editar/', views.editar_trilha_view, name='editar'),
    re_path(
        r'^(?P<pk>\d+)/(?P<acao>publicar|arquivar)/$',
        views.acao_trilha_view,
        name='acao',
    ),
    path('inscricoes/', views.inscricoes_view, name='inscricoes'),
    re_path(
        r'^inscricoes/(?P<pk>\d+)/(?P<acao>pausar|reativar|cancelar)/$',
        views.alterar_inscricao_view,
        name='alterar_inscricao',
    ),
]
