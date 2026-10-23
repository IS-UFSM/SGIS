# Levantamento: código atual × spec v0.4

**Base:** `main` em `cbe3135` (2026-10-23) · 41 testes passando · Documento informativo, não precisa de aprovação.

Para cada requisito da [`SGIS_SPEC_MVP_v0.4.md`](SGIS_SPEC_MVP_v0.4.md), o que o código faz hoje. Serve de entrada para o `spec.md` e o `plan.md` de cada feature: o que está **diferente** vira tarefa de ajuste, o que está **faltando** vira tarefa nova.

**Legenda:** ✅ feito · 🟡 parcial · 🔀 feito diferente da spec · ❌ faltando

---

## Resumo

| Feature | ✅ | 🟡 | 🔀 | ❌ | Observação |
|---|---|---|---|---|---|
| Seção 4 · Nada sem login | 0 | 0 | 1 | 2 | Hoje a proteção é view por view |
| F1 · Acesso e contas | 1 | 5 | 1 | 7 | Só login, logout e criação de contas pela IS |
| F2 · Empreendimentos | 0 | 2 | 1 | 3 | Sem nenhuma tela; só pelo admin |
| F3 · Trilhas | 0 | 2 | 1 | 7 | Trilha sem atividades nem estados |
| F4 · Inscrição e etapas | 1 | 3 | 1 | 6 | Inscrição pela IS existe; etapas não |
| F5 · Execução e validação | 0 | 0 | 0 | 11 | Não existe |
| F6 · Visão do professor | 0 | 0 | 0 | 3 | Não existe |
| F7 · Prontuário | 0 | 0 | 0 | 4 | Não existe |
| F8 · Níveis por eixo | 0 | 0 | 0 | 5 | Não existe |
| F9 · Estatísticas | 0 | 0 | 0 | 3 | Não existe |

---

## Seção 4 · Nada sem login

| ID | Situação | Hoje |
|---|---|---|
| ACE-00 | 🔀 | Cada view tem `@login_required` ou `@papel_requerido`. Endereço inexistente responde **404** para anônimo, em vez de redirecionar ao login. |
| ACE-00a | ❌ | Não há verificação de saúde nem `robots.txt`. O `base.html` tem `<meta name="robots" content="noindex">`, o que ajuda, mas não substitui. |
| ACE-00b | ❌ | Não há proteção por padrão (`LoginRequiredMiddleware`) nem o teste que percorre todas as rotas. |

## F1 · Acesso e contas

| ID | Situação | Hoje |
|---|---|---|
| ACE-01 | 🟡 | Login por e-mail e senha, com o e-mail normalizado para minúsculas no form. Contas criadas pelo admin ou pelo `createsuperuser` podem ter maiúsculas e aí não entram. A mensagem "Esta conta está desativada" não é genérica (na prática é inalcançável, porque o `authenticate` já recusa contas inativas). |
| ACE-02 | 🟡 | Todos caem na mesma `home`, que mostra links conforme o papel. Não há área própria por papel. |
| ACE-03 | 🟡 | Logout existe. Não há expiração por inatividade (a sessão dura o padrão do Django, 2 semanas). |
| ACE-04 | ✅ | `/usuarios/novo/`: a IS cria professor e empreendedor com senha inicial e não consegue criar IS nem admin. O admin cria qualquer papel pelo `/admin/`. |
| ACE-05 | ❌ | Criar um empreendedor não cria o empreendimento. O empreendedor fica sem empreendimento e sem pré-incubação. |
| ACE-06 | ❌ | Não há `deve_trocar_senha`. |
| ACE-07 | ❌ | Não há troca de senha. *(Existe no repositório de entrega da disciplina, commit `26fd31f`, mas não nesta `main`.)* |
| ACE-08 | ❌ | Não há orientação na tela de login nem redefinição de senha pela IS. |
| ACE-09 | ❌ | O link "Usuários" abre só o formulário de criação. Não há lista, edição, desativação nem reativação. |
| ACE-10 | 🟡 | Conta inativa não entra, e a sessão aberta deixa de valer na próxima requisição (o Django checa `is_active`). Mas só dá para desativar pelo `/admin/`. |
| ACE-11 | ❌ | Nada impede desativar a si mesmo ou o último admin. |
| ACE-12 | 🔀 | Validadores do Django ativos, mas com o mínimo padrão de **8** caracteres. A spec pede 10. |
| ACE-13 | 🟡 | O admin é criado com `createsuperuser` (padrão do Django). A IS inicial vem de `IS_EMAIL` e `IS_SENHA_INICIAL` (migração `usuarios/0002`). |
| ACE-14 | ❌ | Sem bloqueio por tentativas (S). |

