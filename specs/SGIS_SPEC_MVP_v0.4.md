# SGIS — Especificação do MVP

**Versão:** 0.5.3 (revisão após a segunda reunião com a IS; ver seção 14)

**Substitui:** `_arquivo/SGIS_SPEC_MVP.md` (v0.3) e, para o MVP, o `_arquivo/MODELAGEM_BANCO.md`. A `_arquivo/SGIS_SPEC_COMPLETA.md` continua como registro da visão inicial, mas vários módulos dela foram descartados (ver seção 12).

**Convenções:** `ID` = requisito · `Prior.`: **M** obrigatório, **S** desejável, **C** só se sobrar tempo · `[Confirmar]` = decisão ainda pendente com a IS · `[ASSUMIDO]` = proposta da equipe, ainda não validada.

---

## 1. Objetivo

Um sistema fechado em que a Incubadora Social (IS) organiza as etapas da incubação, os professores oferecem trilhas personalizadas, e os empreendimentos percorrem as trilhas em que foram inscritos, marcando atividades que o dono da trilha valida.

**Hub e IS são a mesma coisa.** O sistema atende uma única incubadora.

---

## 2. Vocabulário

| Termo | Significado |
|---|---|
| **Empreendimento** | O negócio incubado (MEI, associação, coletivo…). |
| **Empreendedor** | Papel da **conta do empreendimento**: um login único, compartilhado pelas pessoas do empreendimento. A conta é o **representante** do empreendimento. Nas telas, aparece como "conta do empreendimento". |
| **Contato** | Registro de contato do empreendimento (nome, função, e-mail, telefone). Costuma ser uma pessoa, mas não precisa ser (pode ser um setor ou um e-mail geral). Não faz login e não tem vínculo com nenhum usuário do sistema. Um dos contatos é o **responsável** atual pelo empreendimento, que pode mudar com o tempo. |
| **Etapa** | Fase da incubação: **Pré-incubação → Incubação → Desincubação**. [Confirmar o nome da última etapa] |
| **Trilha de etapa** | Trilha criada pela IS, comum a todos os empreendimentos daquela etapa. Existe uma por etapa. |
| **Trilha personalizada** | Trilha criada por um professor ou pela IS, sem etapa, em que só alguns empreendimentos são inscritos. |
| **Dono da trilha** | Quem a criou. É quem edita e quem valida as atividades. |
| **Inscrição** | Decisão da IS de colocar um empreendimento numa trilha. |
| **Execução** | O andamento de uma atividade para um empreendimento inscrito. |
| **Liberação** | Ato do dono da trilha de tornar visível, para uma inscrição, uma atividade que não era visível desde a inscrição. |
| **Desistência** | Cancelamento de uma inscrição em trilha personalizada feito pelo próprio empreendimento. |
| **Banner** | Imagem com título e link opcional, exibida em carrossel no Início dos papéis a que se destina. |
| **Professor que atende** | Professor dono de alguma trilha em que o empreendimento está ou esteve inscrito. |
| **Prontuário** | Notas no perfil do empreendimento, para registrar o que já foi trabalhado. |
| **Nível por eixo** | Nível atual (N1, N2, N3) do empreendimento em cada um dos 5 eixos, definido pela IS. |

---

## 3. Papéis

| Papel | No MVP |
|---|---|
| **Empreendedor** | Vê o perfil do próprio empreendimento, as trilhas em que ele está inscrito e as atividades já liberadas, marca atividades como concluídas, vê devoluções, o prontuário e os níveis por eixo, e desiste de trilhas personalizadas. |
| **Professor** | Cria trilhas personalizadas, libera, valida ou devolve atividades delas, vê os empreendimentos que atende, com as trilhas e o status em cada uma, e escreve no prontuário deles. Não cancela inscrições. |
| **IS** | Cria contas de professores e empreendedores, mantém as trilhas de etapa, cria trilhas personalizadas, inscreve empreendimentos, avança etapas, cancela inscrições, libera e valida atividades nas trilhas de que é dona, define níveis por eixo, escreve no prontuário, mantém os banners e vê as estatísticas. |
| **Admin** | Gerencia contas de todos os papéis, inclusive IS e admin. Não acessa dados de negócio. |

Cada usuário tem um único papel.

---

## 4. Regra transversal: nada disponível sem login

| ID | Requisito | Prior. |
|---|---|---|
| ACE-00 | Todo endereço exige usuário autenticado. Anônimos são redirecionados ao login, **inclusive** em endereços que não existem. | M |
| ACE-00a | **Exceções públicas (lista fechada):** tela de login; verificação de saúde do serviço (responde só "ok"); `robots.txt` bloqueando indexação; arquivos estáticos, que não têm dados. | M |
| ACE-00b | Toda rota nova nasce protegida. Torná-la pública exige marcação explícita, revisada em code review. | M |

**Aceite ACE-00:** *Dado* um visitante sem sessão, *quando* abre qualquer endereço fora da lista de exceções (existente ou não), *então* vai ao login e nenhum dado ou mensagem de "não encontrado" é exibido.

---

## 5. Requisitos funcionais

### F1 · Acesso e contas

