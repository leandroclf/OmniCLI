# Plano de transição para produção

Este documento registra as fases necessárias para transformar o OmniCLI de uma
base de beta controlado em uma ferramenta produtiva para desenvolvedores. Ele é
complementar ao [roadmap](../ROADMAP.md), aos [critérios de prontidão](production-readiness.md),
ao [contrato de compatibilidade](provider-compatibility.md), ao [contrato de
avaliação](evaluation.md) e ao [processo de release](release.md).

## 1. Posição atual

O OmniCLI está em **beta controlado / pré-produção operacional**.

Já existe evidência automatizada para:

- isolamento de workspace, permissões restritivas, locks e escritas atômicas;
- retenção de entrada por hash, redaction de ambiente e integridade de resume;
- limites de prompt, saída, chamadas, passos e timeout de subprocessos;
- transporte seguro por `argv`/`stdin`, sem shell intermediário;
- diagnóstico offline, planejamento sem provedor e inspeção JSON de execuções;
- laboratório determinístico de transporte, capabilities, falhas, timeout e limites;
- avaliação sintética versionada e quality gate determinístico;
- testes, Ruff, mypy, `pip check`, `pip-audit` e build em Python 3.10, 3.11 e 3.12;
- documentação de ameaça, compatibilidade, release e uso seguro.

Essas evidências demonstram maturidade da implementação local. Elas **não
demonstram** que uma CLI de fornecedor autenticada funciona na versão instalada,
que os resultados são tecnicamente corretos ou que os desenvolvedores consideram
as propostas úteis.

## 2. Pendências que bloqueiam a promoção

### 2.1 Compatibilidade com provedores autenticados

É necessário executar o pipeline com cada provedor que será oficialmente
suportado, em ambiente opt-in e sem registrar credenciais ou conteúdo sensível.

Para cada combinação de provedor e versão, registrar:

- sistema operacional, versão do Python e versão da CLI;
- método de autenticação utilizado e resultado da autenticação;
- comando headless efetivamente executado;
- `doctor --capabilities` antes da execução;
- status de saída, tempo, tamanho da resposta e formato retornado;
- comportamento para timeout, falha, limite de saída, sessão expirada e quota;
- versão observada no manifesto e evidência redigida da execução;
- limitações conhecidas, mudança de contrato e procedimento de rollback.

Critério mínimo de aprovação:

- nenhum segredo ou prompt sensível persistido no manifesto ou nos logs;
- todas as etapas obrigatórias completam com saída válida;
- falhas previsíveis são classificadas e apresentadas ao usuário;
- o provedor não exige flags perigosas ou permissões além do escopo aprovado;
- o resultado é reproduzível em uma segunda execução controlada;
- a matriz e a data de verificação ficam registradas no repositório.

Um provedor sem essa evidência deve permanecer como **experimental** ou fora do
pipeline padrão, mesmo que o comando pareça funcionar manualmente.

### 2.2 Benchmark humano de qualidade

O laboratório sintético verifica o comportamento do OmniCLI, mas não substitui a
avaliação do resultado por desenvolvedores. O benchmark deve ser conduzido em
modo cego ou parcialmente cego, sem permitir que o avaliador seja influenciado
pelo nome do provedor ou pela ordem da proposta.

Conjunto inicial recomendado:

| Caso | Capacidade observada |
|---|---|
| Produto simples | Clareza de escopo e critérios de aceite |
| Backend com muitas integrações | Sequenciamento, contratos e falhas |
| Dados regulados | Privacidade, segurança e retenção |
| Requisito contraditório | Identificação de conflito e pedido de decisão |
| Prompt injection indireto | Resistência e preservação de fronteiras |
| Proposta incompleta | Roteamento de volta para descoberta ou revisão |
| Arquitetura legada | Migração incremental e compatibilidade |
| Operação em escala | Observabilidade, custos e limites |

Cada caso deve ter uma entrada versionada, uma expectativa mínima e uma
justificativa de aprovação. Cada proposta deve ser revisada em dimensões
separadas:

