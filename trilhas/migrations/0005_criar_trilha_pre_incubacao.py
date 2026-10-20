from django.db import migrations

TITULO = 'Pré-incubação'


def criar_trilha_pre_incubacao(apps, schema_editor):
    """Cria a trilha de pré-incubação e inscreve os empreendimentos ativos já existentes."""
    Usuario = apps.get_model('usuarios', 'Usuario')
    Trilha = apps.get_model('trilhas', 'Trilha')
    Inscricao = apps.get_model('trilhas', 'Inscricao')
    Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')

    if Trilha.objects.filter(pre_incubacao=True).exists():
        return

    criador = (
        Usuario.objects.filter(email='is@sgis.com').first()
        or Usuario.objects.filter(papel='is').order_by('id').first()
    )
    if criador is None:
        return

    trilha = Trilha.objects.create(
        titulo=TITULO,
        descricao='Trilha inicial em que todo novo empreendimento é inscrito automaticamente.',
        tipo='padrao',
        usuario_criador=criador,
        pre_incubacao=True,
    )

    ja_inscritos = Inscricao.objects.filter(trilha=trilha).values('empreendimento_id')
    for empreendimento in (
        Empreendimento.objects
        .filter(desativado_em__isnull=True)
        .exclude(id__in=ja_inscritos)
    ):
        Inscricao.objects.create(empreendimento=empreendimento, trilha=trilha, status='ativa')


def remover_trilha_pre_incubacao(apps, schema_editor):
    Trilha = apps.get_model('trilhas', 'Trilha')
    Inscricao = apps.get_model('trilhas', 'Inscricao')
    Inscricao.objects.filter(trilha__pre_incubacao=True, inscrito_por__isnull=True).delete()
    Trilha.objects.filter(pre_incubacao=True, titulo=TITULO, inscricoes__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('trilhas', '0004_pre_incubacao'),
        ('usuarios', '0002_criar_usuario_is_padrao'),
        ('empreendimentos', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(criar_trilha_pre_incubacao, remover_trilha_pre_incubacao),
    ]
