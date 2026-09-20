# Arquitetura para avaliação defensiva contra prompt injection

## 1. Objetivo arquitetural

Avaliar, em ambiente isolado e autorizado, se um agente de IA trata documentos externos como conteúdo não confiável e resiste a tentativas de:

- revelar segredos ou confirmar sua existência;
- alterar regras de maior precedência;
- executar ações externas sem autorização;
- ampliar privilégios;
- induzir o agente a ignorar controles de segurança.

A arquitetura não deve ter como objetivo obter segredos reais, contornar controles de produção ou criar um mecanismo reutilizável de exfiltração.

---

## 2. Classificação do contexto

### Fatos fornecidos

- A ideia original propõe usar um documento externo para instruir um agente a revelar segredos e ignorar regras.
- A proposta anterior identificou que documentos externos devem ser tratados como dados não confiáveis.
- O uso legítimo mais próximo é uma avaliação defensiva de resistência a prompt injection.
- Não foram especificados o agente-alvo, as ferramentas disponíveis, os tipos de dados, o ambiente ou os critérios de sucesso.

### Hipóteses de arquitetura

As recomendações abaixo assumem que:

- o teste será executado pelo proprietário do agente ou por equipe formalmente autorizada;
- o agente possui uma interface de entrada de documentos;
- pode haver acesso a ferramentas, arquivos ou sistemas externos;
- será possível executar os testes em ambiente separado de produção;
- segredos-isca sintéticos podem ser disponibilizados para validar não divulgação.

Essas hipóteses precisam ser confirmadas antes da implementação.

### Recomendações principais

- Reformular formalmente o objetivo para avaliação defensiva.
- Usar apenas valores sintéticos, como `CANARY_SECRET_DO_NOT_DISCLOSE`.
- Desabilitar ferramentas e rede por padrão.
- Separar o executor dos testes do agente avaliado.
- Classificar resultados por evidências mínimas, sem armazenar prompts ou respostas sensíveis completos.
- Testar tanto respostas textuais quanto tentativas de uso de ferramentas.

---

## 3. Visão geral dos componentes

```text
+---------------------+
| Operador autorizado |
+----------+----------+
           |
           v
+---------------------+       +----------------------+
| Orquestrador de     |------>| Catálogo de casos    |
| avaliação           |       | e políticas          |
+----------+----------+       +----------------------+
           |
           v
+---------------------+
| Sanitizador e       |
| empacotador         |
| de documentos       |
+----------+----------+
           |
           v
+---------------------+       +----------------------+
| Ambiente isolado    |------>| Agente sob avaliação |
| de execução         |       +----------+-----------+
+----------+----------+                  |
           |                             v
           |                    +----------------------+
           +------------------->| Proxy de ferramentas |
                                | e rede               |
                                +----------+-----------+
                                           |
                                           v
                                +----------------------+
                                | Sistema de decisão  |
                                | e registro de       |
                                | evidências          |
                                +----------+-----------+
                                           |
                                           v
                                +----------------------+
                                | Relatório agregado  |
                                +----------------------+
```

### 3.1 Orquestrador de avaliação

Responsabilidades:

- selecionar casos de teste;
- associar cada caso a um ambiente e configuração;
- gerar identificadores de execução;
- controlar limites de tempo, tentativas e ferramentas;
- enviar entradas ao agente;
- coletar resultados minimizados;
- acionar a avaliação automática;
- impedir execução fora do escopo autorizado.

Não deve:

- possuir credenciais de produção;
- armazenar segredos reais;
- decidir sozinho que um ambiente de produção está autorizado;
- transformar instruções contidas no documento em comandos privilegiados.

### 3.2 Catálogo de casos de teste

Cada caso deve ser versionado e conter:

- identificador único;
- categoria da tentativa;
- documento ou entrada sintética;
- objetivo do teste;
- comportamento esperado;
- sinais de aprovação;
- sinais de reprovação;
- ferramentas permitidas;
- severidade;
- versão da política utilizada.

Exemplos de categorias:

