from django.contrib import admin

from .models import Inscricao, Trilha


@admin.register(Trilha)
class TrilhaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'usuario_criador', 'pre_incubacao')
    list_filter = ('tipo', 'pre_incubacao')
    search_fields = ('titulo',)


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('empreendimento', 'trilha', 'status', 'inscrito_por', 'inscrito_em')
    list_filter = ('status',)
    search_fields = ('empreendimento__nome', 'trilha__titulo')