| ID | Requisito | Prior. |
|---|---|---|
| ACE-01 | Login com e-mail e senha. O e-mail não diferencia maiúsculas. Erro genérico: "e-mail ou senha incorretos". | M |
| ACE-02 | Após o login, o usuário vai para a área do seu papel. | M |
| ACE-03 | Logout e expiração da sessão por inatividade. | M |
| ACE-04 | A **IS cria contas** de professor e de empreendedor, definindo uma senha inicial. O **admin** cria contas de qualquer papel. A IS não cria contas IS nem admin. | M |
| ACE-05 | Ao criar um empreendedor, a IS informa também os dados do empreendimento (F2). Usuário e empreendimento são criados juntos: se um falhar, nenhum é salvo. | M |
| ACE-06 | Toda conta criada por outra pessoa nasce com **troca de senha obrigatória**: no primeiro acesso, o usuário só consegue usar o sistema depois de trocar a senha. | M |
| ACE-07 | O usuário altera a própria senha estando logado (exige a senha atual). | M |
| ACE-08 | **Esqueci a senha:** sem fluxo por e-mail no MVP. A tela de login orienta: "entre em contato com a Incubadora Social". A IS redefine a senha de professores e empreendedores, e a conta volta a exigir troca no próximo acesso. | M |
| ACE-09 | **Gestão de contas:** lista com nome, e-mail, papel, status e data de criação, com filtro por papel. A IS edita, desativa e reativa contas de professor e empreendedor; o admin, de todos os papéis. Nada é apagado. | M |
| ACE-10 | Conta desativada não entra e perde as sessões abertas. | M |
| ACE-11 | Ninguém desativa a si mesmo nem a última conta ativa de admin. | M |
| ACE-12 | A senha passa pelos validadores do Django, com **mínimo de 10 caracteres**. | M |
| ACE-13 | A primeira conta de admin é criada na implantação, por comando. A conta inicial da IS vem de variáveis de ambiente. | M |
| ACE-14 | Bloqueio temporário após tentativas de login malsucedidas repetidas. | S |

### F2 · Empreendimentos

| ID | Requisito | Prior. |
|---|---|---|
| EMP-01 | A IS cadastra e edita o empreendimento: nome, tipo (MEI, Associação, Coletivo, Outro), descrição, e-mail e telefone de contato. | M |
| EMP-02 | Cada empreendimento tem **uma única conta** (papel empreendedor), o seu representante, compartilhada pelas pessoas do empreendimento. | M |
| EMP-07 | **Contatos:** o empreendimento tem uma lista de contatos, cada um com **nome, e-mail e telefone (obrigatórios)** e função (opcional); um deles é marcado como **responsável** pelo empreendimento. O responsável **pode mudar**: trocar de responsável é marcar outro contato, sem mexer na conta do empreendimento. Contatos não fazem login e não são ligados a usuários. **Só a IS** cria, edita e **remove** os contatos. Remover apaga o contato de vez, com confirmação: contato não é registro de negócio. | M |
| EMP-03 | A IS lista os empreendimentos com filtros: ativos, desativados e por etapa atual. | M |
| EMP-04 | **Perfil do empreendimento:** dados, contatos, etapa atual, níveis por eixo, trilhas em que está inscrito (com status) e prontuário. | M |
| EMP-05 | Quem vê o perfil: a IS (todos), os professores que o atendem e o próprio representante. | M |
| EMP-06 | A IS desativa um empreendimento sem apagar histórico. O representante perde o acesso enquanto o empreendimento estiver desativado. | S |

### F3 · Trilhas

| ID | Requisito | Prior. |
|---|---|---|
| TRL-01 | Há dois tipos de trilha: **de etapa** (da IS, exatamente uma por etapa, criadas pelo sistema) e **personalizada** (criada por um professor ou pela IS). | M |
| TRL-02 | O professor e a IS criam trilhas personalizadas: título, descrição e atividades. Uma trilha personalizada da IS não é trilha de etapa. | M |
| TRL-03 | A IS cria e mantém a trilha de cada etapa: título, descrição e atividades. | M |
| TRL-04 | **Atividade:** título, descrição em **texto formatado** (TXT-01), obrigatória (sim/não), exige validação (padrão **sim**), **visível desde a inscrição** (sim/não), prazo fixo **ou** em dias após a atividade ficar disponível (EXE-02), e ordem. Não há tipo de atividade nem campo de endereço: links vão dentro da descrição. | M |
| TRL-05 | **Estados da trilha:** rascunho → publicada → arquivada. Publicar exige pelo menos uma atividade ativa. Rascunho não aparece para empreendimentos. | M |
| TRL-06 | Editar trilha publicada: ajustar textos e acrescentar atividades ao final. Atividade com progresso só pode ser arquivada. Trilha com progresso nunca é apagada. | M |
| TRL-07 | O dono edita a trilha. A IS também tem plenos poderes de edição sobre as trilhas personalizadas de professores (editar, publicar, arquivar), com uma confirmação antes de cada alteração. O dono continua sendo o professor. | M |
| TRL-08 | Reordenar atividades. | S |
| TRL-09 | Duplicar trilha. | C |
| TRL-10 | **Quem vê trilhas:** a IS vê todas; o professor vê as suas, as trilhas de etapa e, em leitura, as outras trilhas personalizadas em que os empreendimentos que ele atende estão inscritos; o empreendedor vê só as trilhas em que está inscrito. | M |

### F4 · Inscrição e etapas

