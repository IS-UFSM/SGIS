from django.shortcuts import render

from trilhas import regras as regras_trilhas
from trilhas.models import Trilha
from usuarios.decorators import papel_requerido
from usuarios.models import Usuario

from .models import Empreendimento

# Filtro por situação na lista: valor do parâmetro -> (rótulo, filtro).
FILTROS_SITUACAO = {
    'ativos': ('Ativos', {'desativado_em__isnull': True}),
    'desativados': ('Desativados', {'desativado_em__isnull': False}),
}

# Filtro por etapa atual (spec 3.4.2): as três etapas e "sem etapa".
SEM_ETAPA = 'sem'
FILTROS_ETAPA = [*Trilha.Etapa.choices, (SEM_ETAPA, 'Sem etapa')]


@papel_requerido(Usuario.Papel.IS)
def lista_view(request):
    """EMP-03 (spec 3.4): a IS lista os empreendimentos, com filtros combináveis (A-06, A-07)."""
    empreendimentos = regras_trilhas.anotar_etapa_atual(
        Empreendimento.objects.select_related('representante').order_by('nome'),
    )

    situacao = request.GET.get('situacao', '')
    if situacao in FILTROS_SITUACAO:
        empreendimentos = empreendimentos.filter(**FILTROS_SITUACAO[situacao][1])
    else:
        situacao = ''

    etapa = request.GET.get('etapa', '')
    if etapa == SEM_ETAPA:
        empreendimentos = empreendimentos.filter(etapa_atual__isnull=True)
    elif etapa in Trilha.Etapa.values:
        empreendimentos = empreendimentos.filter(etapa_atual=etapa)
    else:
        etapa = ''

    empreendimentos = list(empreendimentos)
    for empreendimento in empreendimentos:
        empreendimento.etapa_rotulo = (
            Trilha.Etapa(empreendimento.etapa_atual).label if empreendimento.etapa_atual else 'Sem etapa'
        )

    return render(request, 'empreendimentos/lista.html', {
        'empreendimentos': empreendimentos,
        'situacoes': [(valor, rotulo) for valor, (rotulo, _) in FILTROS_SITUACAO.items()],
        'situacao_atual': situacao,
        'etapas': FILTROS_ETAPA,
        'etapa_atual': etapa,
    })
