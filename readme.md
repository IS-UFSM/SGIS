# SGIS — Sistema de Gestão da Incubadora Social

Sistema web da **Incubadora Social da UFSM (IS)** para organizar a incubação de empreendimentos: a IS conduz cada empreendimento pelas etapas da incubação, professores oferecem trilhas de atividades, e os empreendedores percorrem as trilhas em que foram inscritos.

O projeto segue **Spec Driven Development**: nada é implementado antes de a especificação ser escrita e aprovada. Veja [Como trabalhamos](#como-trabalhamos).

---

## Sumário

- [Papéis](#papéis)
- [Situação do projeto](#situação-do-projeto)
- [Stack](#stack)
- [Rodando localmente](#rodando-localmente)
- [Testes](#testes)
- [Configuração](#configuração)
- [Deploy](#deploy)
- [Como trabalhamos](#como-trabalhamos)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Documentos do projeto](#documentos-do-projeto)
- [Contexto acadêmico](#contexto-acadêmico)

---

## Papéis

| Papel | O que faz no sistema |
|---|---|
| **IS** (Incubadora Social) | Cria contas de professores e empreendedores, mantém as trilhas de etapa, inscreve empreendimentos e os avança pelas etapas |
| **Professor** | Cria trilhas personalizadas e valida as atividades delas |
| **Empreendedor** | Representa um empreendimento: vê as trilhas em que ele está inscrito e marca as atividades |
| **Admin** | Gerencia as contas da plataforma; não acessa dados de negócio |

As etapas da incubação são **Pré-incubação → Incubação → Desincubação**. Todo empreendimento novo entra automaticamente na trilha de Pré-incubação.

Parte dessas funções ainda está em construção (por exemplo, marcar e validar atividades é a F5); veja a situação de cada uma abaixo.

## Situação do projeto

| Feature | Spec | Código |
|---|---|---|
| F0 · Fundação (nada sem login, admin, CI) | ✅ aprovada | ❌ |
| F1 · Acesso e contas | ✅ aprovada | 🟡 parcial |
| F2 · Empreendimentos | ✅ aprovada | 🟡 parcial |
| F3 · Trilhas | ✅ aprovada | ✅ concluída |
| F4 · Inscrição e etapas | ✅ aprovada | 🟡 parcial |
| F5 · Execução e validação | — | ❌ |
| F6 · Visão do professor | — | ❌ |
| F7 · Prontuário | — | ❌ |
| F8 · Níveis por eixo | — | ❌ |
| F9 · Estatísticas da IS | — | ❌ |

O detalhe, requisito por requisito, está em [`specs/levantamento-codigo-v0.4.md`](specs/levantamento-codigo-v0.4.md).

## Stack

- **Python 3.12+** e **Django 6.1**, com páginas renderizadas no servidor (templates do Django)
- **Tailwind CSS** por CDN
- **SQLite** em desenvolvimento e **PostgreSQL** em produção (via `DATABASE_URL`)
- **Render** (plano gratuito) para hospedagem, com **gunicorn** e **WhiteNoise**

Sem API pública, SPA ou framework de frontend.

## Rodando localmente

Pré-requisito: Python 3.12 ou mais novo.

1. Clone o repositório e entre na pasta:
   ```bash
   git clone https://github.com/IS-UFSM/SGIS.git
   ```
   ```bash
   cd SGIS
   ```
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   ```
   ```bash
   source .venv/Scripts/activate
   ```
   (No Linux e no macOS, `source .venv/bin/activate`.)
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Crie o banco local e aplique as migrações:
   ```bash
   python manage.py migrate
   ```
   As migrações já criam a conta inicial da IS (`is@sgis.com`, senha `is123456` em desenvolvimento) e as três trilhas de etapa.
5. (Opcional) Carregue dados fictícios, com professores, empreendedores, empreendimentos e trilhas com atividades:
   ```bash
   python manage.py popular_banco
   ```
   As contas e senhas fictícias estão em `usuarios/management/commands/popular_banco.py` (por exemplo, `professor.carlos@sgis.com` / `prof123456`). O comando se recusa a rodar com `DEBUG=False`: **nunca rode contra o banco de produção**.
6. Suba o servidor e acesse http://127.0.0.1:8000:
   ```bash
   python manage.py runserver
   ```

Para criar uma conta de admin local:
```bash
python manage.py createsuperuser
```

## Testes

```bash
python manage.py test
```
```bash
python manage.py makemigrations --check --dry-run
```

O primeiro roda toda a suíte; o segundo confere que não há migração pendente. Os dois precisam passar antes de qualquer merge. Os testes das features novas citam no nome o critério de aceite que cobrem (por exemplo `test_a09_publicar_exige_atividade_ativa`).

## Configuração

O `sgis/settings.py` lê a configuração de **variáveis de ambiente**. Localmente nenhuma é obrigatória: sem elas, o sistema roda em modo de desenvolvimento (`DEBUG` ligado e SQLite).

| Variável | Para quê | Padrão local |
|---|---|---|
| `DEBUG` | `True` ou `False` | `True` (no Render, `False`) |
| `SECRET_KEY` | Chave do Django; obrigatória com `DEBUG=False` | chave de desenvolvimento |
| `DATABASE_URL` | Endereço do banco | `sqlite:///db.sqlite3` |
| `IS_EMAIL` | E-mail da conta inicial da IS | `is@sgis.com` |
| `IS_SENHA_INICIAL` | Senha da conta inicial da IS; no Render, sem ela a conta não é criada | `is123456` |

O [`.env.example`](.env.example) documenta essas variáveis. **Nunca commite segredos**: chaves, senhas e endereços de banco ficam só no ambiente.

## Deploy

O deploy é no **Render**, descrito no [`render.yaml`](render.yaml) (Blueprint):

- um **web service** Python e um banco **PostgreSQL**, ambos no plano gratuito;
- o build instala as dependências, roda `collectstatic` e `migrate`;
- a `SECRET_KEY` é gerada pelo Render; `IS_EMAIL` e `IS_SENHA_INICIAL` são informadas no painel na criação.

Limites do plano gratuito: o serviço dorme depois de 15 minutos sem acesso (o primeiro acesso seguinte demora), o Postgres gratuito expira em 30 dias e não há backup. Para um piloto com dados reais, isso precisa mudar (ver seção 11 da spec mãe).

## Como trabalhamos

O projeto segue **Spec Driven Development**, com as regras na [constituição](specs/00-constituicao.md):

1. **Spec antes do código.** Cada feature tem uma pasta em `specs/` com:
   - `spec.md`: o quê e por quê, com os critérios de aceite;
   - `plan.md`: como implementar;
   - `tasks.md`: as tarefas, cada uma do tamanho de um PR.
2. **Aprovação.** Um documento só vale depois de aprovado pelo responsável pelo projeto. Código só começa com `spec.md` e `plan.md` aprovados.
3. **Regra nova vai primeiro para a spec**, nunca direto para o código.
4. **Tarefa vira issue** no GitHub, e a implementação entra por PR (modelo em [`.github/pull_request_template.md`](.github/pull_request_template.md)) citando os IDs da spec.

Convenções:
- Branches `docs/…`, `feat/…`, `fix/…`, `refactor/…`.
- Commits no formato `tipo: descrição`, em português (`feat: trilhas por etapa (F3 · T1)`).
- Código, interface e documentos em português, com o vocabulário da spec: **empreendimento** é o negócio, **empreendedor** é a pessoa, **representante** é o vínculo entre os dois.
- Permissões sempre checadas no servidor; registros de negócio nunca são apagados (desativar, cancelar, arquivar).

**Ferramentas de IA** (Claude Code, OpenCode e outras) seguem o [`AGENTS.md`](AGENTS.md): trabalham uma tarefa por vez, a partir da spec e do plano aprovados, e perguntam quando a spec tem lacuna.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `sgis/` | Configuração (`settings.py`, `urls.py`) e templates base |
| `usuarios/` | Contas, login, papéis, troca de senha, cadastro pela IS e o comando `popular_banco` |
| `empreendimentos/` | Empreendimentos e seus representantes |
| `trilhas/` | Trilhas, atividades, inscrições e as regras de permissão e estado (`regras.py`) |
| `specs/` | Constituição, spec mãe, specs de cada feature e o levantamento do código |
| `specs/_arquivo/` | Documentos substituídos, só como histórico |
| `AGENTS.md`, `CLAUDE.md` | Instruções para ferramentas de IA |
| `render.yaml` | Infraestrutura no Render |

## Documentos do projeto

- [Constituição](specs/00-constituicao.md): como o sistema é construído
- [Spec do MVP (spec mãe)](specs/SGIS_SPEC_MVP_v0.4.md): o que o sistema faz
- Specs das features: [F0](specs/F0-fundacao/spec.md) · [F1](specs/F1-acesso/spec.md) · [F2](specs/F2-empreendimentos/spec.md) · [F3](specs/F3-trilhas/spec.md) · [F4](specs/F4-inscricao/spec.md)
- [Levantamento do código × spec](specs/levantamento-codigo-v0.4.md)
- Reuniões com a IS: [08/10](https://docs.google.com/document/d/1hjom8iviEU5f6He7RsyRFO3UuHWmsLh_FywNCSXnfks/edit?tab=t.0#heading=h.4czhe7wpdyt5)

## Contexto acadêmico

O SGIS também é o trabalho da disciplina de **Desenvolvimento de Software para a Web** (ELC1090, UFSM). Os requisitos da disciplina e onde cada um é atendido:

| Requisito da disciplina | No SGIS |
|---|---|
| Frontend e backend integrados, com persistência no servidor | Django com templates; SQLite/PostgreSQL |
| Cadastro de usuários | A IS cria professores e empreendedores (F1) |
| Login e logout, com autenticação integrada | Sessões do Django; login por e-mail |
| Recurso associado ao usuário autenticado | Trilhas e atividades do professor; empreendimento do empreendedor |
| Operações protegidas no backend | Permissões por papel e por dono, checadas no servidor (`trilhas/regras.py`) |
| Deploy em infraestrutura gratuita | Render, plano gratuito |
