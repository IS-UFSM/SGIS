from django.contrib import admin

from .models import Inscricao, Trilha


@admin.register(Trilha)
class TrilhaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'etapa', 'status', 'usuario_criador')
    list_filter = ('etapa', 'status')
    search_fields = ('titulo',)


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('empreendimento', 'trilha', 'status', 'inscrito_por', 'inscrito_em')
    list_filter = ('status',)
    search_fields = ('empreendimento__nome', 'trilha__titulo')
