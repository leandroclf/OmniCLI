# Contexto opcional de codebase

O OmniCLI pode fundamentar uma proposta em trechos selecionados de uma pasta
local ou de um repositório Git HTTPS. O modo é somente leitura e não executa
scripts, testes, hooks nem código do projeto.

```bash
omnicli conceive "Adicionar processamento assíncrono" \
  --project ./meu-projeto --context-preview

omnicli conceive "Adicionar processamento assíncrono" \
  --project ./meu-projeto --output proposta.md

omnicli conceive "Adicionar processamento assíncrono" \
  --repo https://github.com/empresa/projeto.git --ref main \
  --context-preview
```

`--context-preview` imprime JSON com os trechos **exatos** selecionados, caminhos,
hashes SHA-256, commit Git (quando disponível), estado de alterações locais e
fingerprint do contexto. Nenhuma CLI de IA é chamada. Revise o JSON antes de
executar o pipeline. `--dry-run --json` também inclui metadados resumidos do
contexto, sem os trechos.

Para retomar, informe a mesma ideia original e a mesma fonte:

```bash
omnicli run resume RUN_ID --idea "Adicionar processamento assíncrono" \
  --project ./meu-projeto
```

A retomada é recusada quando o fingerprint dos arquivos selecionados muda.
Para Git remoto, a referência é resolvida para um commit; uma branch que avançou
precisa ser substituída pela referência adequada à execução original. O
manifesto armazena caminhos, hashes e fingerprint, mas não trechos de código.

## Seleção e limites

- Em pasta Git, são considerados arquivos rastreados e não rastreados que não
  estejam ignorados. Em pasta sem Git, há varredura limitada do diretório.
- São examinados até 5.000 caminhos. Um arquivo com mais de 128 KB é ignorado.
- São selecionados até 24 arquivos; o trecho de cada um tem até 900 caracteres.
  O contexto total é limitado a 24.000 caracteres.
- A busca de relevância examina até 240 arquivos e 10 MB de texto elegível;
  os trechos incluem a linha inicial, mas não a totalidade dos arquivos.
- Pastas de dependências, artefatos, arquivos binários, links simbólicos, nomes
  típicos de credenciais e arquivos com padrões simples de segredos são ignorados.
- A seleção é determinística e prioriza caminhos relacionados à ideia, código,
  documentação e manifestos de dependências.
- Git remoto é clonado temporariamente com `--no-checkout`, sem recursão de
  submódulos, e lido pelos objetos Git. A URL deve ser HTTPS pública, sem
  credenciais embutidas; o helper de credenciais é desabilitado. O commit
  observado fica registrado.

Isso é uma amostra, não uma indexação completa, auditoria de segurança ou
prova de que um arquivo ausente na amostra não existe no projeto. A filtragem
de segredos é defensiva e não garante detecção de todo dado sensível. Não use
este modo com código confidencial sem uma revisão explícita da prévia e das
políticas dos provedores.

As CLIs autenticadas continuam sendo subprocessos com permissões do usuário;
suas chamadas recebem um diretório temporário como diretório de trabalho ao
usar contexto. O OmniCLI não é um sandbox. Execute em ambiente isolado quando a codebase ou
as credenciais exigirem isolamento forte. Conteúdo nos comentários e arquivos
do projeto é tratado como dado não confiável dentro dos prompts.