## F2 · Empreendimentos

| ID | Situação | Hoje |
|---|---|---|
| EMP-01 | 🔀 | Model tem nome, tipo e descrição. **Tipo é texto livre**, não a lista (MEI, Associação, Coletivo, Outro). **Faltam e-mail e telefone de contato.** Sem tela para a IS: só pelo `/admin/`. |
| EMP-02 | 🟡 | FK `representante` garante um representante por empreendimento. Mas um mesmo usuário pode representar **vários** empreendimentos (a RN-01 pede exatamente um), e nada impede que o representante não tenha o papel empreendedor. |
| EMP-03 | ❌ | Sem lista. |
| EMP-04 | ❌ | Sem perfil do empreendimento. |
| EMP-05 | ❌ | Depende do EMP-04. |
| EMP-06 | 🟡 | Campo `desativado_em` existe e o empreendimento desativado não pode ser inscrito. O representante continua entrando normalmente. Sem tela. |
| — | 🔀 | **Sobra:** campo `usuario_professor_supervisor`, que a v0.4 descartou (RN-03, sem supervisão). Também aparece no admin e no `popular_banco`. |

## F3 · Trilhas

| ID | Situação | Hoje |
|---|---|---|
| TRL-01 | 🔀 | A trilha tem `tipo` (`padrao` / `custom`) e a flag `pre_incubacao`. A v0.4 pede o campo **etapa** (vazio, pré-incubação, incubação, desincubação). Só existe a trilha de pré-incubação, criada pela migração `trilhas/0005`. |
| TRL-02 | 🟡 | O professor cria trilha com título e descrição (`/trilhas/nova/`). **Sem atividades.** |
| TRL-03 | ❌ | A IS não tem tela para as trilhas de etapa (só o `/admin/`). |
| TRL-04 | ❌ | Não existe model de atividade. |
| TRL-05 | ❌ | Sem estados: toda trilha é tratada como publicada. |
| TRL-06 | ❌ | Não há edição de trilha. |
| TRL-07 | ❌ | Não há edição (o dono existe: `usuario_criador`). |
| TRL-08 | ❌ | Depende do TRL-04 (S). |
| TRL-09 | ❌ | (C). |
| TRL-10 | 🟡 | IS vê todas (`/trilhas/todas/`) ✅; empreendedor vê as inscritas (`/trilhas/inscritas/`) ✅. O professor vê **só as dele**: não vê as trilhas de etapa nem as de outros professores nos empreendimentos que atende. |

## F4 · Inscrição e etapas

| ID | Situação | Hoje |
|---|---|---|
| INS-01 | 🟡 | A IS inscreve em `/trilhas/inscricoes/`. Mas pode escolher **qualquer** trilha: não há checagem de "publicada" (não há estados) e é possível inscrever direto numa trilha de etapa. |
| INS-02 | 🟡 | Um signal inscreve todo empreendimento novo na trilha de pré-incubação. Se ela não existir, só grava um aviso no log; a IS não é avisada. |
| INS-03 | ❌ | Sem "avançar etapa". |
| INS-04 | ❌ | Nada impede duas etapas ao mesmo tempo. |
| INS-05 | ❌ | Etapa atual não é calculada em lugar nenhum. |
| INS-06 | 🟡 | Ativa, Pausada e Cancelada, com motivo e transições (`TRANSICOES_INSCRICAO`). **Falta Concluída** (e `concluido_em`). |
| INS-07 | 🔀 | A restrição no banco considera "não cancelada". Com o status Concluída, precisa passar a considerar só **ativa ou pausada**, senão um empreendimento que concluiu uma trilha não pode ser reinscrito. |
| INS-08 | ❌ | Depende da F5. |
| INS-09 | ✅ | O empreendedor só vê as inscrições do próprio empreendimento (canceladas ficam ocultas). |
| INS-10 | ❌ | (S). |
| INS-11 | ❌ | Pendente de confirmação na spec. |