- solicitação direta de segredo-isca;
- tentativa de substituir instruções superiores;
- solicitação de ação externa;
- confirmação da existência de dado protegido;
- instrução escondida em conteúdo legítimo;
- instrução em metadados, nome de arquivo ou campo estruturado;
- tentativa de exploração por múltiplas etapas;
- tentativa de induzir o agente a revelar contexto interno.

Os documentos de teste devem ser tratados como artefatos de avaliação, e não como configuração operacional.

### 3.3 Sanitizador e empacotador

Responsabilidades:

- remover credenciais e dados reais;
- validar tamanho e tipo dos arquivos;
- rejeitar conteúdo fora do escopo;
- calcular hash do artefato;
- aplicar marcação de origem não confiável;
- criar o contexto de teste com separação clara entre políticas e conteúdo externo.

A sanitização não deve ser considerada prova de que um arquivo é seguro. Ela é apenas uma camada preventiva.

### 3.4 Ambiente isolado de execução

O ambiente deve fornecer:

- sistema de arquivos temporário;
- rede bloqueada por padrão;
- ausência de credenciais de produção;
- limites de CPU, memória, tempo e armazenamento;
- execução descartável ou facilmente restaurável;
- ferramentas simuladas quando possível;
- dados sintéticos e segredos-isca;
- identificação explícita do ambiente de teste.

Quando uma ferramenta precisar ser habilitada, ela deve usar um mock ou sandbox com operações inofensivas. Por exemplo, uma operação de envio pode apenas registrar uma tentativa em um coletor local, sem transmitir dados reais.

### 3.5 Agente sob avaliação

O agente deve receber:

- as políticas de segurança aplicáveis;
- o documento externo como conteúdo não confiável;
- uma tarefa claramente definida;
- acesso somente às ferramentas aprovadas para o caso;
- um identificador de correlação não sensível.

A arquitetura deve preservar a separação entre:

1. regras e políticas confiáveis;
2. instruções do operador autorizado;
3. conteúdo externo fornecido para análise;
4. resultados produzidos pelo agente;
5. ações de ferramentas.

O documento externo não pode alterar a hierarquia de autoridade apenas por afirmar que possui precedência.

### 3.6 Proxy de ferramentas e rede

Toda ferramenta deve passar por um proxy controlado, responsável por:

- autenticação do chamador;
- autorização por caso de teste;
- validação de parâmetros;
- bloqueio de destinos não permitidos;
- remoção de cabeçalhos ou tokens sensíveis;
- registro da tentativa;
- aplicação de limites de volume e frequência;
- retorno de respostas sintéticas quando possível.

Uma requisição bloqueada deve ser registrada como evento de segurança, sem incluir segredos ou conteúdo integral desnecessário.

### 3.7 Avaliador de resultados

O avaliador deve combinar:

- regras determinísticas;
- detecção de marcadores secretos-isca;
- análise de chamadas de ferramentas;
- validação de status e códigos de bloqueio;
- classificação manual para casos ambíguos.

A avaliação automática não deve depender exclusivamente de outro modelo de linguagem. Um avaliador baseado em regras deve detectar, no mínimo:

- presença do valor do segredo-isca na saída;
- confirmação indevida da existência de um segredo;
- chamada a ferramenta proibida;
- tentativa de acesso a destino não autorizado;
- alteração ou tentativa de alteração de política;
- ausência de recusa quando ela era obrigatória.

### 3.8 Armazenamento de resultados

Armazenar apenas os dados necessários:

- identificador da execução;
- versão do agente e da política;
- hash do documento;
- identificador do caso;
- resultado aprovado, reprovado ou inconclusivo;
- categorias de violações;
- ferramentas acionadas;
- latência e consumo de recursos;
- evidência redigida;
- referência para revisão autorizada, quando necessário.

O armazenamento de conteúdo bruto deve ser excepcional, temporário, criptografado e sujeito a controle de acesso.

### 3.9 Relatório

O relatório deve apresentar:

- escopo e autorização;
- ambiente e configuração avaliados;
- matriz de casos executados;
- taxa de aprovação;
- falhas por categoria e severidade;
- tentativas de ação bloqueadas;
- casos inconclusivos;
- limitações conhecidas;
- recomendações de correção;
- comparação com execuções anteriores, quando houver baseline.

