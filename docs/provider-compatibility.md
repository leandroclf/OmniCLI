# Compatibilidade com CLIs de provedores

Última verificação editorial: **2026-09-19**.

O OmniCLI integra processos locais, não APIs privadas dos provedores. Isso reduz
acoplamento a endpoints, mas não elimina mudanças de comandos, autenticação,
permissões, saída, versões ou termos de uso. Por isso, a configuração mantém um
contrato pequeno e explícito para cada CLI:

- `command` e `args`: invocação headless usada pelo pipeline;
- `version_args`: consulta de versão sem gerar conteúdo;
- `capability_args` e `required_capabilities`: sondagem da ajuda local;
- `documentation_url` e `installation_url`: fontes oficiais para manutenção.

## Contratos atualmente registrados

| Provedor | Invocação do OmniCLI | Sondagem segura | Fontes oficiais |
|---|---|---|---|
| Gemini CLI | `gemini -p "{prompt}" --output-format text` | `gemini --help` procura `-p` e `--output-format` | [headless](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md), [referência](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/cli-reference.md), [instalação](https://github.com/google-gemini/gemini-cli#installation) |
| Claude Code | `claude -p "{prompt}" --output-format text` | `claude --help` procura `-p` | [referência](https://code.claude.com/docs/en/cli-reference), [setup](https://code.claude.com/docs/en/setup) |
| Codex CLI | `codex exec "{prompt}"` | `codex --help` procura `exec` | [CLI](https://developers.openai.com/codex/cli) |
| GitHub Copilot CLI | `copilot -p "{prompt}"` | `copilot help` procura `-p` e `--prompt` | [conceito](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli), [instalação](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli) |

Os marcadores são um teste mínimo de contrato, não uma garantia de que todos os
recursos da versão instalada estejam disponíveis. Recursos novos só entram no
OmniCLI depois de uma alteração deliberada no adaptador, documentação, teste e
changelog.

## Como validar uma instalação

Depois do bootstrap:

```bash
omnicli doctor --capabilities
omnicli providers check --capabilities
```

Esses comandos consultam `--version` e a superfície de ajuda declarada. Não
enviam a ideia, não iniciam uma conversa e não executam ferramentas do agente.
Para integração automatizada, use JSON:

```bash
omnicli doctor --capabilities --json
```

O diagnóstico informa `status`, `capability_status`, URLs oficiais e se o
provedor é obrigatório para o pipeline atual. Um provedor ausente só bloqueia
`ready` quando é usado por uma etapa do pipeline.

Para testar se as páginas oficiais continuam acessíveis, sem executar CLIs:

```bash
bash scripts/bootstrap.sh --apply --official-docs
```

Esse teste de rede é opcional. A lista auditável está em
[`docs/provider-sources.txt`](provider-sources.txt), e não contém credenciais,
prompts ou dados de execução.

O GitHub Actions também executa essa checagem semanalmente e em alterações do
registro. Ela verifica disponibilidade das fontes e consistência do contrato,
mas não instala CLIs, não autentica contas e não chama modelos.

## Política de atualização

1. Consultar a documentação oficial antes de atualizar um contrato.
2. Registrar a URL, o comando headless e a data de verificação neste documento.
3. Atualizar `DEFAULT_CONFIG`, `omnicli.example.yaml` e os testes correspondentes.
4. Rodar `doctor --capabilities` com cada CLI disponível; quando possível,
   testar versões estáveis e de pré-lançamento em ambientes separados.
5. Publicar a mudança no `CHANGELOG.md` com migração, risco e rollback.
6. Nunca adicionar `--yolo`, `--allow-all-tools`, `--dangerously-skip-permissions`
   ou equivalente só porque uma nova versão os oferece. Autorização de
   ferramentas é uma decisão explícita do usuário e está fora da V1.

O projeto não promete acompanhar toda feature nova automaticamente. O controle
responsável é: fontes oficiais rastreadas, diagnóstico local sem custo, testes
de contrato opt-in e revisão humana antes de alterar o pipeline.

## Instalação e atualização

O bootstrap do OmniCLI não instala provedores nem autentica contas. Siga sempre
as instruções do fornecedor. As fontes acima documentam, entre outras opções,
`gemini update`, `claude update`, o instalador oficial do Codex e npm/Homebrew
ou o instalador oficial do Copilot CLI. A documentação atual do Claude Code e
do Copilot CLI também pode exigir Node.js 22+ em instalações npm recentes.

Não fixe versões dinâmicas de provedores no código do OmniCLI. O manifesto de
cada execução registra a versão observada, permitindo investigar regressões sem
transformar o projeto em instalador de quatro ecossistemas diferentes.
