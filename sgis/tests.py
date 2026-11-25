import re

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import URLPattern, URLResolver, get_resolver, path, reverse
from django.utils.http import urlencode

from sgis.texto import TextoFormatadoField, limpar_html
from usuarios.models import Usuario
from usuarios.views import login_view

# Lista fechada da F0, 3.2. Acrescentar uma rota aqui é mudar a spec.
ROTAS_PUBLICAS = {'login', 'saude', 'robots'}


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


class LoginSeguroTests(TestCase):
    """RNF-01: depois do login, só volta a endereços do próprio SGIS."""

    def setUp(self):
        Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora', 'senha12345',
                                    papel=Usuario.Papel.IS)

    def entrar(self, proximo):
        return self.client.post(f"{reverse('login')}?{urlencode({'next': proximo})}", {
            'email': 'is-teste@sgis.com', 'senha': 'senha12345',
        })

    def test_a10_next_externo_vai_para_a_pagina_inicial(self):
        enderecos = [
            'https://site-externo.com/',
            '//site-externo.com/',
            'javascript:alert(1)',
        ]
        for proximo in enderecos:
            with self.subTest(next=proximo):
                resposta = self.entrar(proximo)
                self.client.logout()
                self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)

    def test_a11_next_interno_e_respeitado(self):
        destino = reverse('trilhas:todas')
        resposta = self.entrar(destino)
        self.assertRedirects(resposta, destino, fetch_redirect_response=False)


