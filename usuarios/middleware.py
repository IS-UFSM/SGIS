from django.shortcuts import redirect


class TrocaSenhaObrigatoriaMiddleware:
    """ACE-06: enquanto a conta estiver marcada, só a troca e o Sair funcionam."""

    ROTAS_PERMITIDAS = {'trocar_senha', 'logout'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        rota = getattr(request.resolver_match, 'url_name', None)
        if (
            request.user.is_authenticated
            and request.user.deve_trocar_senha
            and rota not in self.ROTAS_PERMITIDAS
        ):
            return redirect('trocar_senha')
        return None