| ID | Requisito | Prior. |
|---|---|---|
| INS-01 | A IS inscreve um empreendimento numa trilha personalizada **publicada**. | M |
| INS-02 | Todo empreendimento novo é inscrito automaticamente na trilha de **pré-incubação**. Se ela não estiver publicada, o cadastro avisa a IS e a inscrição é feita quando ela for publicada. [ASSUMIDO] | M |
| INS-03 | **Avançar etapa:** tela própria em que a IS move o empreendimento para a etapa seguinte. A inscrição na trilha da etapa atual vira **Concluída** e é criada a inscrição na trilha da próxima etapa. | M |
| INS-04 | O empreendimento está em **uma única etapa por vez**: no máximo uma inscrição ativa ou pausada em trilha de etapa. | M |
| INS-05 | A **etapa atual** é a trilha de etapa com inscrição ativa ou pausada. Não é guardada em campo próprio. | M |
| INS-06 | Status da inscrição: **Ativa, Pausada, Concluída, Cancelada**. A IS pausa, reativa ou cancela qualquer inscrição, com motivo opcional. O professor não cancela inscrições. O histórico é preservado. | M |
| INS-12 | **Desistência:** o empreendedor cancela a inscrição do próprio empreendimento numa trilha **personalizada**, ativa, com confirmação e sem motivo. Desistir de inscrição **pausada**: a resolver depois (pendência 10). Não desiste de trilha de etapa. A inscrição fica *Cancelada*, e a tela distingue "Desistência" de "Cancelada pela IS". | M |
| INS-07 | Não pode haver duas inscrições ativas ou pausadas do mesmo empreendimento na mesma trilha. | M |
| INS-08 | Com a inscrição pausada, o empreendedor vê a trilha, mas não marca atividades. Os prazos **não correm**: ao reativar, os prazos das execuções não concluídas são adiados pelo tempo que a inscrição ficou pausada, e nada fica atrasado durante a pausa. | M |
| INS-09 | O empreendedor vê só as inscrições do próprio empreendimento. | M |
| INS-10 | Inscrição de vários empreendimentos de uma vez. | S |
| INS-11 | Avançar a partir da Desincubação **encerra a incubação**: a inscrição fica Concluída e o empreendimento fica sem etapa ativa ("incubação concluída"). | M |

### F5 · Execução e validação

| ID | Requisito | Prior. |
|---|---|---|
| EXE-01 | Ao criar uma inscrição, o sistema cria uma **execução** para cada atividade ativa da trilha. Ao acrescentar uma atividade a uma trilha publicada, cria execuções para as inscrições ativas e pausadas. A execução nasce **liberada** se a atividade é visível desde a inscrição; senão, nasce **oculta** (EXE-12). | M |
| EXE-02 | **Prazo da execução:** o prazo fixo da atividade, ou os dias após a data em que a atividade ficou **disponível** para a inscrição: a data mais recente entre a inscrição e a criação da atividade, ou, se ela nasceu oculta, a data da **liberação**. Execução oculta não tem prazo. O prazo é adiado pelo tempo em que a inscrição ficou pausada (INS-08). | M |
| EXE-03 | Status da execução: **Pendente, Aguardando validação, Devolvida, Concluída**. **Atrasada** é calculada (não concluída e prazo vencido), nunca gravada. | M |
| EXE-04 | O empreendedor **marca como concluída**, com confirmação. Se a atividade exige validação, vai para *Aguardando validação*; senão, para *Concluída*. | M |
| EXE-05 | O empreendedor desfaz a marcação enquanto ela aguarda validação. | S |
| EXE-06 | **O dono da trilha valida ou devolve.** A devolução exige comentário, que o empreendedor vê; ele pode marcar de novo. | M |
| EXE-07 | O dono reabre uma atividade concluída, informando o motivo. Ela volta a *Pendente*. | S |
| EXE-08 | **Histórico** de cada execução (liberada, marcada, desfeita, validada, devolvida, reaberta), com autor, data e comentário. Nunca é apagado. | M |
| EXE-09 | **Progresso** da inscrição = atividades obrigatórias concluídas ÷ obrigatórias. *Aguardando validação* ainda não conta. Atividades arquivadas e execuções ocultas saem do cálculo; as arquivadas continuam no histórico. | M |
| EXE-10 | **Minhas atividades** (empreendedor): lista das execuções liberadas, com filtros Pendentes, Devolvidas, Concluídas e Atrasadas, ordenada por prazo. | M |
| EXE-11 | **Fila de validação** do dono (professor ou IS): execuções aguardando validação nas suas trilhas, da mais antiga para a mais nova. | M |
| EXE-12 | **Liberação por empreendimento:** a execução oculta não aparece para o empreendimento (nem o título) e não pode ser marcada. **Só o dono da trilha** a libera, para uma inscrição de cada vez, quando achar adequado; a IS não libera atividades das trilhas de professores. Uma execução liberada não volta a ficar oculta [ASSUMIDO]. | M |

**Transições:**

| Ação | Quem | De | Para | Condição |
|---|---|---|---|---|
| Marcar | Empreendedor | Pendente, Devolvida | Aguardando validação (ou Concluída) | Inscrição ativa e execução liberada |
| Desfazer | Empreendedor | Aguardando validação | Pendente | — |
| Validar | Dono da trilha | Aguardando validação | Concluída | — |
| Devolver | Dono da trilha | Aguardando validação | Devolvida | Comentário obrigatório |
| Reabrir | Dono da trilha | Concluída | Pendente | Motivo obrigatório |

A **liberação** (EXE-12) não muda o status: a execução continua *Pendente* e passa de oculta a liberada.

### F6 · Visão do professor

| ID | Requisito | Prior. |
|---|---|---|
| PRO-01 | **Painel do professor:** os empreendimentos que ele atende e, para cada um, as trilhas em que está inscrito, com status (progresso, aguardando validação, atrasadas). | M |
| PRO-02 | **Situação do empreendimento**, derivada das atividades: *Sem atividades*, *Em dia*, *Atenção* (atividade atrasada ou devolvida há mais de 7 dias) e *Concluído*. Painel ordenado com *Atenção* primeiro. [ASSUMIDO o prazo de 7 dias] | M |
| PRO-03 | O professor continua vendo o empreendimento depois que a inscrição na trilha dele é concluída ou cancelada (somente leitura). | M |

