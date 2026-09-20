# Arquitetura proposta para processamento de documentos de saúde

## 1. Resumo executivo

A arquitetura recomendada para o primeiro ciclo é um serviço de processamento documental assíncrono, com escopo limitado a um tipo de documento e sem tomada automática de decisão clínica.

O serviço deverá:

1. receber um documento enviado por um sistema ou usuário autorizado;
2. validar formato, tamanho e metadados;
3. armazenar o original de forma segura;
4. executar OCR e, quando aplicável, extração de campos previamente definidos;
5. indicar campos ausentes, ilegíveis ou de baixa confiança;
6. encaminhar resultados incertos para revisão humana;
7. publicar somente resultados aprovados;
8. disponibilizar o resultado por API e/ou evento para o sistema de origem;
9. manter auditoria completa do processamento e das alterações.

A arquitetura deve tratar documentos, texto extraído e dados estruturados como dados de saúde sensíveis. A solução não deve inferir a identidade do paciente apenas pelo conteúdo do documento.

---

## 2. Fatos, hipóteses e recomendações

### Fatos fornecidos

O único requisito confirmado é:

> Criar um serviço que processe documentos de saúde de pacientes.

Também está confirmado, pelo contexto anterior, que ainda não foram definidos:

- tipo de documento;
- usuário ou organização consumidora;
- finalidade do processamento;
- campos a serem extraídos;
- volume;
- prazo de resposta;
- jurisdição;
- integração com sistemas existentes;
- uso clínico ou administrativo do resultado.

### Hipóteses arquiteturais

Para produzir uma arquitetura implementável, são adotadas as seguintes hipóteses:

- o serviço receberá PDFs e imagens;
- o processamento poderá demorar mais que uma requisição HTTP convencional;
- documentos poderão conter dados pessoais e clínicos;
- o resultado precisará ser auditável;
- determinados campos poderão exigir revisão humana;
- o serviço será usado inicialmente como apoio documental, e não como mecanismo autônomo de decisão clínica;
- o sistema de origem poderá fornecer um identificador externo do paciente, sem que o processador precise ser a fonte mestre da identidade.

Essas hipóteses devem ser confirmadas antes do desenho definitivo de contratos, capacidade e controles de conformidade.

### Recomendações

Recomenda-se que o MVP suporte somente:

- um tipo de documento;
- um conjunto pequeno de campos;
- um fluxo assíncrono;
- revisão humana para resultados de baixa confiança;
- nenhuma publicação automática em prontuário ou sistema clínico sem regra explícita de aprovação;
- uma única forma de integração inicial, preferencialmente API.

OCR genérico, múltiplos tipos documentais, interpretação clínica, interoperabilidade ampla e integrações com vários sistemas devem ser adicionados somente após validação do caso inicial.

---

## 3. Escopo funcional inicial

### Entrada

O serviço deverá aceitar:

- arquivo PDF, PNG, JPEG ou outro formato explicitamente aprovado;
- identificador do documento no sistema de origem;
- identificador externo do paciente, quando necessário;
- tipo documental declarado pelo sistema de origem;
- contexto da solicitação;
- identificador de correlação da operação.

O identificador do paciente deve ser recebido de uma fonte autorizada. O serviço não deve considerar o nome ou outro dado textual extraído do documento como prova suficiente de identidade.

### Saída

O resultado poderá conter:

- texto extraído;
- metadados do documento;
- campos estruturados suportados pelo tipo documental;
- confiança por campo;
- indicação de campos ausentes ou ilegíveis;
- versão do processador;
- status do processamento;
- histórico de revisão;
- referências ao documento original e às versões derivadas.

O resultado deve indicar claramente a diferença entre:

- conteúdo transcrito;
- campo extraído;
- dado normalizado;
- valor corrigido por um revisor;
- interpretação clínica.

A primeira versão deve limitar-se à transcrição, organização e extração de campos definidos. Interpretação clínica deve permanecer fora do escopo inicial.

---

## 4. Visão lógica da arquitetura