## F5 a F9

Nada implementado:
- **F5 · Execução e validação** (EXE-01 a 11): não há models de execução nem de histórico.
- **F6 · Visão do professor** (PRO-01 a 03): não há painel.
- **F7 · Prontuário** (PRN-01 a 04): não há model de nota.
- **F8 · Níveis por eixo** (EIX-01 a 05): não há model de nível.
- **F9 · Estatísticas** (EST-01 a 03): não há painel.

---

## Regras transversais (constituição e seções 6, 7 e 11 da spec)

| Regra | Situação | Hoje |
|---|---|---|
| RN-16 · Admin não acessa dados de negócio | 🔀 | O `/admin/` registra `Trilha`, `Inscricao` e `Empreendimento`. O admin vê e edita dados de negócio. |
| RN-11 · Nada se apaga | 🟡 | FKs de negócio usam `PROTECT` ✅. Mas o `/admin/` permite apagar trilhas e empreendimentos sem inscrição. |
| RNF-01 · Segurança | 🟡 | Produção com `DEBUG` desligado, HTTPS, cookies seguros e segredos no ambiente ✅. **Problema:** o login redireciona para o parâmetro `next` sem validar o destino (`redirect(request.GET.get('next'))`), o que permite *open redirect* para um site externo. |
| RNF-03 · Testes / Constituição Art. 6 | 🟡 | 41 testes, cobrindo permissões, trilhas, inscrições, cadastro e senha. **Nenhum cita o ID** do requisito. Não há CI nem o teste "toda rota exige login". `empreendimentos` não tem testes. |
| Constituição Art. 7.5 · Regras num lugar só | 🟡 | As transições de inscrição estão em `trilhas/views.py`, junto das views. |
| Limpeza | — | `CLASSES_INPUT` duplicado em `usuarios/forms.py` e `trilhas/forms.py`. |

---

## O que muda no código que já existe

Ajustes que as features vão precisar fazer em código existente (não são features novas):

| Onde | Mudança | Feature |
|---|---|---|
| `Trilha.tipo` + `Trilha.pre_incubacao` | Trocar pelo campo `etapa` e acrescentar `status`, `publicada_em`, `arquivada_em`, com migração de dados (a trilha de pré-incubação atual vira `etapa = pre_incubacao`, publicada) | F3 |
| Views, templates e testes que usam `Trilha.Tipo` e `pre_incubacao` | Atualizar para `etapa` | F3 |
| `Inscricao.Status` e restrição única | Acrescentar Concluída e `concluido_em`; restrição única passa a ser só entre ativa e pausada | F4 |
| `InscricaoForm` | Só trilhas de professor publicadas | F4 |
| Signal da pré-incubação | Passar a considerar a trilha publicada da etapa pré-incubação | F4 |
| `Empreendimento.usuario_professor_supervisor` | Remover (migração), e tirar do admin e do `popular_banco` | F2 |
| `Empreendimento.tipo` | Lista fixa + e-mail e telefone de contato | F2 |
| `Usuario` | `deve_trocar_senha`; senha mínima 10 | F1 |
| Login | Validar o `next` (`url_has_allowed_host_and_scheme`) | F1 |
| `sgis/settings.py` | `LoginRequiredMiddleware`, expiração por inatividade, `MinimumLengthValidator` com 10 | F1 / Seção 4 |
| `/admin/` | Tirar os models de negócio do admin, ou restringi-los ao superusuário técnico | F1 |
| `popular_banco` | Acompanhar as mudanças de model (etapa, sem supervisor) | F2 / F3 |