### F7 · Prontuário

| ID | Requisito | Prior. |
|---|---|---|
| PRN-01 | Cada empreendimento tem um prontuário: uma lista de **notas** (texto, autor, data), da mais recente para a mais antiga. | M |
| PRN-02 | Escrevem: a IS e os professores que atendem o empreendimento. | M |
| PRN-03 | Veem: a IS, os professores que atendem o empreendimento e o próprio empreendedor. | M |
| PRN-04 | Notas não são editadas nem apagadas; só acrescentadas. [ASSUMIDO] | M |

### F8 · Níveis por eixo

| ID | Requisito | Prior. |
|---|---|---|
| EIX-01 | Os 5 eixos são fixos: Empreendedor, Tecnológico, Mercado, Gestão e Capital. | M |
| EIX-02 | Cada empreendimento tem um **nível atual** (N1, N2 ou N3) em cada eixo, como um "status de RPG". Sem histórico no MVP. | M |
| EIX-03 | Só a IS define e altera os níveis, manualmente. | M |
| EIX-04 | O empreendedor e os professores que atendem o empreendimento veem os níveis (somente leitura). | M |
| EIX-05 | Nível de um empreendimento novo: vazio ("não avaliado") até a IS definir. [ASSUMIDO] | M |

### F9 · Estatísticas da IS

| ID | Requisito | Prior. |
|---|---|---|
| EST-01 | Painel da IS com: **contas** por papel e status; **empreendimentos** ativos e por etapa; **inscrições** por trilha; **atividades** por status, atrasadas e taxa geral de conclusão; **fila de validação** (quantidade e idade da mais antiga). | M |
| EST-02 | Quadro por professor: trilhas, empreendimentos atendidos, atividades aguardando validação. | S |
| EST-03 | Gráficos. | C |

### F10 · Banners

| ID | Requisito | Prior. |
|---|---|---|
| BAN-01 | A IS cadastra e edita banners: **imagem** (JPG ou PNG, até 1 MB), título, texto alternativo (obrigatório), link opcional e ordem. | M |
| BAN-06 | **Público do banner:** cada banner tem uma **flag por tipo de usuário** (mostrar para empreendedores, para professores, para a IS), que a IS marca no cadastro. É obrigatório marcar pelo menos uma. O banner só aparece para os papéis marcados. O admin não vê banners. | M |
| BAN-02 | A imagem é enviada pela IS na interface e guardada **no banco de dados**, para não depender do disco do servidor, que é apagado a cada implantação. | M |
| BAN-03 | O **Início** de cada papel mostra, depois do login, um **carrossel horizontal** com os banners ativos destinados a esse papel, na ordem definida. Não há data de início nem de fim: o banner fica no ar até a IS desativá-lo. | M |
| BAN-04 | A IS desativa e reativa banners. Banner desativado não aparece no carrossel. | M |
| BAN-05 | O carrossel é acessível: tem botões de anterior, próximo e pausa, funciona pelo teclado, e a troca automática para quando o usuário interage. | M |

---

## 6. Permissões

| Recurso | Ação | Empreendedor | Professor | IS | Admin |
|---|---|---|---|---|---|
| Contas | criar, editar, desativar, redefinir senha | — | — | professor e empreendedor | todas |
| Minha conta | alterar a própria senha | ✔ | ✔ | ✔ | ✔ |
| Empreendimentos | ver perfil | o próprio | os que atende | todos | — |
| Empreendimentos | criar, junto com o empreendedor | — | — | ✔ | ✔ |
| Empreendimentos | editar, desativar | — | — | ✔ | — |
| Contatos do empreendimento | ver | o próprio | dos que atende | todos | — |
| Contatos do empreendimento | criar, editar, remover | — | — | ✔ | — |
| Trilhas de etapa | criar, editar, publicar, arquivar | — | — | ✔ | — |
| Trilhas de etapa | ver | as inscritas (atual e anteriores) | ✔ | ✔ | — |
| Trilhas personalizadas | criar, editar, publicar, arquivar | — | as suas | as suas | — |
| Trilhas personalizadas de professores | editar, publicar, arquivar | — | — | ✔ (com confirmação) | — |
| Trilhas personalizadas | ver | as inscritas | as suas + as outras nos empreendimentos que atende | todas | — |
| Inscrição | criar, pausar, reativar, cancelar, avançar etapa | — | — | ✔ | — |
| Inscrição | desistir | as próprias, só em trilha personalizada | — | — | — |
| Inscrição | ver | as próprias | dos empreendimentos que atende | todas | — |
| Atividade | ver | as liberadas, nas próprias inscrições | ✔ (todas, nas inscrições que vê) | ✔ | — |
| Atividade | liberar | — | nas suas trilhas | nas trilhas de etapa e nas suas personalizadas | — |
| Atividade | marcar, desfazer | ✔ (as próprias, liberadas) | — | — | — |
| Atividade | validar, devolver, reabrir | — | nas suas trilhas | nas trilhas de etapa e nas suas personalizadas | — |
| Prontuário | escrever | — | dos que atende | ✔ | — |
| Prontuário | ler | o próprio | dos que atende | todos | — |
| Nível por eixo | definir | — | — | ✔ | — |
| Nível por eixo | ver | o próprio | dos que atende | todos | — |
| Estatísticas | ver | — | — | ✔ | — |
| Banners | criar, editar, desativar | — | — | ✔ | — |
| Banners | ver no Início | os destinados ao papel | os destinados ao papel | os destinados ao papel | — |

