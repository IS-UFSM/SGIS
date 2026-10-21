from django.test import TestCase
from django.urls import reverse

from .models import Usuario


def criar_is():
    return Usuario.objects.create_user(
        'is-teste@sgis.com', 'Incubadora', 'senha12345', papel=Usuario.Papel.IS,
    )


class CriarUsuarioViewTests(TestCase):
    """A IS cria usuários; os demais papéis não."""

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(reverse('criar_usuario'))
        self.assertRedirects(
            resposta,
            f"{reverse('login')}?next={reverse('criar_usuario')}",
        )

    def test_papel_diferente_de_is_recebe_403(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDIMENTO):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(
                    f'{papel}@sgis.com', 'Teste', 'senha12345', papel=papel,
                )
                self.client.force_login(usuario)
                resposta = self.client.get(reverse('criar_usuario'))
                self.assertEqual(resposta.status_code, 403)
                self.client.logout()

    def test_is_cria_professor_e_consegue_logar(self):
        self.client.force_login(criar_is())
        resposta = self.client.post(reverse('criar_usuario'), {
            'nome': 'Maria das Trilhas',
            'email': 'maria@escola.com',
            'papel': Usuario.Papel.PROFESSOR,
            'senha': 'senha-super-segura',
        })

        self.assertRedirects(resposta, reverse('criar_usuario'))
        usuario = Usuario.objects.get(email='maria@escola.com')
        self.assertEqual(usuario.nome, 'Maria das Trilhas')
        self.assertEqual(usuario.papel, Usuario.Papel.PROFESSOR)
        self.assertTrue(usuario.check_password('senha-super-segura'))
        self.assertFalse(usuario.check_password('senha-super-segura'[:1]))
        self.assertTrue(
            self.client.login(email='maria@escola.com', password='senha-super-segura'),
        )

    def test_is_cria_empreendimento(self):
        self.client.force_login(criar_is())
        resposta = self.client.post(reverse('criar_usuario'), {
            'nome': 'Ateliê da Praça',
            'email': 'contato@atelie.com',
            'papel': Usuario.Papel.EMPREENDIMENTO,
            'senha': 'senha-super-segura',
        })

        self.assertRedirects(resposta, reverse('criar_usuario'))
        usuario = Usuario.objects.get(email='contato@atelie.com')
        self.assertEqual(usuario.papel, Usuario.Papel.EMPREENDIMENTO)

    def test_is_nao_consegue_criar_is_ou_admin(self):
        """Mesmo enviando o papel direto no POST, a validação bloqueia."""
        self.client.force_login(criar_is())

        for papel in (Usuario.Papel.IS, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                resposta = self.client.post(reverse('criar_usuario'), {
                    'nome': 'Forjado',
                    'email': f'forjado-{papel}@sgis.com',
                    'papel': papel,
                    'senha': 'senha-super-segura',
                })
                self.assertEqual(resposta.status_code, 200)  # re-renderiza o form
                erros = resposta.context['form'].errors
                self.assertIn('papel', erros)
                self.assertTrue(erros['papel'][0].startswith('Faça uma escolha válida'))
                self.assertFalse(Usuario.objects.filter(email=f'forjado-{papel}@sgis.com').exists())

    def test_email_duplicado_e_recusado(self):
        Usuario.objects.create_user(
            'maria@escola.com', 'Maria', 'senha12345', papel=Usuario.Papel.PROFESSOR,
        )
        self.client.force_login(criar_is())
        resposta = self.client.post(reverse('criar_usuario'), {
            'nome': 'Outra Maria',
            'email': 'maria@escola.com',
            'papel': Usuario.Papel.PROFESSOR,
            'senha': 'senha-super-segura',
        })

        self.assertEqual(resposta.status_code, 200)
        erros = resposta.context['form'].errors
        self.assertIn('email', erros)
        self.assertIn('já existe', erros['email'][0])

    def test_senha_curta_e_recusada(self):
        self.client.force_login(criar_is())
        resposta = self.client.post(reverse('criar_usuario'), {
            'nome': 'Maria das Trilhas',
            'email': 'maria@escola.com',
            'papel': Usuario.Papel.PROFESSOR,
            'senha': '123',
        })

        self.assertEqual(resposta.status_code, 200)
        erros = resposta.context['form'].errors
        self.assertIn('senha', erros)
        self.assertIn('8 caracteres', erros['senha'][0])