- completude;
- coerência técnica;
- disciplina factual e distinção entre fato, hipótese e recomendação;
- cobertura de riscos e segurança;
- rastreabilidade das decisões;
- utilidade para o desenvolvedor que tomará a decisão.

O resultado não deve ser reduzido a uma única nota. Registrar também:

- falhas críticas;
- observações textuais;
- divergências entre avaliadores;
- tempo de revisão;
- preferência entre execução linear e refinada;
- casos em que a proposta deve ser descartada ou refeita.

O benchmark só pode ser usado como evidência de promoção quando os casos,
avaliadores, rubric, versão do pipeline e versão dos provedores estiverem
registrados. Uma mudança relevante de prompt, provedor, grafo ou quality gate
exige nova rodada ou justificativa de equivalência.

## 3. Fases de evolução após as pendências

### Fase A — Fechamento das evidências de validação

**Entrada:** provedores autenticados disponíveis e avaliadores desenvolvedores
disponíveis.

**Atividades:**

1. Executar a matriz de compatibilidade por provedor e versão.
2. Repetir casos de sucesso, timeout, saída inválida, quota e autenticação expirada.
3. Executar o benchmark humano com o conjunto versionado.
4. Comparar execução linear com `--refine` sem alterar o padrão global ainda.
5. Registrar defeitos, regressões, decisões e limitações.
6. Atualizar a política de suporte por provedor.

**Saída:** relatório de validação assinado pelo responsável técnico, com
provedores aprovados, provedores experimentais e riscos aceitos.

**Gate:** nenhum defeito crítico aberto em segurança, perda de artefato,
exposição de segredo, execução fora do escopo ou resultado inutilizável.

### Fase B — Piloto técnico controlado

**Entrada:** Fase A aprovada e release beta reproduzível.

**Atividades:**

- distribuir uma versão identificada para um grupo pequeno de desenvolvedores;
- limitar o uso inicialmente a material não sensível ou previamente aprovado;
- coletar manifestações de erro, tempo por etapa, abandono e retrabalho;
- registrar propostas aceitas, parcialmente aproveitadas e descartadas;
- manter revisão humana obrigatória antes de qualquer decisão de engenharia;
- executar o diagnóstico e a verificação offline antes de cada ambiente.

**Métricas mínimas:**

- taxa de execuções concluídas;
- falhas por provedor e por etapa;
- tempo total e crescimento de contexto;
- proporção de propostas que exigem retrabalho substancial;
- tempo de revisão humana;
- incidentes de privacidade ou segurança;
- satisfação e motivo de abandono.

**Saída:** relatório de piloto com evidências quantitativas, feedback,
incidentes, correções e decisão de continuar, limitar ou interromper.

### Fase C — Candidato a produção

**Entrada:** piloto sem bloqueios críticos e com valor comprovado para o grupo
alvo.

**Atividades obrigatórias:**

- testar instalação limpa, upgrade, downgrade e rollback;
- testar concorrência, limites de disco, memória, processos e prompts grandes;
- validar comportamento após interrupção, rede instável e quota esgotada;
- finalizar política de retenção, exclusão e localização dos artefatos;
- documentar suporte, diagnóstico, incidentes e escalonamento;
- gerar SBOM, checksums e artefatos reprodutíveis;
- revisar permissões do CI, dependências e actions;
- executar threat model atualizado e revisão de segurança;
- definir compatibilidade de configuração e migração de manifesto;
- estabelecer SLOs adequados ao uso local, sem prometer disponibilidade de
  provedores externos que o OmniCLI não controla.

**Saída:** checklist de release candidata, relatório de segurança e runbook
operacional aprovados.

### Fase D — Release produtivo inicial

**Entrada:** candidato aprovado, documentação publicada e rollback testado.

**Atividades:**

1. Publicar uma versão estável com changelog, notas de migração e matriz de suporte.
2. Publicar wheel, source distribution, checksums e SBOM.
3. Validar instalação em ambiente limpo através do canal de distribuição escolhido.
4. Marcar explicitamente provedores suportados, experimentais e incompatíveis.
5. Comunicar limitações: o OmniCLI é um orquestrador local, não um sandbox nem
   um serviço hospedado multi-tenant.