Qualquer acesso fora desta tabela, por lista, busca ou endereço direto, é negado (403) e nenhum dado é exibido.

---

## 7. Regras de negócio

| ID | Regra |
|---|---|
| RN-01 | Um usuário tem um único papel. A conta de papel empreendedor é representante de exatamente um empreendimento; os demais papéis não têm vínculo com empreendimento. |
| RN-02 | Um empreendimento tem uma única conta (representante), compartilhada pelas suas pessoas. As pessoas ficam registradas como contatos, sem login. |
| RN-03 | O professor se relaciona com um empreendimento **apenas por meio das trilhas dele**: atende quem está ou esteve inscrito nelas. Não há supervisão nem orientador fixo. |
| RN-04 | Quem valida é sempre o **dono da trilha**: a IS nas trilhas de etapa e nas personalizadas que criou, o professor nas dele. |
| RN-05 | A atividade só é marcada pelo empreendedor. Nenhum outro papel marca por ele. |
| RN-06 | Atividade que exige validação só conta como concluída depois de validada. |
| RN-07 | Atividade atrasada = não concluída com prazo vencido (calculado, nunca gravado). |
| RN-08 | Há exatamente uma trilha de etapa para cada etapa. |
| RN-09 | O empreendimento está em uma única etapa por vez. |
| RN-10 | Atividade com progresso e trilha com progresso são arquivadas, nunca apagadas. |
| RN-11 | Inscrições, execuções, histórico e prontuário nunca são apagados. |
| RN-12 | O nível por eixo só é alterado pela IS. |
| RN-13 | Conta desativada não entra e perde as sessões ativas. |
| RN-14 | Toda rota exige login, salvo a lista fechada da seção 4. |
| RN-15 | Dados fictícios nunca vão para produção. |
| RN-16 | O admin não acessa dados de negócio, exceto para informar os dados do empreendimento ao criar um empreendedor. |
| RN-17 | Só o dono da trilha libera atividades ocultas, uma inscrição por vez. Atividade oculta não é vista, não é marcada, não tem prazo e não conta no progresso. |
| RN-18 | O empreendedor só desiste de inscrição em trilha personalizada. O professor não cancela inscrições. |
| RN-19 | Todo texto formatado é limpo no servidor antes de ser gravado e exibido: só as marcações da lista de TXT-01 sobrevivem. |

---

## 8. Modelo de dados (MVP)

Substitui o `MODELAGEM_BANCO.md` para o escopo do MVP. Campos de auditoria (`criado_por`, `atualizado_por` etc.) ficam fora por enquanto.

| Entidade | Campos principais | Observações |
|---|---|---|
| **Usuário** | nome, e-mail (único, minúsculas), senha (hash), papel, ativo, deve_trocar_senha, último acesso, criado_em | Papéis: `admin`, `is`, `professor`, `empreendedor` |
| **Empreendimento** | nome, tipo, descrição (texto formatado), e-mail e telefone de contato, representante → Usuário, desativado_em | Nulo em `desativado_em` = ativo. E-mail e telefone continuam como contato geral do empreendimento |
| **Contato** | empreendimento, nome, função, e-mail, telefone, responsavel | Sem vínculo com Usuário. Nome, e-mail e telefone obrigatórios, exceto no contato provisório. No máximo um responsável por empreendimento. Na migração, cada empreendimento existente ganha um contato responsável **provisório** (placeholder), para a IS preencher |
| **Trilha** | título, descrição, etapa (vazio, `pre_incubacao`, `incubacao`, `desincubacao`), dono → Usuário, status, publicada_em, arquivada_em | Etapa vazia = trilha personalizada. No máximo uma trilha não arquivada por etapa |
| **Atividade da trilha** | trilha, título, descrição (texto formatado), ordem, obrigatória, exige_validacao, visivel_desde_inscricao, prazo_fixo, dias_apos_inscricao, criada_em, arquivada_em | Um dos dois prazos, ou nenhum. Os dias contam a partir da disponibilidade (EXE-02). Sem `tipo` e sem `endereço`: na migração, o endereço existente passa para o fim da descrição |
| **Inscrição** | empreendimento, trilha, status, inscrito_por (vazio = automática), inscrito_em, pausado_em, reativado_em, cancelado_em, cancelado_por → Usuário, concluido_em, motivo | Única por par entre as ativas e pausadas. `cancelado_por` distingue a desistência (INS-12) do cancelamento pela IS |
| **Execução da atividade** | inscrição, atividade, status, liberada_em, prazo, concluida_em, atualizada_em | Única por par inscrição–atividade. Vazio em `liberada_em` = oculta |
| **Histórico da atividade** | execução, ação, autor, comentário, criado_em | Só inserção |
| **Nota do prontuário** | empreendimento, autor, texto, criado_em | Só inserção |
| **Nível por eixo** | empreendimento, eixo, nível | Único por par empreendimento–eixo. Eixo é uma lista fixa |
| **Banner** | título, texto_alternativo, imagem (binária), tipo_da_imagem, link, mostrar_empreendedor, mostrar_professor, mostrar_is, ordem, ativo, criado_em | Imagem guardada no banco (BAN-02). As três flags de público (BAN-06): pelo menos uma marcada |

**Relacionamentos:**
```text
USUARIO 1 ─── 0..1 EMPREENDIMENTO            (representante)
EMPREENDIMENTO 1 ─── N CONTATO
USUARIO 1 ─── N TRILHA                       (dono)
TRILHA 1 ─── N ATIVIDADE_TRILHA
EMPREENDIMENTO 1 ─── N INSCRICAO N ─── 1 TRILHA
INSCRICAO 1 ─── N EXECUCAO_ATIVIDADE N ─── 1 ATIVIDADE_TRILHA
EXECUCAO_ATIVIDADE 1 ─── N HISTORICO_ATIVIDADE
EMPREENDIMENTO 1 ─── N NOTA_PRONTUARIO
EMPREENDIMENTO 1 ─── 5 NIVEL_EIXO
```