```text
Sistema consumidor
        |
        | 1. Solicita processamento
        v
API de ingestão
        |
        | 2. Valida autorização e metadados
        v
Orquestrador de processamento
        |
        +--> Armazenamento do original
        |
        +--> Fila de processamento
                    |
                    v
             Worker documental
                    |
                    +--> OCR
                    |
                    +--> Classificação limitada
                    |
                    +--> Extração de campos
                    |
                    +--> Validação de confiança
                    |
                    v
             Resultado estruturado
                    |
          +---------+---------+
          |                   |
          v                   v
   Revisão humana       Publicação controlada
                              |
                              v
                    API ou evento de resultado
```

### Componentes

#### 4.1 API de ingestão

Responsabilidades:

- autenticar o chamador;
- autorizar a organização e o contexto de acesso;
- validar tamanho, formato e metadados;
- gerar ou aceitar um identificador de idempotência;
- registrar o documento;
- armazenar o conteúdo;
- criar a solicitação de processamento;
- retornar um identificador de acompanhamento.

A API não deve executar OCR ou extração pesada durante a requisição de upload.

#### 4.2 Armazenamento de objetos

Deve armazenar:

- documento original;
- imagens derivadas, quando necessárias;
- texto extraído;
- resultado estruturado;
- evidências de processamento;
- versões revisadas.

Características recomendadas:

- criptografia em repouso;
- acesso privado;
- URLs temporárias quando houver download direto;
- versionamento ou mecanismo equivalente;
- política de retenção por tipo de artefato;
- separação lógica por organização ou tenant.

O conteúdo clínico não deve ser colocado em nomes de arquivos, tags públicas ou metadados desnecessários.

#### 4.3 Banco de metadados

Deve armazenar o estado operacional, e não necessariamente o binário do documento.

Entidades sugeridas:

- `tenant` ou organização;
- `document`;
- `processing_request`;
- `processing_attempt`;
- `extracted_field`;
- `review`;
- `publication`;
- `audit_event`;
- `retention_policy`.

O banco deve manter referências ao armazenamento de objetos, hashes, status, timestamps e versões.

#### 4.4 Fila de processamento

A fila desacopla a API dos workers e permite:

- retentativas;
- controle de concorrência;
- isolamento de falhas;
- processamento em lote;
- escalabilidade independente;
- encaminhamento de mensagens inválidas para uma fila de erro.

Cada mensagem deve conter somente os identificadores necessários para localizar o documento e a solicitação. O conteúdo clínico completo não deve ser replicado na mensagem sem necessidade.

#### 4.5 Worker documental

Responsabilidades:

1. recuperar o documento autorizado;
2. verificar integridade e tipo real do arquivo;
3. preparar o conteúdo para processamento;
4. executar OCR;
5. aplicar regras específicas do tipo documental;
6. extrair campos;
7. atribuir confiança e evidências;
8. validar obrigatoriedades;
9. persistir o resultado;
10. decidir entre aprovação automática permitida, revisão humana ou falha.

O worker deve ser idempotente. A repetição de uma mensagem não pode criar múltiplos resultados publicados ou múltiplos eventos inconsistentes.

#### 4.6 Serviço de revisão humana

Responsabilidades:

- exibir documento e resultado lado a lado;
- destacar campos de baixa confiança;
- permitir correção controlada;
- exigir identificação do revisor;
- registrar valor anterior, valor novo, motivo e horário;
- impedir alteração fora da permissão do revisor;
- finalizar o resultado com status explícito.

A revisão humana não deve sobrescrever silenciosamente o resultado automático.

#### 4.7 Serviço de publicação

Responsabilidades:

- publicar somente resultados em estado permitido;
- impedir publicação duplicada;
- enviar o resultado para o sistema consumidor;
- registrar resposta, falha e retentativa;
- preservar a versão publicada;
- impedir que alterações posteriores modifiquem retroativamente o que foi entregue sem novo evento.

---

## 5. Estados do documento

Um fluxo mínimo pode ser modelado da seguinte forma:

```text
RECEBIDO
   |
   v
VALIDADO
   |
   v
PROCESSANDO
   |
   +--> FALHA_TÉCNICA
   |
   +--> REQUER_REVISÃO
   |          |
   |          v
   |       EM_REVISÃO
   |          |
   |          v
   +------ APROVADO
              |
              v
          PUBLICADO
```

