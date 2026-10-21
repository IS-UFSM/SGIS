from django.contrib import admin

from .models import Empreendimento


@admin.register(Empreendimento)
class EmpreendimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'representante',
                    'usuario_professor_supervisor', 'ativo')
    list_filter = ('tipo',)
    search_fields = ('nome',)

    @admin.display(boolean=True, description='Ativo')
    def ativo(self, obj):
        return obj.ativo
