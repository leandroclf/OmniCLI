# OmniCLI

Orquestrador local de ferramentas de inteligência artificial executadas por linha de comando.

O OmniCLI coordena CLIs já instaladas e autenticadas no ambiente do desenvolvedor para transformar uma ideia inicial em uma proposta arquitetural estruturada. A primeira versão usa subprocessos locais e não exige chaves de API próprias do OmniCLI.

> O projeto não promete custo zero absoluto. O uso continua sujeito às assinaturas, quotas, limites e termos de uso de cada provedor.

## O que existe nesta versão

- Pipeline configurável por YAML.
- Adaptador genérico para CLIs locais via stdin/stdout.
- Pipeline padrão com descoberta, revisão crítica, arquitetura, viabilidade e consolidação.
- Iterações controladas com `--loops`.
- Workspace por execução com prompts, respostas, logs e manifesto.
- Timeout, retry limitado e diagnóstico de provedores.
- Retomada e inspeção de execuções interrompidas.
- Validação preliminar do documento final.
- Modo de preview em Markdown no terminal.
- Testes automatizados e CI.

## Requisitos

- Linux.
- Python 3.10 ou superior.
- CLIs de IA instaladas e autenticadas, conforme o pipeline utilizado.

As ferramentas são executadas com as permissões do usuário atual. O OmniCLI não deve ser considerado um sandbox de segurança.

## Quickstart oficial

```bash
bash scripts/bootstrap.sh --apply --check
```

Esse é o único caminho recomendado para preparar o ambiente local. O bootstrap usa um ambiente virtual, não usa `sudo`, não instala CLIs de provedores e não inicia chamadas de IA automaticamente.

Consulte o [guia de bootstrap](docs/bootstrap.md) para configuração de caminhos, diagnóstico e execução controlada.

## Diagnóstico

```bash
omnicli providers check
```

O comando informa quais comandos estão disponíveis e tenta consultar suas versões.

## Primeira execução

Depois de instalar e autenticar as CLIs desejadas, use a configuração padrão:

```bash
omnicli conceive \
  "Aplicativo de meditação gamificado com progressão de RPG" \
  --loops 1 \
  --output design_arquitetura.md \
  --verbose
```

Para criar uma configuração editável:

```bash
omnicli init omnicli.yaml
omnicli conceive "Minha ideia" --config omnicli.yaml
```

Para visualizar o resultado no terminal:

```bash
omnicli conceive "Minha ideia" --preview
```

Para inspecionar ou retomar uma execução interrompida:

```bash
omnicli run inspect run-20260919-200000-123
omnicli run resume run-20260919-200000-123 --output proposta.md
```

## Workspace

Cada execução gera uma pasta semelhante a:

```text
.omnicli_workspace/run-20260919-200000-123/
├── input.md
├── 01-01-discovery.md
├── 01-02-critical-review.md
├── 01-03-architecture.md
├── 01-04-feasibility.md
├── 01-05-master-proposal.md
└── manifest.json
```

Por padrão, o conteúdo completo dos prompts não é persistido. Para habilitar esse registro, configure `retain_prompt_content: true` e avalie antes se o conteúdo pode conter dados sensíveis.

## Arquitetura

```text
CLI ──> PipelineRunner ──> ProviderAdapter ──> subprocesso local
              │                    │
              └──────────────> Workspace/Manifest
```

O núcleo depende de um contrato de adaptador. Isso permite adicionar integrações específicas sem espalhar comandos de provedores pelo orquestrador.

## Segurança e conformidade

- Não inclua segredos, dados pessoais ou código proprietário sem avaliar o destino do conteúdo.
- Não habilite persistência de prompts em ambientes sensíveis sem necessidade.
- Não execute comandos gerados por modelos automaticamente.
- Verifique os termos comerciais e limites das CLIs utilizadas.
- O processo filho pode herdar variáveis de ambiente e permissões do usuário.

## Desenvolvimento

```bash
pytest
ruff check .
mypy
```

## Roadmap

1. Estabilizar adaptadores e compatibilidade por versão.
2. Criar validadores de documentos por pipeline.
3. Implementar geração de código em workspace temporário com aprovação humana.
4. Evoluir para autocorreção controlada por patches e testes.

## Licença

MIT. Consulte `LICENSE`.