Estados adicionais recomendados:

- `REJEITADO`: arquivo inválido, incompatível ou fora do escopo;
- `CANCELADO`: cancelamento autorizado antes da publicação;
- `EXPIRADO`: retenção encerrada;
- `RETIDO_POR_INCIDENTE`: preservação temporária para investigação autorizada.

As transições devem ser explícitas e auditáveis. Não se deve permitir a publicação de documentos em `PROCESSANDO`, `REQUER_REVISÃO`, `FALHA_TÉCNICA` ou `REJEITADO`.

---

## 6. Fluxos principais

### 6.1 Ingestão

1. O sistema consumidor solicita uma operação autenticada.
2. A API valida o chamador e sua organização.
3. O arquivo é validado por extensão, MIME real, tamanho e conteúdo.
4. O serviço calcula um hash do arquivo.
5. O original é armazenado em área privada.
6. A solicitação recebe status `RECEBIDO` ou `VALIDADO`.
7. Uma mensagem idempotente é publicada na fila.
8. A API responde com o identificador da solicitação.

A resposta inicial deve informar que a solicitação foi aceita, não que o documento foi processado com sucesso.

### 6.2 Processamento

1. O worker obtém a mensagem.
2. Verifica se a solicitação já foi concluída.
3. Recupera o documento pelo identificador interno.
4. Executa OCR e extração.
5. Valida campos e confiança.
6. Persiste o resultado com sua versão do processador.
7. Define o próximo estado.
8. Emite evento operacional.
9. Confirma a mensagem somente após a persistência necessária.

### 6.3 Revisão humana

1. O resultado é marcado como `REQUER_REVISÃO`.
2. O revisor autorizado acessa o documento.
3. O sistema mostra os valores extraídos e as evidências.
4. O revisor corrige ou confirma campos.
5. O sistema registra o histórico completo.
6. O revisor aprova ou rejeita o resultado.
7. O documento segue para publicação, se aplicável.

### 6.4 Consulta de status

A API deve permitir consultar:

- status atual;
- timestamps;
- motivo de rejeição ou falha;
- versão do resultado;
- necessidade de revisão;
- resultado publicado;
- identificadores de correlação.

Mensagens de erro destinadas ao consumidor não devem revelar dados clínicos desnecessários.

### 6.5 Publicação

A publicação deve ser baseada em uma chave idempotente composta, por exemplo, por:

- organização;
- documento;
- versão do resultado;
- destino.

O consumidor deve conseguir distinguir:

- resultado automático;
- resultado revisado;
- resultado corrigido posteriormente;
- falha de publicação.

---

## 7. Modelo de dados conceitual

### Documento

- identificador interno;
- identificador externo;
- organização proprietária;
- identificador externo do paciente, quando aplicável;
- tipo documental;
- hash do conteúdo;
- localização do original;
- tamanho;
- formato;
- status;
- data de retenção;
- timestamps.

### Solicitação de processamento

- identificador da solicitação;
- documento associado;
- versão do pipeline;
- prioridade;
- status;
- número de tentativas;
- erro técnico categorizado;
- identificador de idempotência;
- timestamps.

### Campo extraído

- nome do campo;
- valor bruto;
- valor normalizado, se houver;
- unidade, quando aplicável;
- localização ou evidência no documento;
- confiança;
- origem: `automático`, `revisado` ou `corrigido`;
- versão;
- status de validação.

### Revisão

- identificador da revisão;
- revisor;
- campos alterados;
- valor anterior;
- valor posterior;
- motivo;
- timestamp;
- versão revisada;
- decisão final.

### Auditoria

- ator;
- tipo de ator;
- ação;
- recurso afetado;
- organização;
- resultado da ação;
- identificador de correlação;
- timestamp;
- metadados técnicos mínimos.

O log de auditoria deve registrar a ação sem duplicar o conteúdo clínico completo.

---

## 8. Integrações

### Integração inicial recomendada

A primeira integração deve ser uma API autenticada para:

