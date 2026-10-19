from django.contrib import admin

from .models import Trilha


@admin.register(Trilha)
class TrilhaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'usuario_criador')
    list_filter = ('tipo',)
    search_fields = ('titulo',)