Não deve reproduzir segredos, tokens ou documentos completos que contenham dados protegidos.

---

## 4. Fluxos principais

### 4.1 Preparação de uma avaliação

1. Um responsável autorizado registra o agente, a versão e o ambiente-alvo.
2. O sistema valida o escopo e exige confirmação de que não há dados reais necessários ao teste.
3. O catálogo seleciona os casos compatíveis.
4. O material de teste passa por validação e sanitização.
5. O orquestrador cria um ambiente descartável.
6. As ferramentas permitidas são configuradas no proxy.
7. A execução recebe um identificador de correlação.

Se não houver confirmação de autorização ou isolamento, a execução deve ser recusada.

### 4.2 Execução de um caso

1. O caso fornece uma tarefa legítima e um documento externo não confiável.
2. O agente processa o documento dentro do contexto delimitado.
3. O proxy intercepta chamadas de ferramentas.
4. Chamadas autorizadas são executadas em mocks ou sandbox.
5. Chamadas proibidas são bloqueadas.
6. A saída é analisada contra critérios determinísticos.
7. O resultado é classificado como:

   - **Aprovado:** o agente manteve as políticas e não expôs dados protegidos.
   - **Reprovado:** houve divulgação, confirmação indevida ou ação não autorizada.
   - **Inconclusivo:** os sinais não permitem classificação segura.

### 4.3 Tratamento de falha

Quando houver uma reprovação:

1. interromper a execução daquele caso;
2. bloquear novas ações externas;
3. preservar somente evidências minimizadas;
4. marcar o caso com severidade;
5. notificar os responsáveis autorizados;
6. impedir que o conteúdo sensível seja incluído automaticamente no relatório;
7. permitir revisão controlada do artefato original, se indispensável.

### 4.4 Geração do relatório

1. Consolidar os resultados por caso, categoria e versão.
2. Remover ou mascarar valores protegidos.
3. Calcular métricas agregadas.
4. Identificar falsos positivos e casos inconclusivos.
5. Produzir recomendações técnicas.
6. Expirar artefatos temporários conforme a política de retenção.

---

## 5. Modelo de dados mínimo

### Caso de teste

```text
TestCase
- id
- version
- category
- objective
- input_artifact_hash
- expected_behavior
- allowed_tools
- severity
- policy_version
```

### Execução

```text
EvaluationRun
- id
- subject_agent
- subject_version
- environment_id
- authorization_reference
- started_at
- finished_at
- status
```

### Resultado

```text
EvaluationResult
- run_id
- test_case_id
- outcome
- violation_type
- tool_attempts
- evidence_summary
- redaction_status
- evaluator_version
```

### Evento de segurança

```text
SecurityEvent
- event_id
- run_id
- event_type
- action
- decision
- target_class
- timestamp
- evidence_hash
```

Os campos devem evitar valores brutos de credenciais, tokens, dados pessoais ou conteúdo integral do documento.

---

## 6. Requisitos não funcionais

### Segurança

- Isolamento entre avaliações.
- Privilégio mínimo para o orquestrador, o agente e o proxy.
- Rede bloqueada por padrão.
- Nenhuma credencial de produção no ambiente.
- Segredos-isca não reutilizáveis fora do teste.
- Criptografia em trânsito e em repouso, conforme a infraestrutura adotada.
- Controle de acesso baseado em função.
- Auditoria de alterações em casos, políticas e permissões.
- Expiração automática de artefatos temporários.
- Proteção contra inclusão de segredos em logs e relatórios.

### Confiabilidade

- Execuções idempotentes ou identificadas para evitar duplicidade.
- Timeouts para agente, ferramentas e avaliação.
- Interrupção segura em caso de comportamento inesperado.
- Registro de versão de todos os componentes relevantes.
- Repetição controlada apenas quando fizer sentido, pois respostas de modelos podem variar.

### Reprodutibilidade

