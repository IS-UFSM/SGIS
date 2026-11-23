import copy

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm, AdminUserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from empreendimentos.forms import EmpreendimentoCadastroForm

from . import regras
from .models import Usuario

# RN-16: o /admin/ só gerencia contas e papéis (F0, 3.3.1).
admin.site.unregister(Group)


class UsuarioAdminCreationForm(AdminUserCreationForm):
    """ACE-04/ACE-05: campos do empreendimento na criação pelo admin."""

    class Meta(AdminUserCreationForm.Meta):
        model = Usuario
        fields = ('email', 'nome', 'papel')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # O admin não precisa oferecer a opção de criar uma conta sem senha.
        # `AdminUserCreationForm` adiciona este campo por padrão no Django 6.1;
        # removê-lo impede que um POST forjado contorne a troca obrigatória.
        self.fields.pop('usable_password', None)

        for nome, campo in EmpreendimentoCadastroForm.base_fields.items():
            campo_admin = copy.deepcopy(campo)
            campo_admin.required = (
                self.data.get('papel') == Usuario.Papel.EMPREENDEDOR
                and campo.required
            )
            self.fields[f'empreendimento-{nome}'] = campo_admin

        self.order_fields([
            'email', 'nome', 'papel',
            'empreendimento-nome', 'empreendimento-tipo', 'empreendimento-descricao',
            'password1', 'password2',
        ])


class UsuarioAdminPasswordChangeForm(AdminPasswordChangeForm):
    """ACE-08: redefinição pelo admin também exige troca no próximo acesso."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A redefinição sempre define uma senha utilizável; não há caminho para
        # desabilitar a autenticação por senha pelo /admin/.
        self.fields.pop('usable_password', None)

    def save(self, commit=True):
        conta = super().save(commit=commit)
        conta.deve_trocar_senha = True
        if commit:
            conta.save(update_fields=['deve_trocar_senha'])
        return conta


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    add_form = UsuarioAdminCreationForm
    change_password_form = UsuarioAdminPasswordChangeForm

    list_display = ('email', 'nome', 'papel', 'is_active')
    list_filter = ('papel', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    actions = ('desativar_selecionadas', 'reativar_selecionadas')

    # Campos exibidos ao editar um usuário existente
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dados pessoais', {'fields': ('nome', 'papel')}),
        ('Permissões', {'fields': ('is_active',)}),
    )

    # Campos exibidos ao criar um novo usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'nome', 'papel',
                'empreendimento-nome', 'empreendimento-tipo', 'empreendimento-descricao',
                'password1', 'password2',
            ),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Preserva os campos extras ao montar o ModelForm do admin."""
        if obj is None:
            kwargs.setdefault('form', self.add_form)
            # `modelform_factory` só aceita campos do model neste argumento;
            # os campos do empreendimento já são declarados no formulário.
            kwargs['fields'] = ('email', 'nome', 'papel')
        return super().get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        """ACE-09/ACE-11: papel e situação não mudam depois da criação."""
        if obj is None:
            return ()
        return ('papel', 'is_active')

    def has_delete_permission(self, request, obj=None):
        """ACE-09: contas nunca são apagadas."""
        return False

    def save_model(self, request, obj, form, change):
        """ACE-04/ACE-05: mantém acesso e empreendimento coerentes com o papel."""
        obj.is_staff = obj.papel == Usuario.Papel.ADMIN
        obj.is_superuser = obj.papel == Usuario.Papel.ADMIN
        if not change:
            obj.deve_trocar_senha = True

        super().save_model(request, obj, form, change)

        if not change and obj.papel == Usuario.Papel.EMPREENDEDOR:
            dados_empreendimento = {
                nome: form.cleaned_data[f'empreendimento-{nome}']
                for nome in EmpreendimentoCadastroForm.base_fields
            }
            regras.vincular_empreendimento(obj, dados_empreendimento)

    @admin.action(description='Desativar contas selecionadas')
    def desativar_selecionadas(self, request, queryset):
        self._alterar_selecionadas(request, queryset, regras.desativar, 'desativada')

    @admin.action(description='Reativar contas selecionadas')
    def reativar_selecionadas(self, request, queryset):
        self._alterar_selecionadas(request, queryset, regras.reativar, 'reativada')

    def _alterar_selecionadas(self, request, queryset, regra, estado):
        """Aplica uma transição por conta, sem deixar uma falha abortar as demais."""
        for conta in queryset:
            try:
                regra(conta, request.user)
            except (PermissionDenied, regras.RegraViolada) as erro:
                self.message_user(request, str(erro), messages.ERROR)
            else:
                self.message_user(
                    request,
                    f'Conta de "{conta.nome}" {estado} com sucesso.',
                    messages.SUCCESS,
                )
