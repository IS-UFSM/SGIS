from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from empreendimentos.models import Empreendimento
from trilhas.models import Trilha
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste/mock (usuários, empreendimentos e trilhas).'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Dados de mock nunca vão para produção (RN-MVP-10).')
        self.stdout.write(self.style.NOTICE('Iniciando carga de dados de mock...'))

        # 1. Usuários de teste para cada papel
        usuarios_data = [
            {
                'email': 'admin@sgis.com',
                'nome': 'Administrador Geral',
                'papel': Usuario.Papel.ADMIN,
                'senha': 'admin123',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'is@sgis.com',
                'nome': 'Coordenação Incubadora Social',
                'papel': Usuario.Papel.IS,
                'senha': 'is123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'professor.carlos@sgis.com',
                'nome': 'Prof. Carlos Eduardo',
                'papel': Usuario.Papel.PROFESSOR,
                'senha': 'prof123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'professora.marina@sgis.com',
                'nome': 'Profa. Marina Silva',
                'papel': Usuario.Papel.PROFESSOR,
                'senha': 'prof123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'ana.costura@sgis.com',
                'nome': 'Ana Souza (Costura Criativa)',
                'papel': Usuario.Papel.EMPREENDIMENTO,
                'senha': 'emp123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'joao.horta@sgis.com',
                'nome': 'João Pereira (Horta Comunitária)',
                'papel': Usuario.Papel.EMPREENDIMENTO,
                'senha': 'emp123456',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        usuarios = {}
        for item in usuarios_data:
            usuario, created = Usuario.objects.get_or_create(
                email=item['email'],
                defaults={
                    'nome': item['nome'],
                    'papel': item['papel'],
                    'is_staff': item['is_staff'],
                    'is_superuser': item['is_superuser'],
                    'is_active': True,
                },
            )
            # Garante que a senha está devidamente configurada
            usuario.nome = item['nome']
            usuario.papel = item['papel']
            usuario.is_staff = item['is_staff']
            usuario.is_superuser = item['is_superuser']
            usuario.set_password(item['senha'])
            usuario.save()

            status = 'criado' if created else 'atualizado'
            self.stdout.write(f'  [OK] Usuario [{usuario.papel.upper()}] {usuario.email} ({status})')
            usuarios[item['email']] = usuario

        # 2. Empreendimentos de mock
        empreendimentos_data = [
            {
                'nome': 'Atelie Costura Solidaria',
                'tipo': 'Artesanato / Textil',
                'descricao': 'Producao artesanal sustentavel e geracao de renda para costureiras locais.',
                'usuario_empreendimento': usuarios['ana.costura@sgis.com'],
                'usuario_professor_supervisor': usuarios['professor.carlos@sgis.com'],
            },
            {
                'nome': 'Horta Urbana Verde Vivo',
                'tipo': 'Agroecologia / Alimentos',
                'descricao': 'Cultivo comunitario de hortalicas organicas com venda direta ao consumidor.',
                'usuario_empreendimento': usuarios['joao.horta@sgis.com'],
                'usuario_professor_supervisor': usuarios['professora.marina@sgis.com'],
            },
        ]

        for emp_info in empreendimentos_data:
            emp, created = Empreendimento.objects.get_or_create(
                nome=emp_info['nome'],
                defaults=emp_info,
            )
            status = 'criado' if created else 'ja existente'
            self.stdout.write(f'  [OK] Empreendimento: {emp.nome} ({status})')

        # 3. Trilhas de mock
        trilhas_data = [
            {
                'titulo': 'Trilha Base da Incubadora (Ciclo 1)',
                'descricao': 'Passos essenciais para estruturacao do modelo de negocio e formalizacao basica.',
                'tipo': Trilha.Tipo.PADRAO,
                'usuario_criador': usuarios['is@sgis.com'],
            },
            {
                'titulo': 'Mentoria de Precificacao e Custos',
                'descricao': 'Trilha personalizada focada em definicao de precos, margem e fluxo de caixa.',
                'tipo': Trilha.Tipo.CUSTOM,
                'usuario_criador': usuarios['professor.carlos@sgis.com'],
            },
        ]

        for tr_info in trilhas_data:
            trilha, created = Trilha.objects.get_or_create(
                titulo=tr_info['titulo'],
                defaults=tr_info,
            )
            status = 'criada' if created else 'ja existente'
            self.stdout.write(f'  [OK] Trilha [{trilha.tipo}]: {trilha.titulo} ({status})')

        self.stdout.write(self.style.SUCCESS('\nDados de mock populados com sucesso!'))