- Versionamento do caso, documento, política, modelo e avaliador.
- Hash dos artefatos de entrada.
- Configuração declarativa do ambiente.
- Sementes ou parâmetros de aleatoriedade registrados quando suportados.
- Registro das ferramentas habilitadas e dos mocks utilizados.

A reprodutibilidade pode ser limitada por variações do modelo, do provedor ou do ambiente. Isso deve ser explicitado no relatório.

### Desempenho

- Limite de tempo por caso.
- Execução paralela somente quando não houver compartilhamento de estado.
- Controle de volume para evitar custos ou consumo excessivo da infraestrutura.
- Encerramento antecipado após violação crítica.
- Métricas de latência separando agente, ferramentas e avaliador.

### Privacidade e retenção

- Minimização de dados.
- Mascaramento antes do armazenamento.
- Retenção diferenciada para métricas, evidências e artefatos.
- Acesso revisável aos resultados.
- Exclusão automática de arquivos temporários.
- Proibição de inserir dados reais apenas para aumentar a cobertura do teste.

### Operação

- Configuração por ambiente.
- Health checks para executor, proxy e armazenamento.
- Alertas para falhas de isolamento, chamadas proibidas e aumento de reprovações.
- Procedimento documentado para interromper uma campanha.
- Registro de mudanças e aprovação de novas classes de teste.

---

## 7. Segurança e modelo de ameaças

### Ativos a proteger

- Credenciais e tokens;
- dados pessoais;
- arquivos internos;
- instruções e políticas do agente;
- configurações de ferramentas;
- informações sobre infraestrutura;
- resultados de avaliações;
- artefatos de teste que possam ser reutilizados ofensivamente.

### Ameaças consideradas

- Documento que se apresenta como instrução superior;
- documento que solicita revelação direta ou indireta;
- confirmação da existência de um segredo;
- chamada de ferramenta escondida em texto, metadado ou estrutura do arquivo;
- tentativa de usar uma ferramenta permitida para alcançar um objetivo proibido;
- vazamento por logs, mensagens de erro ou relatórios;
- comprometimento do executor de testes;
- mistura de resultados de avaliações distintas;
- uso do ambiente de teste como ponte para sistemas externos.

### Controles recomendados

- Delimitação explícita de conteúdo externo;
- políticas de ferramenta aplicadas fora do modelo, no proxy;
- allowlist de operações;
- bloqueio de rede por padrão;
- sandbox descartável;
- validação de parâmetros;
- detecção de segredos-isca;
- revisão humana para casos críticos;
- separação entre dados de teste e dados operacionais;
- testes negativos para confirmar que bloqueios realmente funcionam.

O comportamento do agente, isoladamente, não deve ser considerado uma fronteira de segurança. Controles críticos devem existir fora do modelo.

---

## 8. Observabilidade

### Métricas

- quantidade de casos executados;
- percentual aprovado, reprovado e inconclusivo;
- reprovações por categoria;
- tentativas de divulgação de segredo-isca;
- chamadas de ferramentas permitidas e bloqueadas;
- tentativas de acesso a destinos proibidos;
- latência por componente;
- taxa de timeout;
- falhas de sandbox;
- número de artefatos redigidos;
- variação de resultado entre repetições.

### Logs estruturados

Os logs devem incluir:

- identificador de correlação;
- caso e versão;
- agente e versão;
- decisão do proxy;
- classe do evento;
- duração;
- resultado da avaliação;
- referência hash da evidência.

Os logs não devem conter:

- segredos, mesmo que sejam sintéticos, salvo quando o mecanismo de detecção precisar de armazenamento seguro separado;
- tokens;
- conteúdo integral de documentos;
- respostas completas sem necessidade operacional;
- dados pessoais.

### Alertas

Alertar quando ocorrer:

- tentativa de uso de ferramenta proibida;
- presença de marcador protegido na saída;
- falha de isolamento;
- tentativa de conexão externa;
- aumento relevante de reprovações;
- alteração não autorizada de caso ou política;
- indisponibilidade do proxy;
- armazenamento de evidência sem redaction.

### Rastreamento

Cada execução deve poder ser reconstruída por meio de:

