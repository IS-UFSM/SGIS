from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from usuarios.decorators import papel_requerido
from usuarios.models import Usuario

from .forms import InscricaoForm, TrilhaForm
from .models import Inscricao, Trilha


@papel_requerido(Usuario.Papel.PROFESSOR)
def minhas_trilhas_view(request):
    """Lista as trilhas personalizadas criadas pelo professor logado."""
    trilhas = Trilha.objects.filter(usuario_criador=request.user).order_by('-id')
    return render(request, 'trilhas/minhas_trilhas.html', {'trilhas': trilhas})


@papel_requerido(Usuario.Papel.PROFESSOR)
def criar_trilha_view(request):
    """Professor cria uma trilha personalizada. Tipo e criador vêm do servidor."""
    form = TrilhaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        trilha = form.save(commit=False)
        trilha.tipo = Trilha.Tipo.CUSTOM
        trilha.usuario_criador = request.user
        trilha.save()
        messages.success(request, f'Trilha "{trilha.titulo}" criada com sucesso.')
        return redirect('trilhas:minhas')

    return render(request, 'trilhas/criar_trilha.html', {'form': form})


@papel_requerido(Usuario.Papel.IS)
def todas_trilhas_view(request):
    """IS vê todas as trilhas do sistema, com filtro opcional por tipo."""
    trilhas = Trilha.objects.select_related('usuario_criador').order_by('-id')

    tipo = request.GET.get('tipo', '')
    if tipo in Trilha.Tipo.values:
        trilhas = trilhas.filter(tipo=tipo)
    else:
        tipo = ''

    return render(request, 'trilhas/todas_trilhas.html', {
        'trilhas': trilhas,
        'tipos': Trilha.Tipo.choices,
        'tipo_atual': tipo,
    })


@papel_requerido(Usuario.Papel.IS)
def inscricoes_view(request):
    """IS lista as inscrições e inscreve empreendimentos em trilhas."""
    form = InscricaoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        inscricao = form.save(commit=False)
        inscricao.inscrito_por = request.user
        inscricao.save()
        messages.success(
            request,
            f'{inscricao.empreendimento} inscrito na trilha "{inscricao.trilha}".',
        )
        return redirect('trilhas:inscricoes')

    inscricoes = (
        Inscricao.objects
        .select_related('empreendimento', 'trilha', 'inscrito_por')
        .order_by('-inscrito_em')
    )
    return render(request, 'trilhas/inscricoes.html', {
        'form': form,
        'inscricoes': inscricoes,
    })


# Transições permitidas: ação -> (status de origem, status de destino).
TRANSICOES_INSCRICAO = {
    'pausar': ({Inscricao.Status.ATIVA}, Inscricao.Status.PAUSADA),
    'reativar': ({Inscricao.Status.PAUSADA}, Inscricao.Status.ATIVA),
    'cancelar': (
        {Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA},
        Inscricao.Status.CANCELADA,
    ),
}


@require_POST
@papel_requerido(Usuario.Papel.IS)
def alterar_inscricao_view(request, pk, acao):
    """IS pausa, reativa ou cancela uma inscrição. O registro nunca é apagado."""
    inscricao = get_object_or_404(Inscricao, pk=pk)
    origens, destino = TRANSICOES_INSCRICAO[acao]

    if inscricao.status not in origens:
        messages.error(request, 'Esta ação não é permitida para o status atual.')
        return redirect('trilhas:inscricoes')

    inscricao.status = destino
    if destino == Inscricao.Status.PAUSADA:
        inscricao.pausado_em = timezone.now()
    elif destino == Inscricao.Status.CANCELADA:
        inscricao.cancelado_em = timezone.now()
    motivo = request.POST.get('motivo', '').strip()
    if motivo:
        inscricao.motivo = motivo
    inscricao.save()

    messages.success(request, f'Inscrição {inscricao} atualizada: {inscricao.get_status_display()}.')
    return redirect('trilhas:inscricoes')


@papel_requerido(Usuario.Papel.EMPREENDIMENTO)
def trilhas_inscritas_view(request):
    """Empreendimento vê as trilhas em que está inscrito (canceladas ficam ocultas)."""
    inscricoes = (
        Inscricao.objects
        .filter(
            empreendimento__usuario_empreendimento=request.user,
            empreendimento__desativado_em__isnull=True,
        )
        .exclude(status=Inscricao.Status.CANCELADA)
        .select_related('empreendimento', 'trilha')
        .order_by('empreendimento__nome', '-inscrito_em')
    )
    return render(request, 'trilhas/trilhas_inscritas.html', {'inscricoes': inscricoes})
