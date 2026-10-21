from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import papel_requerido
from .forms import LoginForm, UsuarioCadastroForm
from .models import Usuario


def login_view(request):
    """Tela de login. Redireciona se já autenticado."""
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(data=request.POST or None, request=request)

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        proximo = request.GET.get('next', 'home')
        return redirect(proximo)

    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    """Encerra a sessão e volta ao login."""
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    """Página inicial após o login."""
    return render(request, 'usuarios/home.html')


@papel_requerido(Usuario.Papel.IS)
def criar_usuario_view(request):
    """IS cria um usuário novo (professor ou empreendimento)."""
    form = UsuarioCadastroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(request, f'Usuário "{usuario.nome}" criado com sucesso.')
        return redirect('criar_usuario')

    return render(request, 'usuarios/criar_usuario.html', {'form': form})
