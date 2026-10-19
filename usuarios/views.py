from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm


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
