# OmniCLI — Português

**Transforme uma ideia inicial em uma proposta de engenharia revisável, encadeando as CLIs de IA que você já utiliza.**

O OmniCLI é um orquestrador local e configurável para ferramentas de IA autenticadas por linha de comando. Seu primeiro fluxo conduz uma ideia por descoberta de produto, revisão crítica, arquitetura, viabilidade e edição técnica, preservando artefatos e rastreabilidade para revisão humana.

> O OmniCLI não promete “IA grátis”. Ele não exige chaves de API próprias, mas cada provedor continua sujeito à assinatura, quotas, licença, privacidade e termos de uso correspondentes.

## Diferencial

Enquanto muitos agentes priorizam escrever código, o OmniCLI começa pelo problema de comunicação anterior ao código: converter intenção ambígua em um plano explícito, questionado e rastreável.

- Utiliza CLIs já instaladas e autenticadas sem armazenar credenciais dos provedores.
- Incentiva discordância construtiva e separa fatos, hipóteses e recomendações.
- Produz Markdown legível e manifesto por execução.
- Configura papéis, instruções, timeouts, retries e provedores em YAML.
- Não executa shell, código gerado ou alterações em repositórios automaticamente.
- Permite inspecionar e retomar execuções interrompidas.

O projeto está em beta controlado. Use primeiro em pilotos técnicos com conteúdo
revisado e não sensível; o OmniCLI não é um sandbox.

Veja a [galeria da interface](interface.md) para exemplos visuais dos comandos,
do diagnóstico e do bootstrap.

Consulte também os critérios de [prontidão para produção](production-readiness.md),
o [plano de transição para produção](plano-transicao-producao.md), o
[contrato de avaliação](evaluation.md) e o [processo de release](release.md).

## Instalação recomendada

Requisitos: Linux, Python 3.10+ e as CLIs exigidas pelo pipeline.

```bash
git clone https://github.com/leandroclf/OmniCLI.git
cd OmniCLI
bash scripts/bootstrap.sh --apply --check
source .venv/bin/activate
omnicli doctor --capabilities
```

O bootstrap cria ambiente virtual e configuração locais. Ele não usa `sudo`, não instala CLIs de provedores e não chama modelos sem a opção explícita `--idea`.

Depois de instalar e autenticar Gemini CLI, Claude Code e Codex CLI:

```bash
omnicli conceive \
  "Aplicativo de meditação gamificado com progressão de RPG" \
  --loops 1 \
  --output proposta-arquitetura.md \
  --preview
```

### Loop condicional de qualidade

O comportamento padrão de `--loops` não muda: cada loop executa a esteira completa. Use `--refine` para transformar `--loops` no número máximo de passagens da proposta. Após cada `master-proposal`, o OmniCLI executa um quality gate determinístico e retorna somente ao trecho necessário da esteira — por exemplo, a `critical-review` quando faltam riscos ou decisões. O gate não delega a aprovação a um LLM opaco.

```bash
omnicli conceive \
  "Aplicativo de meditação gamificado com progressão de RPG" \
  --loops 3 \
  --refine \
  --output proposta-arquitetura.md \
  --verbose
```

O recurso é opt-in também pelo YAML:

```yaml
pipeline:
  quality_loop:
    enabled: false
    min_score: 80
    min_improvement: 3
    stable_passes: 1
    max_steps: 30
    max_calls: 50
    stop_on_quality: true
```

O manifesto registra histórico de qualidade, chamadas, passos consumidos,
passagens concluídas, fingerprint da configuração, versão do grafo e
`termination_reason`. O score mede sinais de completude e não garante correção;
toda proposta continua exigindo revisão humana.

### Verificação offline

Quando não for possível autenticar as CLIs, use:

```bash
omnicli conceive "Minha ideia" --dry-run --json
omnicli doctor --offline --json
omnicli lab verify --json
```

Esses comandos validam o plano, o transporte local, limites e regressões
sintéticas. Não comprovam compatibilidade com fornecedores nem substituem
benchmark humano.

## Diagnóstico

```bash
omnicli doctor --capabilities
omnicli doctor --capabilities --json
omnicli providers check --capabilities
omnicli providers check --offline
```

`doctor --capabilities` valida a configuração, executáveis obrigatórios, versões
e marcadores mínimos da ajuda local sem gerar conteúdo. Consulte a
[política de compatibilidade](provider-compatibility.md) para acompanhar as
mudanças oficiais sem prometer suporte automático a toda feature nova.

## Invocações padrão

| Provedor | Forma de execução | Estado padrão |
|---|---|---|
| Gemini CLI | `gemini -p "{prompt}" --output-format text` | habilitado |
| Claude Code | `claude -p "{prompt}" --output-format text` | habilitado |
| Codex CLI | `codex exec "{prompt}"` | habilitado |
| GitHub Copilot CLI | `copilot -p "{prompt}"` | habilitado, fora do pipeline padrão |

O placeholder `{prompt}` é enviado como um único argumento sem shell. Ferramentas personalizadas podem omiti-lo para receber o prompt por `stdin`.

O bootstrap também oferece `--official-docs` para verificar as URLs oficiais
registradas, sem enviar prompts nem instalar provedores.

## Segurança e rastreabilidade

Cada execução possui workspace isolado e `manifest.json` com status, versão do provedor, horários, tamanho das saídas e hashes SHA-256. O conteúdo integral dos prompts não é persistido por padrão.

Por privacidade, a ideia original fica somente como hash por padrão; para retomar
uma execução, informe novamente a ideia com `omnicli run resume RUN_ID --idea ...`.
Valores de ambiente são redigidos no manifesto. As entradas são delimitadas como
dados não confiáveis e as etapas recebem instruções para rejeitar tentativas
embutidas de trocar papéis, revelar segredos ou executar comandos. Essa medida
reduz risco, mas não garante imunidade a prompt injection.

Os subprocessos herdam permissões e ambiente do usuário. O OmniCLI não é um sandbox. Consulte o [modelo de ameaças](threat-model.md) e a [política de segurança](../SECURITY.md).

## Comunidade

Consulte a [análise de projetos similares](research/landscape.md), o [roadmap](../ROADMAP.md) e o [guia de contribuição](../CONTRIBUTING.md). Contribuições de compatibilidade, exemplos, traduções, documentação e avaliações são bem-vindas.
