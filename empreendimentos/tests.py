from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from usuarios import regras as regras_usuarios
from usuarios.models import Usuario

from .models import Empreendimento


def criar_conta(email, papel=Usuario.Papel.EMPREENDEDOR):
    return Usuario.objects.create_user(email, 'Pessoa', 'senha-forte-123', papel=papel)


class RepresentanteTests(TestCase):
    """F2 · T1: EMP-02, RN-01 e RN-02 (spec 3.2)."""

    dados = {'nome': 'Ateliê', 'tipo': Empreendimento.Tipo.COLETIVO}

    def test_a04_empreendedor_nao_representa_dois(self):
        conta = criar_conta('joao@atelie.com')
        regras_usuarios.vincular_empreendimento(conta, self.dados)

        with self.assertRaises(ValidationError) as erro:
            regras_usuarios.vincular_empreendimento(conta, {**self.dados, 'nome': 'Horta'})
        self.assertIn('representante', erro.exception.error_dict)

        # O banco também recusa, mesmo por fora das regras.
        with self.assertRaises(IntegrityError):
            Empreendimento.objects.create(nome='Horta', tipo='outro', representante=conta)

    def test_a04_so_empreendedor_e_representante(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.IS, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                conta = criar_conta(f'{papel}@ufsm.br', papel=papel)
                with self.assertRaises(ValidationError) as erro:
                    regras_usuarios.vincular_empreendimento(conta, self.dados)
                self.assertEqual(erro.exception.error_dict['representante'][0].code, 'papel_invalido')
                self.assertFalse(Empreendimento.objects.filter(representante=conta).exists())


class MigracaoDoTipoTests(TransactionTestCase):
    """F2 · T1: a 0005 converte o tipo em texto livre, e a reversa o devolve (decisão 7.1)."""

    # A migração trilhas/0005 cria as trilhas de etapa no banco de testes; sem isto,
    # a limpeza do TransactionTestCase as apagaria para os testes seguintes.
    serialized_rollback = True

    antes = [('empreendimentos', '0004_email_telefone_contato')]
    depois = [('empreendimentos', '0005_converter_tipo')]

    def migrar(self, alvo):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(alvo)
        return executor.loader.project_state(alvo).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_migracao_converte_tipo_e_reversa_restaura(self):
        apps = self.migrar(self.antes)
        EmpreendimentoAntigo = apps.get_model('empreendimentos', 'Empreendimento')
        # A tabela de usuários continua no esquema atual: as contas usam o model de hoje.
        criar = lambda email, **campos: EmpreendimentoAntigo.objects.create(
            representante_id=criar_conta(email).pk, **campos,
        )
        livre = criar('a@a.com', nome='Ateliê', tipo='Artesanato / Textil', descricao='Peças à mão.')
        sem_descricao = criar('b@b.com', nome='Horta', tipo='alimentos', descricao='')
        valido = criar('c@c.com', nome='MEI do Zé', tipo='mei', descricao='Já na lista.')

        apps = self.migrar(self.depois)
        Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
        livre_novo = Empreendimento.objects.get(pk=livre.pk)
        self.assertEqual(livre_novo.tipo, 'outro')
        self.assertEqual(livre_novo.descricao, 'Peças à mão.\n\nTipo anterior: Artesanato / Textil')
        sem_descricao_novo = Empreendimento.objects.get(pk=sem_descricao.pk)
        self.assertEqual(
            (sem_descricao_novo.tipo, sem_descricao_novo.descricao),
            ('outro', 'Tipo anterior: alimentos'),
        )
        self.assertEqual(Empreendimento.objects.get(pk=valido.pk).tipo, 'mei')

        apps = self.migrar(self.antes)
        Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
        for original in (livre, sem_descricao, valido):
            restaurado = Empreendimento.objects.get(pk=original.pk)
            self.assertEqual(
                (restaurado.tipo, restaurado.descricao), (original.tipo, original.descricao),
            )
