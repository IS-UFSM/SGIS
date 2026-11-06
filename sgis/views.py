from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse


@login_not_required
def saude_view(request):
    """Verificação de saúde do Render: responde só `ok` (ACE-00a)."""
    return HttpResponse('ok', content_type='text/plain')


@login_not_required
def robots_view(request):
    """Pede a todos os buscadores que não indexem o site (ACE-00a)."""
    return HttpResponse('User-agent: *\nDisallow: /\n', content_type='text/plain')
