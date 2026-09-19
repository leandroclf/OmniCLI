# Bootstrap e operação local

O repositório possui um único caminho recomendado para instalação local: `scripts/bootstrap.sh`.

O script foi desenhado para ser seguro em ambientes de desenvolvimento:

- o modo padrão é `plan`;
- não instala nada sem `--apply` ou `OMNICLI_BOOTSTRAP_MODE=apply`;
- não usa `sudo` nem altera instalações globais;
- cria ou reutiliza um ambiente virtual local;
- não instala as CLIs de IA dos provedores;
- não executa o pipeline nem consome quotas sem `--idea` explícito;
- `--providers` executa o diagnóstico de prontidão e dos contratos de ajuda sem gerar conteúdo;
- `--official-docs` verifica opcionalmente as URLs oficiais registradas, sem executar provedores;
- a configuração existente nunca é sobrescrita automaticamente.

## Quickstart oficial

Na raiz do repositório:

```bash
bash scripts/bootstrap.sh --apply --check
```

Esse comando cria `.venv`, instala o pacote em modo editável, cria `omnicli.yaml` se necessário e executa os gates locais.

Depois, instale e autentique somente as CLIs de IA que serão utilizadas. O OmniCLI não instala essas ferramentas porque cada provedor possui distribuição, autenticação, versão e termos próprios.

Verifique o ambiente:

```bash
bash scripts/bootstrap.sh --apply --providers
bash scripts/bootstrap.sh --apply --providers --official-docs
```

Execute uma concepção somente quando desejar consumir a quota dos provedores:

```bash
bash scripts/bootstrap.sh \
  --apply \
  --idea "Aplicativo de meditação gamificado com progressão de RPG" \
  --loops 1 \
  --output design_arquitetura.md
```

Para usar o refinamento condicional de qualidade, acrescente `--refine`:

```bash
bash scripts/bootstrap.sh --apply \
  --idea "Aplicativo de meditação gamificado" \
  --loops 3 --refine --output proposta.md
```

## Modo de planejamento

Para visualizar as ações sem alterar o ambiente:

```bash
bash scripts/bootstrap.sh
```

O mesmo comportamento pode ser solicitado explicitamente:

```bash
OMNICLI_BOOTSTRAP_MODE=plan bash scripts/bootstrap.sh --check --providers
```

## Configuração e caminhos

As variáveis abaixo permitem executar o bootstrap em uma localização específica sem editar o script:

```bash
OMNICLI_VENV_DIR="$PWD/.venv-omnicli" \
OMNICLI_CONFIG="$PWD/config/omnicli.yaml" \
bash scripts/bootstrap.sh --apply --check
```

O script aceita caminhos relativos e os resolve a partir da raiz do repositório.

## O que o bootstrap não faz

O bootstrap não:

- instala Gemini, Claude, Codex ou GitHub Copilot;
- configura credenciais ou tokens;
- executa comandos gerados por modelos;
- envia a ideia inicial para um provedor sem `--idea` explícito;
- garante que uma CLI instalada aceite o mesmo formato de argumentos em todas as versões.

O diagnóstico cobre versão e marcadores mínimos na ajuda da CLI; ele não
certifica todas as features novas do fornecedor. A matriz, as fontes oficiais e
o procedimento de atualização estão em
[provider-compatibility.md](provider-compatibility.md).

Esses limites são intencionais. Eles mantêm o setup local previsível e evitam custos ou alterações externas inesperadas.

## Diagnóstico de problemas

```bash
bash scripts/bootstrap.sh --apply --check
bash scripts/bootstrap.sh --apply --providers
bash scripts/bootstrap.sh --apply --official-docs
source .venv/bin/activate
omnicli --help
```

Se um provedor obrigatório aparecer como indisponível ou incompatível, instale-o
e autentique-o conforme a documentação oficial do próprio provedor. Depois repita
`--providers`. Para integrar o diagnóstico a scripts, use
`omnicli doctor --capabilities --json`.