- enviar documento;
- consultar status;
- obter resultado aprovado;
- cancelar solicitação quando permitido;
- baixar o original ou resultado por acesso temporário;
- receber notificações opcionais.

### Integrações futuras

Podem ser avaliadas posteriormente:

- sistemas de prontuário eletrônico;
- repositórios documentais;
- sistemas de laboratório;
- filas corporativas;
- formatos de interoperabilidade;
- notificações por webhook;
- exportação para análise operacional.

Essas integrações não devem ser assumidas como disponíveis. Cada uma exigirá contrato, autenticação, tratamento de indisponibilidade, versionamento, idempotência e definição de responsabilidade sobre erros.

### Provedores externos de OCR ou IA

O uso de um provedor externo depende de validação específica sobre:

- localização e transferência dos dados;
- retenção pelo provedor;
- uso para treinamento;
- segregação entre clientes;
- criptografia;
- subcontratados;
- contrato e responsabilidades;
- disponibilidade;
- comportamento em caso de indisponibilidade;
- possibilidade de processamento local ou alternativa.

Até essa validação, a arquitetura deve encapsular OCR e extração atrás de interfaces internas, sem acoplar o domínio a um fornecedor específico.

---

## 9. Requisitos não funcionais

Os valores abaixo são metas iniciais recomendadas, não requisitos confirmados.

### Segurança e privacidade

- autenticação forte para usuários e sistemas;
- autorização por organização, função e recurso;
- segregação de tenants;
- criptografia em trânsito e em repouso;
- gestão centralizada de chaves e segredos;
- proibição de dados clínicos em logs comuns;
- auditoria de acesso e alteração;
- expiração de acessos temporários;
- validação contra arquivos maliciosos;
- proteção contra upload abusivo;
- exclusão e retenção controladas;
- backup protegido e com política de expiração;
- revisão de permissões periodicamente.

### Confiabilidade

- processamento idempotente;
- retentativas com limite;
- fila de mensagens inválidas;
- recuperação após reinício de worker;
- persistência do estado antes da confirmação da mensagem;
- prevenção de publicação duplicada;
- mecanismo para reprocessamento controlado;
- isolamento entre falhas de OCR, banco, armazenamento e publicação.

### Desempenho

Devem ser definidos após medição, mas o desenho deve suportar:

- upload separado do processamento;
- documentos grandes sem bloquear a API;
- concorrência controlada;
- limites de páginas e tamanho;
- escalabilidade horizontal dos workers;
- priorização opcional de solicitações;
- backpressure quando a fila crescer.

### Disponibilidade

A disponibilidade da API e do processamento deve ser medida separadamente. Um sistema pode aceitar solicitações mesmo quando o processamento estiver temporariamente degradado, desde que:

- a solicitação seja preservada;
- o usuário receba status transparente;
- exista limite para acúmulo;
- haja estratégia de recuperação.

### Qualidade da extração

A qualidade deve ser acompanhada por tipo de campo, e não apenas por uma média global.

Métricas recomendadas:

- precisão e revocação por campo;
- taxa de campos ausentes;
- taxa de revisão humana;
- taxa de correção por revisor;
- erro de associação documental;
- taxa de documentos rejeitados;
- desempenho por qualidade de imagem;
- desempenho por layout e versão do documento.

Nenhum limiar de confiança deve ser considerado suficiente para uso clínico sem validação do caso de uso.

---

## 10. Segurança e controle de acesso

### Princípio de menor privilégio

Perfis sugeridos:

- `integrador`: envia e consulta documentos de sua organização;
- `revisor`: acessa documentos atribuídos e corrige resultados;
- `auditor`: consulta trilhas de auditoria sem editar resultados;
- `operador`: acompanha falhas técnicas sem acesso ao conteúdo clínico, quando possível;
- `administrador`: gerencia configuração com acesso excepcional e auditado.

O acesso deve ser limitado por organização, unidade, caso de uso e estado do documento, conforme necessário.

### Proteção do upload

O serviço deve:

- limitar tamanho e quantidade de páginas;
- verificar o tipo real do arquivo;
- rejeitar formatos não suportados;
- detectar conteúdo malicioso;
- remover ou neutralizar conteúdo ativo quando aplicável;
- impedir processamento de arquivos compactados abusivos;
- usar nomes internos não previsíveis;
- não confiar em extensões fornecidas pelo usuário.

