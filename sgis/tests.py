import re

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, path, reverse

from usuarios.models import Usuario
from usuarios.views import login_view

# Lista fechada da F0, 3.2. Acrescentar uma rota aqui é mudar a spec.
# `admin:login` é temporária: sai quando a F0 · T3 sobrepuser /admin/login/ (plano, seção 3).
ROTAS_PUBLICAS = {'login', 'saude', 'robots', 'admin:login'}


def view_sem_marcacao(request):
    return HttpResponse('dados')


@login_not_required
def view_publica(request):
    return HttpResponse('publica')


# URLconf de teste, usada com override_settings(ROOT_URLCONF=__name__).
urlpatterns = [
    path('login/', login_view, name='login'),
    path('rota-nova/', view_sem_marcacao),
    path('rota-publica/', view_publica),
]


def caminho_ficticio(padrao):
    """Troca os parâmetros de um padrão de URL por valores fictícios."""
    texto = re.sub(r'<int:\w+>', '1', str(padrao))
    texto = re.sub(r'<(\w+:)?\w+>', 'x', texto)
    texto = re.sub(r'\(\?P<\w+>[^)]*\)', 'x', texto)
    return texto.replace('^', '').replace('$', '').replace(r'\Z', '')


def percorrer_rotas(padroes, prefixo='', espaco=''):
    """Gera (nome, caminho) de todas as rotas registradas."""
    for padrao in padroes:
        caminho = prefixo + caminho_ficticio(padrao.pattern)
        if isinstance(padrao, URLResolver):
            novo_espaco = f'{espaco}{padrao.namespace}:' if padrao.namespace else espaco
            yield from percorrer_rotas(padrao.url_patterns, caminho, novo_espaco)
        elif isinstance(padrao, URLPattern):
            nome = f'{espaco}{padrao.name}' if padrao.name else None
            yield nome, '/' + caminho


class NadaSemLoginTests(TestCase):
    """ACE-00, RN-14: anônimo vai ao login, inclusive em endereço inexistente."""

    def test_a01_anonimo_vai_ao_login_e_volta_para_a_pagina(self):
        Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora', 'senha12345',
                                    papel=Usuario.Papel.IS)
        destino = reverse('trilhas:todas')

        resposta = self.client.get(destino)
        self.assertRedirects(resposta, f'/login/?next={destino}', fetch_redirect_response=False)

        resposta = self.client.post(resposta.url, {
            'email': 'is-teste@sgis.com', 'senha': 'senha12345',
        })
        self.assertRedirects(resposta, destino, fetch_redirect_response=False)

    def test_a02_anonimo_em_endereco_inexistente_vai_ao_login(self):
        resposta = self.client.get('/nao-existe/')
        self.assertRedirects(resposta, '/login/?next=/nao-existe/', fetch_redirect_response=False)


class ExcecoesPublicasTests(TestCase):
    """ACE-00a: lista fechada de exceções públicas."""

    def test_a04_excecoes_respondem_sem_login(self):
        for nome in ('login', 'saude', 'robots'):
            with self.subTest(rota=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_a04_estaticos_vem_antes_da_protecao(self):
        whitenoise = settings.MIDDLEWARE.index('whitenoise.middleware.WhiteNoiseMiddleware')
        protecao = settings.MIDDLEWARE.index('sgis.middleware.ProtecaoLoginMiddleware')
        self.assertLess(whitenoise, protecao)

    def test_a05_saude_responde_so_ok(self):
        resposta = self.client.get(reverse('saude'))
        self.assertEqual(resposta.content, b'ok')

    def test_a06_robots_pede_para_nao_indexar(self):
        resposta = self.client.get('/robots.txt')
        linhas = resposta.content.decode().split()
        self.assertEqual(linhas, ['User-agent:', '*', 'Disallow:', '/'])


class RotaNovaProtegidaTests(TestCase):
    """ACE-00b, RNF-03: rota nova nasce protegida."""

    def test_a07_toda_rota_exige_login_salvo_a_lista_de_excecoes(self):
        rotas = list(percorrer_rotas(get_resolver().url_patterns))
        self.assertGreater(len(rotas), 0)
        for nome, caminho in rotas:
            if nome in ROTAS_PUBLICAS:
                continue
            with self.subTest(rota=nome, caminho=caminho):
                resposta = self.client.get(caminho)
                self.assertEqual(resposta.status_code, 302)
                self.assertTrue(resposta.url.startswith('/login/?next='))

    @override_settings(ROOT_URLCONF=__name__)
    def test_a07_rota_nova_sem_marcacao_e_protegida(self):
        resposta = self.client.get('/rota-nova/')
        self.assertRedirects(resposta, '/login/?next=/rota-nova/', fetch_redirect_response=False)

        self.assertEqual(self.client.get('/rota-publica/').status_code, 200)