---

## 9. Jornadas e critérios de aceite

Cada jornada é um teste de ponta a ponta.

**J-1 · Contas**
> *Dado* a IS, *quando* cria um empreendedor com os dados do empreendimento, *então* os dois são criados e o empreendimento entra na trilha de pré-incubação. *Quando* o empreendedor entra pela primeira vez, *então* precisa trocar a senha antes de usar o sistema. *Dado* a IS, *quando* tenta criar uma conta IS ou admin, *então* o sistema recusa.

**J-2 · Nada sem login**
> *Dado* um visitante sem sessão, *quando* abre qualquer endereço fora das exceções, *então* vai ao login e nada é exibido. *Dado* um usuário de um papel, *quando* tenta abrir a área de outro, *então* o acesso é negado.

**J-3 · Etapas**
> *Dado* um empreendimento na pré-incubação, *quando* a IS avança a etapa, *então* a inscrição na pré-incubação fica *Concluída*, ele é inscrito na trilha de incubação, e não fica em duas etapas ao mesmo tempo.

**J-4 · Trilha personalizada e inscrição**
> *Dado* uma trilha personalizada publicada, *quando* a IS inscreve o empreendimento A, *então* ela aparece para A com as atividades visíveis desde a inscrição, todas pendentes, e **não** aparece para B. *Dado* uma trilha em rascunho, *então* nenhum empreendimento a vê e a IS não consegue inscrever ninguém nela.

**J-5 · Execução e validação**
> *Dado* uma atividade que exige validação, *quando* o empreendedor a marca, *então* ela fica *Aguardando validação* e o progresso não muda. *Quando* o dono a devolve sem comentário, *então* o sistema recusa; com comentário, o empreendedor o vê. *Quando* o dono a valida, *então* ela vira *Concluída*, o progresso é recalculado e o histórico mostra as três ações. *Dado* um professor que não é dono da trilha, *quando* tenta validar uma atividade dela, *então* o acesso é negado.

**J-6 · O professor acompanha**
> *Dado* um professor com dois empreendimentos inscritos nas suas trilhas, *quando* abre o painel, *então* vê cada um com suas trilhas e status, e o que tem atividade atrasada aparece primeiro como *Atenção*. *Quando* a inscrição de um deles é concluída, *então* ele continua aparecendo, em leitura.

**J-7 · Prontuário e níveis**
> *Dado* um empreendimento, *quando* um professor que o atende escreve uma nota, *então* a IS, o empreendedor e os outros professores que o atendem a veem, e um professor que não o atende não vê. *Quando* a IS altera um nível por eixo, *então* o empreendedor vê o novo nível; nenhum outro papel consegue alterá-lo.

**J-8 · Gestão de contas**
> *Dado* um usuário com sessão aberta, *quando* a IS (ou o admin) o desativa, *então* a sessão é encerrada e ele não entra mais. Ninguém desativa a última conta ativa de admin.

**J-9 · Liberação de atividades**
> *Dado* uma trilha com quatro atividades, das quais só as duas primeiras são visíveis desde a inscrição, *quando* a IS inscreve A e B, *então* os dois veem só as duas primeiras, e o progresso considera só elas. *Quando* o dono libera a terceira para A, *então* A a vê com prazo contado da liberação, e B continua sem vê-la. *Dado* um professor que não é dono da trilha, ou a IS numa trilha de professor, *quando* tenta liberar, *então* o acesso é negado. *Dado* uma execução oculta, *quando* o empreendedor tenta marcá-la por endereço direto, *então* o sistema recusa.

**J-10 · Desistência**
> *Dado* A inscrito numa trilha personalizada, *quando* o empreendedor de A desiste, *então* a inscrição fica *Cancelada*, registrada como desistência. *Dado* A na trilha de etapa, *então* a opção de desistir não existe e uma tentativa forjada é recusada. *Dado* um professor, *quando* tenta cancelar uma inscrição, *então* o acesso é negado.

**J-11 · Banners**
> *Dado* um banner ativo só com a flag de empreendedores marcada, *quando* um empreendedor abre o Início, *então* o banner aparece no carrossel; *quando* um professor abre o Início, *então* não aparece. *Quando* a IS desativa o banner, *então* ele some do carrossel. *Dado* um professor ou empreendedor, *quando* tenta cadastrar um banner, *então* o acesso é negado.

**J-12 · Texto formatado**
> *Dado* o dono de uma trilha, *quando* escreve na descrição de uma atividade um texto com negrito e um link, *então* o empreendedor vê o negrito e o link clicável. *Quando* o texto enviado contém um `<script>` ou um atributo `onclick`, *então* essas partes são removidas antes de gravar.

---

## 10. Telas

| Área | Telas |
|---|---|
| **Todos** | Login (com a orientação de "esqueci a senha") · Troca de senha obrigatória · Minha conta · Erros 403 e 404 |
| **Empreendedor** | Início (banners, próximas atividades e devoluções) · Meu empreendimento (perfil e contatos) · Minhas trilhas (com "desistir" nas personalizadas) · Detalhe da trilha · Minhas atividades |
| **Professor** | Início (banners) · Painel (empreendimentos × trilhas × status) · Fila de validação · Perfil do empreendimento · Minhas trilhas · Editor de trilha · Liberação de atividades por inscrição |
| **IS** | Início (banners) · Estatísticas · Contas · Empreendimentos (lista e cadastro) · Perfil do empreendimento (contatos, inscrições, níveis, prontuário) · Avançar etapa · Trilhas de etapa (editor) · Todas as trilhas e inscrição · Liberação de atividades por inscrição · Fila de validação · Banners |
| **Admin** | Contas (todas) |

