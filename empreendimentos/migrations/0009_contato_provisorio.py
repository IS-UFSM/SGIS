"""F2 · T7: cada empreendimento existente ganha um contato provisório (EMP-07, 3.3a.9, decisão 7.9).

O contato provisório é o responsável, com e-mail e telefone vazios, para a IS preencher
pelo perfil. A reversa apaga só os contatos ainda provisórios.
"""

from django.db import migrations


def criar_provisorios(apps, schema_editor):
    Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
    Contato = apps.get_model('empreendimentos', 'Contato')
    Contato.objects.bulk_create([
        Contato(
            empreendimento=empreendimento, nome='A definir', email='', telefone='',
            responsavel=True, provisorio=True,
        )
        for empreendimento in Empreendimento.objects.filter(contatos__isnull=True)
    ])


def remover_provisorios(apps, schema_editor):
    Contato = apps.get_model('empreendimentos', 'Contato')
    Contato.objects.filter(provisorio=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('empreendimentos', '0008_contato'),
    ]

    operations = [
        migrations.RunPython(criar_provisorios, remover_provisorios),
    ]
