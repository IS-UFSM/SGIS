from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from trilhas import regras as regras_trilhas
from trilhas.models import Trilha
from usuarios.decorators import papel_requerido
from usuarios.models import Usuario

from . import regras
from .forms import ContatoForm, EmpreendimentoForm
from .models import Contato, Empreendimento

# Filtro por situação na lista: valor do parâmetro -> (rótulo, filtro).
FILTROS_SITUACAO = {
    'ativos': ('Ativos', {'desativado_em__isnull': True}),
    'desativados': ('Desativados', {'desativado_em__isnull': False}),
}

# Filtro por etapa atual (spec 3.4.2): as três etapas e "sem etapa".
SEM_ETAPA = 'sem'
FILTROS_ETAPA = [*Trilha.Etapa.choices, (SEM_ETAPA, 'Sem etapa')]

ACOES_SITUACAO = {
    'desativar': (regras.desativar, 'Empreendimento desativado.'),
    'reativar': (regras.reativar, 'Empreendimento reativado.'),
}


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


@login_required
def perfil_view(request, pk):
    """EMP-04 e EMP-05 (spec 3.5): o perfil, para quem pode vê-lo; senão, 403 (A-08 a A-10)."""
    empreendimento = get_object_or_404(
        Empreendimento.objects.select_related('representante'), pk=pk,
    )
    if not regras.pode_ver(request.user, empreendimento):
        raise PermissionDenied

    inscricoes = list(
        empreendimento.inscricoes.select_related('trilha').order_by('-inscrito_em')
    )
    # O nome da trilha só vira link para quem pode ver a trilha (plano, seção 6).
    trilhas_com_link = set(
        regras_trilhas.trilhas_visiveis(request.user)
        .filter(pk__in=[inscricao.trilha_id for inscricao in inscricoes])
        .values_list('pk', flat=True)
    )
    etapa = regras_trilhas.etapa_atual(empreendimento)
    return render(request, 'empreendimentos/perfil.html', {
        'empreendimento': empreendimento,
        'contatos': empreendimento.contatos.all(),  # 3.3a.8: quem vê o perfil vê os contatos
        'etapa_atual': Trilha.Etapa(etapa).label if etapa else 'Sem etapa',
        'inscricoes': inscricoes,
        'trilhas_com_link': trilhas_com_link,
        'e_is': request.user.papel == Usuario.Papel.IS,
    })


@login_required
def editar_view(request, pk):
    """EMP-01 (spec 3.3): só a IS edita; a conta do empreendimento não muda (A-03, A-05)."""
    regras.exigir_edicao(request.user)
    empreendimento = get_object_or_404(Empreendimento, pk=pk)
    nome_atual = empreendimento.nome  # a validação do form já altera a instância
    form = EmpreendimentoForm(request.POST or None, instance=empreendimento)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Dados de "{empreendimento.nome}" atualizados.')
        return redirect('empreendimentos:perfil', pk=empreendimento.pk)

    return render(request, 'empreendimentos/editar.html', {
        'form': form,
        'empreendimento': empreendimento,
        'nome_atual': nome_atual,
    })


@require_POST
@papel_requerido(Usuario.Papel.IS)
def situacao_view(request, pk, acao):
    """EMP-06: a IS desativa ou reativa o empreendimento, sempre por POST."""
    empreendimento = get_object_or_404(Empreendimento, pk=pk)
    funcao, sucesso = ACOES_SITUACAO[acao]
    funcao(empreendimento, request.user)
    messages.success(request, sucesso)
    return redirect('empreendimentos:perfil', pk=empreendimento.pk)


# Contatos (EMP-07, spec 3.3a): só a IS cria, edita, troca o responsável e remove (A-16).

def _contato(pk, contato):
    """O contato só é achado sob o próprio empreendimento: o de A não abre pelo endereço de B."""
    return get_object_or_404(Contato.objects.select_related('empreendimento'),
                             pk=contato, empreendimento_id=pk)


def _form_contato(request, empreendimento, contato=None):
    form = ContatoForm(request.POST or None, instance=contato)
    if request.method == 'POST' and form.is_valid():
        contato = regras.salvar_contato(request.user, form, empreendimento)
        messages.success(request, f'Contato "{contato.nome}" salvo.')
        return redirect('empreendimentos:perfil', pk=empreendimento.pk)
    return render(request, 'empreendimentos/contato_form.html', {
        'form': form, 'empreendimento': empreendimento, 'contato': contato,
    })


@login_required
def contato_novo_view(request, pk):
    """A-13, A-16b, A-16c: a IS cadastra um contato no perfil (3.3a.6)."""
    regras.exigir_edicao(request.user)
    empreendimento = get_object_or_404(Empreendimento, pk=pk)
    return _form_contato(request, empreendimento)


@login_required
def contato_editar_view(request, pk, contato):
    """A-14b, A-16b: a IS edita um contato; é assim que o provisório é preenchido (3.3a.9)."""
    regras.exigir_edicao(request.user)
    contato = _contato(pk, contato)
    return _form_contato(request, contato.empreendimento, contato)


@require_POST
@login_required
def contato_responsavel_view(request, pk, contato):
    """A-14: o contato vira o responsável, e o anterior continua na lista."""
    regras.exigir_edicao(request.user)
    contato = _contato(pk, contato)
    regras.tornar_responsavel(request.user, contato)
    messages.success(request, f'"{contato.nome}" agora é o responsável pelo empreendimento.')
    return redirect('empreendimentos:perfil', pk=pk)


@login_required
def contato_remover_view(request, pk, contato):
    """A-16d (3.3a.7): o GET pede confirmação; só o POST apaga."""
    regras.exigir_edicao(request.user)
    contato = _contato(pk, contato)
    if request.method == 'POST':
        regras.remover_contato(request.user, contato)
        messages.success(request, f'Contato "{contato.nome}" removido.')
        return redirect('empreendimentos:perfil', pk=pk)
    return render(request, 'empreendimentos/contato_remover.html', {
        'contato': contato, 'empreendimento': contato.empreendimento,
    })