---

## 11. Requisitos não funcionais

| ID | Requisito | Prior. |
|---|---|---|
| RNF-01 | **Segurança:** HTTPS, senhas com hash forte, cookies seguros, proteção CSRF, `DEBUG` desligado em produção, segredos só em variáveis de ambiente. | M |
| RNF-02 | **Isolamento testado automaticamente:** empreendimento A não vê B; professor só vê quem atende; só o dono valida. | M |
| RNF-03 | **Testes:** toda regra RN e toda jornada J com teste automatizado; teste "toda rota exige login" na CI. | M |
| RNF-04 | **Mobile:** telas do empreendedor utilizáveis em celular. | M |
| RNF-05 | **Acessibilidade:** contraste, navegação por teclado, status que não dependem só de cor. | M |
| RNF-06 | **Desempenho:** telas principais em até 3 s; listas paginadas. | M |
| RNF-07 | **Idioma:** pt-BR. | M |
| RNF-08 | **Hospedagem:** serviços gratuitos (Render: web e Postgres free) enquanto o projeto não tiver piloto com dados reais. | M |
| TXT-01 | **Texto formatado:** todo campo de texto longo editado na interface (descrições de trilha, atividade e empreendimento, notas do prontuário, comentários de devolução, motivos e texto dos banners) usa uma única caixa com **mini editor**: negrito, itálico, lista, link e parágrafo. Só essas marcações são aceitas (RN-19). Links abrem em nova aba. | M |

**Antes de um piloto com dados reais** (fora do MVP acadêmico): banco com backup e restauração testada (o Postgres gratuito do Render expira em 30 dias e não tem backup), termo de privacidade e avaliação de LGPD da hospedagem, e o bloqueio de tentativas de login (ACE-14).

---

## 12. Fora do MVP

### Adiado (pode voltar)
- **Acompanhamentos da IS:** registro de reuniões e ações com o empreendimento. Quando voltar, **não deve depender de trilha**.
- **Agendamento:** o empreendedor escolhe data e horário de um encontro.
- **Upload de evidências** nas atividades. [Confirmar com a IS se o MVP pode sair sem]
- **Auditoria** completa (quem alterou o quê, campos `*_por`).
- **Recuperação de senha por e-mail** e **convites** por e-mail.
- **Histórico dos níveis por eixo.**
- **Contas individuais** para cada pessoa do empreendimento (a v0.5 adotou uma conta compartilhada mais contatos).
- Etapas dentro da trilha; notificações; exportação de relatórios.

### Descartado (decisão da reunião ou da equipe)
- **Diagnóstico por questionário** (eixos × competências × perguntas): os níveis por eixo são definidos manualmente pela IS.
- **Demandas** e **Nexus** (demanda × oferta, pactuação).
- **Professor como projeto ou disciplina** (origem da oferta).
- **Ciclo, semestres e participação no ciclo:** a etapa atual vem da inscrição na trilha de etapa.
- **Supervisão** (professor fixo por empreendimento): o professor atua só pelas trilhas.
- **Hub** como entidade: é a própria IS.
- **Incubação 1 e 2** como etapas separadas: é uma só etapa de incubação.

---

## 13. Pendências a confirmar

| # | Pergunta | Proposta |
|---|---|---|
| 1 | Nome da última etapa | "Desincubação" (nome usado no protótipo da IS) |
| 2 | O que acontece ao avançar a partir da Desincubação | **Decidido** (F4, 7.1): encerra a incubação; a inscrição fica *Concluída* e o empreendimento fica sem etapa ativa |
| 3 | O MVP pode sair sem upload de evidências? | Sim; entregas são descritas na atividade e conferidas pelo dono |
| 4 | Notas do prontuário podem ser editadas ou apagadas? | Não; só acrescentadas |
| 5 | Nível inicial de um empreendimento novo | Vazio ("não avaliado") |
| 6 | Prazo para a situação *Atenção* | Atividade devolvida há mais de 7 dias |
| 7 | Desativar empreendimento tira o acesso do representante? | **Decidido** (F2, 7.4): sim, enquanto estiver desativado; a conta do representante continua ativa |
| 8 | Quem cria e edita os contatos do empreendimento (EMP-07)? | **Decidido** (2026-11-24): só a IS. Nome, e-mail e telefone são obrigatórios. Os contatos existem porque o responsável pelo empreendimento pode mudar, e não precisam corresponder a uma pessoa nem a um usuário. Os empreendimentos existentes ganham um contato provisório na migração |
| 9 | Arquivamento na trilha: o que o empreendedor e o dono esperam ver (rótulos "feito/realizado" e "remover")? | **A revisar.** Proposta: para o dono, o botão se chama "Remover atividade", mas por baixo continua sendo arquivamento (RN-10) |
| 10 | O empreendedor pode desistir de uma inscrição pausada? | **Adiada** (2026-11-24): a resolver depois, junto com as demais questões da pausa. Proposta: sim, como na ativa |
| 11 | Liberar uma atividade oculta para todos os inscritos de uma vez | Fora por ora; a liberação é por empreendimento. Pode voltar como atalho (S) |
| 12 | Os prazos correm com a inscrição pausada? | **Decidido** (2026-11-24): não. Ao reativar, os prazos são adiados pelo tempo da pausa (INS-08). Se o **prazo fixo** também é adiado fica **adiado** para depois; proposta: sim |
| 13 | O dono pode liberar uma atividade (EXE-12) com a inscrição pausada? | **Adiada** (2026-11-24): a resolver depois, junto com as demais questões da pausa. Proposta: não |
| 14 | Um contato pode ser removido? | **Decidido** (2026-11-24): sim, pela IS, com confirmação. O contato é apagado de vez, porque não é registro de negócio |