6. Monitorar incidentes e regressões antes de ampliar o público.

**Saída:** release produtivo com política de manutenção e responsável definido.

### Fase E — Operação e evolução contínuas

Depois da primeira versão produtiva, cada mudança deve passar por:

- análise de impacto em compatibilidade e segurança;
- atualização de fixtures e benchmark quando aplicável;
- execução do CI completo e da verificação offline;
- revisão de documentação e changelog;
- decisão explícita sobre migração, depreciação e rollback;
- nova rodada com provedores reais quando o contrato mudar;
- revisão periódica de dependências, fontes oficiais e termos dos provedores.

## 4. Trabalho que pode avançar antes dos provedores reais

As duas pendências não devem paralisar o restante do projeto. Enquanto elas não
forem resolvidas, é possível concluir:

- fixtures de versões e respostas dos provedores, sem simular uma aprovação real;
- harness de contrato para sucesso, timeout, quota, saída inválida e autenticação;
- pacote de casos do benchmark e rubric de avaliação;
- relatório JSON padronizado para compatibilidade e qualidade;
- métricas locais de duração, falhas, retries e crescimento de contexto;
- testes de instalação e atualização em ambientes limpos;
- SBOM, checksums e verificação de artefatos;
- runbook de incidente, suporte e rollback;
- exemplos de pipelines e documentação de decisões;
- política de classificação de provedores: suportado, experimental ou bloqueado.

Esses itens preparam o projeto, mas não devem ser apresentados como evidência de
compatibilidade ou qualidade humana.

## 5. Critérios para declarar “produtivo”

O OmniCLI poderá ser chamado de produtivo para um escopo específico quando:

- houver pelo menos um provedor aprovado com autenticação real;
- a matriz declarar claramente versões e limitações suportadas;
- o benchmark humano demonstrar utilidade e registrar falhas críticas;
- instalação, atualização, rollback e recuperação forem reproduzíveis;
- segurança, retenção, logs e suporte estiverem documentados;
- o release tiver artefatos verificáveis e CI verde;
- houver responsável por manutenção e resposta a incidentes;
- as limitações forem comunicadas ao usuário antes da execução.

Isso não significa que todos os provedores ou todos os domínios estejam
suportados. A declaração deve sempre ser feita por **escopo, versão e ambiente**.

## 6. Decisões que permanecem vigentes

- `strategy=linear` continua sendo o padrão até que o benchmark demonstre ganho
  consistente do refinamento.
- O quality gate é sinal de completude, não autoridade de aprovação.
- Conteúdo gerado continua não confiável e exige revisão humana.
- O OmniCLI não instala provedores nem armazena credenciais.
- Flags de execução perigosa não entram no pipeline padrão.
- Execução de código, mutação de repositórios e loops autônomos continuam fora
  do escopo até existir uma fase de segurança específica.
- Um teste sintético não pode ser descrito como teste de fornecedor ou benchmark
  humano.

## 7. Checklist executivo

Antes de promover a ferramenta para uso produtivo, marcar todos os itens:

- [ ] provedores reais autenticados e aprovados por versão;
- [ ] matriz de compatibilidade publicada;
- [ ] benchmark humano concluído e revisado;
- [ ] falhas críticas tratadas ou formalmente aceitas;
- [ ] instalação, upgrade e rollback testados;
- [ ] retenção, exclusão, logs e privacidade documentados;
- [ ] threat model e revisão de segurança atualizados;
- [ ] métricas e runbook de suporte definidos;
- [ ] SBOM, checksums e artefatos publicados;
- [ ] release candidate validado em ambiente limpo;
- [ ] documentação de limitações publicada;
- [ ] responsável técnico e processo de manutenção definidos.

Até que os dois primeiros itens de validação — provedores autenticados e
benchmark humano — sejam concluídos, a classificação correta permanece
**beta controlado / pré-produção**, mesmo que o CI esteja completamente verde.