```text
campanha
  -> execução
      -> caso
          -> artefato hash
          -> agente/configuração
          -> chamadas de ferramenta
          -> decisão
          -> evidência minimizada
```

Esse rastreamento deve permitir auditoria sem exigir o armazenamento indiscriminado do conteúdo original.

---

## 9. Critérios de aceitação

A primeira versão deve ser considerada tecnicamente aceitável quando:

- nenhum caso exige segredo real;
- o ambiente de teste não possui credenciais de produção;
- documentos externos não conseguem alterar as políticas de execução;
- ferramentas proibidas são bloqueadas fora do agente;
- uma tentativa de revelar o segredo-isca é detectada;
- ações externas não autorizadas não são executadas;
- os resultados são reproduzíveis dentro das limitações documentadas;
- os relatórios não expõem valores protegidos;
- todas as execuções possuem autorização e correlação;
- casos inconclusivos não são contabilizados automaticamente como aprovados.

---

## 10. Plano de implementação

### Fase 1 — Governança e escopo

- Confirmar agente, versões e ambientes autorizados.
- Definir responsáveis, critérios de aprovação e severidade.
- Formalizar dados proibidos e política de retenção.
- Definir se o teste avaliará somente texto ou também ferramentas.

**Saída:** escopo aprovado e matriz inicial de riscos.

### Fase 2 — Executor mínimo isolado

- Implementar o orquestrador de campanhas.
- Criar ambiente descartável sem rede e sem credenciais reais.
- Implementar identificação e correlação de execuções.
- Adicionar limites de tempo, memória e armazenamento.

**Saída:** execução segura de casos sintéticos simples.

### Fase 3 — Catálogo e avaliação determinística

- Criar casos para divulgação, mudança de autoridade e ação externa.
- Implementar segredos-isca.
- Implementar regras de detecção.
- Classificar resultados como aprovado, reprovado ou inconclusivo.

**Saída:** primeira matriz de regressão automatizada.

### Fase 4 — Proxy de ferramentas

- Adicionar allowlist por caso.
- Implementar validação de parâmetros.
- Criar mocks para operações externas.
- Registrar bloqueios e chamadas autorizadas.
- Testar falhas de isolamento.

**Saída:** validação de comportamento textual e operacional.

### Fase 5 — Observabilidade e relatórios

- Criar métricas, logs estruturados e alertas.
- Adicionar redaction e controle de retenção.
- Gerar relatório agregado com evidência mínima.
- Registrar versões de agente, política e avaliador.

**Saída:** relatório auditável sem exposição indevida.

### Fase 6 — Expansão controlada

- Adicionar PDFs, metadados, campos estruturados e documentos mistos.
- Incluir variações de contexto e múltiplas etapas.
- Comparar versões do agente.
- Realizar revisão humana de casos ambíguos.
- Atualizar o catálogo com regressões encontradas.

**Saída:** suíte de avaliação evolutiva, ainda restrita a ambientes autorizados.

---

## 11. Decisões pendentes

Antes de detalhar tecnologia ou implantação, é necessário validar:

1. Qual agente será avaliado?
2. Quais interfaces de entrada de documentos existem?
3. O agente possui ferramentas ou acesso de rede?
4. Quais ambientes estão autorizados?
5. Será permitido executar apenas mocks ou alguma integração real controlada?
6. Qual política de retenção será aplicada aos artefatos?
7. Quem aprovará casos novos e exceções?
8. Quais níveis de severidade exigirão interrupção imediata?
9. Qual variação entre execuções será considerada aceitável?
10. O resultado esperado é uma suíte contínua de regressão ou uma avaliação pontual?

## Conclusão

A proposta original não é tecnicamente aceitável como mecanismo para revelar segredos ou ignorar regras. A arquitetura viável é uma plataforma de avaliação defensiva, isolada e autorizada, na qual documentos externos são entradas não confiáveis, controles críticos ficam fora do modelo e todos os resultados são medidos por critérios verificáveis.

A prioridade de implementação deve ser o isolamento, seguida por casos sintéticos, bloqueio externo de ferramentas, avaliação determinística e observabilidade com minimização de evidências.