### Proteção contra exposição

Não devem aparecer em:

- logs de aplicação;
- métricas;
- traces;
- mensagens de erro;
- URLs permanentes;
- nomes de filas;
- nomes de arquivos;
- tickets automáticos;

dados como nome completo, documento de identidade, diagnóstico ou texto integral do laudo, salvo necessidade operacional devidamente justificada.

### Privacidade

Antes da implementação, devem ser definidos:

- finalidade do tratamento;
- papéis das organizações;
- base jurídica aplicável;
- política de retenção;
- critérios de anonimização ou descarte;
- uso de subcontratados;
- fluxo de atendimento a incidentes;
- tratamento de solicitações de titulares, quando aplicável;
- proibição ou autorização explícita de uso dos dados para treinamento.

Essas decisões exigem participação jurídica, de privacidade e de segurança. A arquitetura não presume obrigações legais específicas sem a jurisdição e o contexto contratual.

---

## 11. Observabilidade

### Logs

Os logs devem ser estruturados e conter:

- timestamp;
- serviço;
- ambiente;
- nível;
- identificador de correlação;
- identificador da solicitação;
- identificador técnico do documento;
- etapa do pipeline;
- resultado;
- duração;
- categoria do erro.

Não devem conter texto clínico bruto ou valores sensíveis completos.

### Métricas

Métricas técnicas:

- solicitações recebidas;
- documentos por status;
- tamanho da fila;
- idade da mensagem mais antiga;
- tempo de processamento;
- taxa de erro por etapa;
- retentativas;
- mensagens em fila de erro;
- falhas de armazenamento;
- falhas de publicação;
- taxa de indisponibilidade.

Métricas de produto e qualidade:

- documentos por tipo;
- taxa de revisão;
- campos corrigidos;
- confiança média por campo;
- documentos rejeitados;
- tempo até aprovação;
- taxa de resultados publicados;
- reprocessamentos;
- divergência entre resultado automático e revisado.

### Traces

O rastreamento distribuído deve conectar:

```text
requisição de ingestão
  -> persistência
  -> publicação na fila
  -> execução do worker
  -> OCR
  -> extração
  -> revisão
  -> publicação
```

Os traces devem usar apenas identificadores técnicos e não carregar o documento ou o texto extraído como atributos.

### Alertas

Alertas prioritários:

- crescimento sustentado da fila;
- aumento de falhas de OCR;
- crescimento da fila de erro;
- publicação duplicada ou rejeitada;
- acesso negado acima do padrão;
- falhas de autenticação anormais;
- aumento de documentos presos em estado intermediário;
- falhas de retenção ou descarte;
- indisponibilidade do armazenamento;
- queda anormal na qualidade da extração.

---

## 12. Decisões arquiteturais registradas

### ADR-001 — Processamento assíncrono

**Decisão:** usar processamento assíncrono para OCR e extração.

**Motivo:** o tempo de processamento pode variar com tamanho, qualidade e tipo do documento. O desacoplamento reduz o risco de timeouts e permite retentativas.

**Trade-off:** o consumidor precisa acompanhar status ou receber notificação posterior.

**Alternativa rejeitada para o MVP:** processamento completo dentro da requisição de upload.

### ADR-002 — Armazenar o original separadamente dos metadados

**Decisão:** usar armazenamento de objetos para o conteúdo e banco para estado e metadados.

**Motivo:** documentos podem ser grandes e possuem ciclo de vida diferente do estado operacional.

**Trade-off:** exige consistência entre armazenamento e banco, além de limpeza de artefatos órfãos.

### ADR-003 — Revisão humana para baixa confiança

**Decisão:** resultados incertos não devem ser publicados automaticamente.

**Motivo:** erros em documentos de saúde podem ser silenciosos e difíceis de detectar.

**Trade-off:** maior custo operacional e tempo de conclusão.

### ADR-004 — Não usar inferência textual como identificação do paciente

**Decisão:** a associação ao paciente deve vir de um identificador autorizado do sistema de origem.