---

## 14. Mudanças

### Da v0.4 para a v0.5 (segunda reunião com a IS)

- **Banners** (F10): carrossel no Início, sem datas, com imagem enviada pela IS e guardada no banco, e uma flag por tipo de usuário para escolher quem vê cada banner (BAN-06).
- **Liberação de atividades** (EXE-12, RN-17): a atividade pode nascer oculta; o dono a libera por empreendimento; o prazo em dias conta da liberação; atividade oculta não conta no progresso.
- **Desistência** (INS-12, RN-18): o empreendedor desiste de trilha personalizada, sem motivo; a inscrição registra quem cancelou (`cancelado_por`). O professor não cancela nada.
- **Conta do empreendimento** (EMP-02, EMP-07, RN-01, RN-02): uma conta compartilhada por empreendimento mais uma lista de contatos sem login, com um responsável que pode mudar. O código do papel continua `empreendedor`.
- **Pausa** (INS-08): os prazos deixam de correr com a inscrição pausada (antes corriam).
- **Texto formatado** (TXT-01, RN-19): mini editor em todos os campos de texto longo, com HTML limpo no servidor. A atividade perde `tipo` e `endereço`.
- **Features já aprovadas que precisam de revisão de spec:** F2 (contatos), F3 (atividade sem tipo e endereço, visível desde a inscrição, texto formatado) e F4 (desistência e `cancelado_por`). A F5 nasce já com a liberação.

### Da v0.3 para a v0.4

- **Validação:** sempre pelo dono da trilha (antes: professor supervisor na trilha base, com a IS como exceção).
- **Trilha base por ciclo → trilha por etapa**, três etapas, sem tabela de ciclo; a etapa atual vem da inscrição; nova tela "avançar etapa".
- **Inscrição** ganha o status *Concluída*.
- **Sem convites:** a IS cria as contas com senha inicial e troca obrigatória no primeiro acesso; "esqueci a senha" é resolvido pela IS.
- **Sem supervisão:** a relação professor–empreendimento vem das trilhas.
- **Prontuário** simplificado para notas, visíveis também ao empreendedor, e entra no MVP (antes: opcional).
- **Níveis por eixo** entram no MVP, só com o nível atual (antes: opcional, com histórico).
- **Acompanhamentos** saem do MVP.
- **Papel "empreendimento" renomeado para "empreendedor"**, e o vínculo para "representante".
- Atividade ganha o campo **endereço** (para o tipo Link); senha mínima de **10 caracteres** passa a valer no código.
- Cronograma e capacidade da v0.3 foram retirados: serão definidos pela equipe a partir das issues.

---

## 15. Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-09-30 | MVP amplo: diagnóstico, demandas, Nexus, jornadas. |
| 0.2 | 2026-10-07 | MVP-0: 3 papéis, atividades, acompanhamentos, estatísticas; "nada sem login"; 8 semanas. |
| 0.3 | 2026-10-10 | Decisões da reunião: 4 papéis, trilha base e personalizadas, inscrição pela IS, validação pelo professor. |
| 0.4 | 2026-10-23 | Revisão da equipe após a reunião com a IS (ver seção 14). |
| 0.4.1 | 2026-10-23 | A IS também cria trilhas personalizadas e pode editar as dos professores; "trilha de professor" passa a se chamar "trilha personalizada" (decisões da `F3-trilhas/spec.md`). |
| 0.4.2 | 2026-10-28 | Decisões das specs F2 e F4: INS-11 (avançar a partir da Desincubação encerra a incubação) e EMP-06 (representante perde o acesso enquanto o empreendimento estiver desativado); pendências 2 e 7 da seção 13 fechadas. |
| 0.4.3 | 2026-11-04 | Decisão da spec F4 (7.7): a inscrição guarda a data de reativação (`reativado_em`, seção 8). |
| 0.4.4 | 2026-11-04 | Decisão da spec F0 (7.6): todos os arquivos estáticos são públicos (ACE-00a). |
| 0.4.5 | 2026-11-04 | Decisão da spec F1 (7.8): o admin informa os dados do empreendimento ao criar um empreendedor (RN-16 e tabela de permissões). |
| 0.5.0 | 2026-11-19 | Segunda reunião com a IS: banners (F10), liberação de atividades (EXE-12), desistência (INS-12), conta do empreendimento com contatos (EMP-07), texto formatado (TXT-01); atividade sem tipo e endereço (ver seção 14). |
| 0.5.1 | 2026-11-24 | Banners com uma flag de público por tipo de usuário (BAN-06). Contatos com um **responsável** que pode mudar, e contato provisório na migração (EMP-07). Prazos não correm com a inscrição pausada (INS-08, EXE-02; pendência 12). |
| 0.5.2 | 2026-11-24 | Contatos: só a IS edita; nome, e-mail e telefone obrigatórios; contato sem vínculo com usuário e não necessariamente uma pessoa (EMP-07). Questões da pausa adiadas (pendências 10, 12 e 13). |
| 0.5.3 | 2026-11-24 | A IS pode remover contatos, que são apagados de vez (EMP-07; pendência 14). |