# As telas do /admin/ usam {% static %}, e o manifesto do WhiteNoise só existe depois do collectstatic.
@override_settings(STORAGES={
    **settings.STORAGES,
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class AdminSoContasTests(TestCase):
    """RN-16: o /admin/ só gerencia contas, e sua entrada é o login do sistema."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser('admin@sgis.com', 'Admin', 'senha12345')

    def test_a08_admin_so_gerencia_contas(self):
        self.client.force_login(self.admin)

        resposta = self.client.get(reverse('admin:index'))
        modelos = {modelo['object_name']
                   for app in resposta.context['app_list'] for modelo in app['models']}
        self.assertEqual(modelos, {'Usuario'})
        self.assertEqual(self.client.get('/admin/usuarios/usuario/').status_code, 200)

        enderecos = [
            '/admin/empreendimentos/empreendimento/',
            '/admin/trilhas/trilha/',
            '/admin/trilhas/inscricao/',
            '/admin/auth/group/',
        ]
        for endereco in enderecos:
            with self.subTest(endereco=endereco):
                self.assertEqual(self.client.get(endereco).status_code, 404)

    def test_a09_admin_anonimo_vai_ao_login_do_sistema(self):
        resposta = self.client.get('/admin/')
        self.assertRedirects(resposta, '/login/?next=/admin/', fetch_redirect_response=False)

    def test_a09_login_do_admin_nao_e_publico(self):
        resposta = self.client.get('/admin/login/')
        self.assertRedirects(resposta, '/login/?next=/admin/login/', fetch_redirect_response=False)

    def test_a09_login_do_admin_leva_staff_ao_admin(self):
        self.client.force_login(self.admin)

        resposta = self.client.get('/admin/login/')
        self.assertRedirects(resposta, reverse('admin:index'), fetch_redirect_response=False)

        resposta = self.client.get('/admin/login/?next=https://site-externo.com/')
        self.assertRedirects(resposta, reverse('admin:index'), fetch_redirect_response=False)

    def test_a09_login_do_admin_nega_quem_nao_e_staff(self):
        usuario = Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora', 'senha12345',
                                              papel=Usuario.Papel.IS)
        self.client.force_login(usuario)

        self.assertEqual(self.client.get('/admin/login/').status_code, 403)
        resposta = self.client.get('/admin/')
        self.assertRedirects(resposta, '/admin/login/?next=/admin/', target_status_code=403)


class PaginasDeErroTests(TestCase):
    """Seção 10 da spec mãe e F0, 3.5: páginas 403 e 404 do SGIS, sem detalhes técnicos."""

    def assertPaginaDoSgis(self, resposta, nome):
        self.assertContains(resposta, nome, status_code=resposta.status_code)  # cabeçalho do sistema
        self.assertContains(resposta, f'href="{reverse("home")}"', status_code=resposta.status_code)
        for detalhe in ('Traceback', 'PermissionDenied', 'Http404', 'urlpatterns'):
            self.assertNotContains(resposta, detalhe, status_code=resposta.status_code)

    def test_a03_logado_em_endereco_inexistente_ve_404_do_sgis(self):
        usuario = Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora', 'senha12345',
                                              papel=Usuario.Papel.IS)
        self.client.force_login(usuario)

        resposta = self.client.get('/nao-existe/')
        self.assertEqual(resposta.status_code, 404)
        self.assertTemplateUsed(resposta, '404.html')
        self.assertPaginaDoSgis(resposta, 'Incubadora')

    def test_a12_403_do_sgis_sem_detalhes_tecnicos(self):
        professor = Usuario.objects.create_user('prof@sgis.com', 'Professora Ana', 'senha12345',
                                                papel=Usuario.Papel.PROFESSOR)
        self.client.force_login(professor)

        resposta = self.client.get(reverse('criar_usuario'))
        self.assertEqual(resposta.status_code, 403)
        self.assertTemplateUsed(resposta, '403.html')
        self.assertPaginaDoSgis(resposta, 'Professora Ana')


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


class TextoFormatadoTests(TestCase):
    """TXT-01 e RN-19: só as marcações do mini editor sobrevivem, ao gravar e ao exibir."""

    def test_rn19_limpar_html_remove_script_e_onclick(self):
        sujo = (
            '<div><strong>Forte</strong> <em>leve</em> <b onclick="roubar()">b</b>'
            '<script>alert(1)</script><style>p{}</style><img src=x onerror="roubar()">'
            '<iframe src="https://x.com"></iframe><!-- comentário -->'
            '<ul><li>um</li></ul><ol><li>dois</li></ol>'
            '<a href="javascript:alert(1)">ruim</a></div>'
        )
        limpo = limpar_html(sujo)
        for proibido in ('script', 'alert', 'style', 'onclick', 'onerror', '<img',
                         '<iframe', 'comentário', 'javascript'):
            self.assertNotIn(proibido, limpo)
        for permitido in ('<strong>Forte</strong>', '<em>leve</em>', '<b>b</b>',
                          '<ul><li>um</li></ul>', '<ol><li>dois</li></ol>'):
            self.assertIn(permitido, limpo)

    def test_rn19_link_abre_em_nova_aba(self):
        limpo = limpar_html('<a href="https://ufsm.br" title="x" class="y">UFSM</a>')
        self.assertIn('href="https://ufsm.br"', limpo)
        self.assertIn('target="_blank"', limpo)
        self.assertIn('rel="noopener noreferrer"', limpo)
        self.assertNotIn('title', limpo)
        self.assertNotIn('class', limpo)
        self.assertIn('href="mailto:is@ufsm.br"', limpar_html('<a href="mailto:is@ufsm.br">e</a>'))

    def test_rn19_filtro_limpa_dado_antigo(self):
        """Um valor gravado por fora do formulário é limpo de novo ao exibir."""
        html = Template('{% load texto %}{{ valor|texto_formatado }}').render(
            Context({'valor': '<p>Oi <script>alert(1)</script><b onclick="x()">b</b></p>'}),
        )
        self.assertEqual(html, '<p>Oi <b>b</b></p>')

    def test_txt01_texto_simples_vira_paragrafos(self):
        """Sem o editor (no /admin/ ou com o CDN fora do ar), as quebras de linha ficam."""
        campo = TextoFormatadoField(required=False)
        self.assertEqual(campo.clean('um\ndois\n\ntrês < 4'), '<p>um<br>dois</p>\n\n<p>três &lt; 4</p>')
        self.assertEqual(campo.clean(''), '')

    def test_txt01_resumo_tira_marcacoes(self):
        html = Template('{% load texto %}{{ valor|texto_resumo:10 }}').render(
            Context({'valor': '<p>Peças <b>à mão</b> &amp; mais</p>'}),
        )
        self.assertEqual(html, 'Peças à m…')