**Motivo:** nomes e outros dados extraídos podem estar ausentes, ilegíveis ou pertencer a outra pessoa.

**Trade-off:** integrações consumidoras precisam fornecer contexto de identidade confiável.

### ADR-005 — Encapsular OCR e extração

**Decisão:** provedores de OCR ou IA devem ser acessados por uma camada de abstração interna.

**Motivo:** preserva a possibilidade de substituição, fallback ou processamento alternativo.

**Trade-off:** adiciona uma interface interna e algum código de adaptação.

---

## 13. Plano de implementação

### Fase 0 — Fechamento de requisitos

Definir e aprovar:

- primeiro tipo documental;
- usuário e sistema consumidor;
- campos extraídos;
- finalidade do resultado;
- necessidade de revisão;
- volume esperado;
- limite de tamanho e páginas;
- prazo aceitável;
- política de retenção;
- jurisdição e requisitos de privacidade;
- uso ou não de provedores externos;
- critério de sucesso.

Sem essa definição, a equipe deve limitar-se a um protótipo técnico, não a um produto clínico operacional.

### Fase 1 — Vertical slice controlado

Implementar:

- autenticação básica;
- ingestão;
- armazenamento privado;
- registro de metadados;
- fila;
- worker;
- OCR ou extrator escolhido para avaliação;
- consulta de status;
- persistência de resultado;
- auditoria mínima;
- limites e validações de upload.

O resultado deve ser testado com documentos autorizados, anonimizados ou sintéticos.

### Fase 2 — Revisão e qualidade

Adicionar:

- interface ou fluxo de revisão;
- confiança por campo;
- evidência do trecho extraído;
- histórico de alterações;
- métricas de precisão;
- estados completos do documento;
- reprocessamento controlado;
- fila de erro;
- controles de publicação.

### Fase 3 — Integração operacional

Adicionar uma integração real somente após validação do fluxo interno:

- contrato de resultado;
- autenticação entre sistemas;
- idempotência;
- notificações;
- tratamento de indisponibilidade;
- reconciliação;
- monitoramento ponta a ponta.

### Fase 4 — Endurecimento de produção

Validar:

- testes de carga;
- testes de segurança;
- recuperação de backup;
- expiração e descarte;
- segregação entre organizações;
- rotação de segredos;
- auditoria;
- resposta a incidentes;
- limites operacionais;
- runbooks;
- revisão de permissões;
- validação formal dos critérios de qualidade.

---

## 14. Critérios de aceitação do MVP

O MVP pode ser considerado tecnicamente pronto quando:

- aceita somente os formatos e limites documentados;
- rejeita arquivos inválidos de forma segura;
- processa uma solicitação sem depender de sessão HTTP aberta;
- suporta repetição sem duplicar resultado;
- preserva o documento original e suas versões;
- informa status observável ao consumidor;
- diferencia resultado automático de resultado revisado;
- bloqueia publicação de resultados que requerem revisão;
- registra acesso, alteração e publicação;
- não expõe dados clínicos em logs comuns;
- possui retentativas e fila de erro;
- permite descartar dados conforme política aprovada;
- apresenta métricas de processamento e qualidade;
- mede a extração contra uma referência conhecida;
- não é apresentado como mecanismo autônomo de decisão clínica.

---

## 15. Riscos remanescentes

Os principais riscos que continuam dependentes de decisão de negócio ou validação especializada são:

- escopo excessivamente amplo de tipos documentais;
- qualidade insuficiente dos documentos de entrada;
- erro de associação ao paciente;
- uso indevido de resultados automáticos;
- dependência de provedor externo de OCR ou IA;
- retenção excessiva de cópias;
- ausência de dados representativos para avaliação;
- integração com sistema clínico sem contrato de responsabilidade;
- requisitos regulatórios específicos da jurisdição;
- custo e capacidade em escala.

A arquitetura proposta é tecnicamente viável para um serviço de processamento documental assistivo. Ela não deve ser interpretada como autorização para automatizar diagnóstico, prescrição, triagem ou outras decisões clínicas sem uma avaliação adicional de segurança, qualidade, responsabilidade e conformidade.
