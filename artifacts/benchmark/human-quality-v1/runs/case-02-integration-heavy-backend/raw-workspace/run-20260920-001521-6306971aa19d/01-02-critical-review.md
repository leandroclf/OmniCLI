# Revisão crítica da proposta

## 1. Fatos disponíveis

- A proposta é: “Projetar uma API que integra pagamentos, antifraude, CRM e notificações”.
- Os quatro domínios foram citados, mas não foram definidos:
  - se serão construídos ou apenas integrados;
  - quais provedores serão utilizados;
  - qual é o usuário da API;
  - qual problema prioritário será resolvido;
  - quais volumes, requisitos de disponibilidade e restrições regulatórias existem.
- A saída anterior reconhece corretamente a falta de requisitos, mas já sugere uma arquitetura orientada a eventos como direção preferencial.

## 2. Premissas frágeis

### “Uma API” é necessariamente a melhor fronteira

A proposta presume que pagamentos, antifraude, CRM e notificações devem ser expostos ou coordenados por uma única API. Isso pode criar uma fronteira artificial entre domínios com responsabilidades diferentes.

Riscos:

- acoplamento entre mudanças de pagamentos e CRM;
- contratos excessivamente genéricos para atender casos incompatíveis;
- dificuldade de definir propriedade dos dados;
- aumento do impacto de falhas em componentes não essenciais;
- API transformada em um ponto central difícil de evoluir.

Correção sugerida: validar primeiro se o produto é uma API única, uma fachada de integração, um conjunto de APIs por domínio ou uma plataforma interna de orquestração. A decisão deve partir dos consumidores e do fluxo operacional, não dos quatro sistemas mencionados.

### “Integrar” pode significar quatro produtos diferentes

Há uma diferença substancial entre:

1. encaminhar chamadas para provedores externos;
2. normalizar dados de vários provedores;
3. orquestrar um fluxo de negócio;
4. implementar pagamentos, antifraude, CRM e notificações próprios.

A proposta não permite determinar o escopo real. Se a interpretação for a quarta, o escopo é provavelmente incompatível com um primeiro incremento. Se for a primeira ou segunda, o principal desafio será a variabilidade dos provedores e dos contratos.

Correção sugerida: exigir uma matriz explícita para cada domínio:

| Domínio | Capacidade própria? | Provedor externo? | Responsável pelo dado | Operações mínimas |
|---|---|---|---|---|
| Pagamentos | A confirmar | A confirmar | A confirmar | A definir |
| Antifraude | A confirmar | A confirmar | A confirmar | A definir |
| CRM | A confirmar | A confirmar | A confirmar | A definir |
| Notificações | A confirmar | A confirmar | A confirmar | A definir |

### O pagamento é tratado implicitamente como evento central

A saída anterior recomenda considerar o pagamento como evento que dispara antifraude, CRM e notificações. Isso pode estar errado dependendo do processo:

- a análise antifraude pode precisar ocorrer antes da autorização;
- o CRM pode ser a origem do cliente, e não apenas um consumidor do pagamento;
- notificações podem depender de confirmação, liquidação, falha ou revisão manual;
- diferentes meios de pagamento podem ter estados e tempos de confirmação distintos.

Correção sugerida: mapear o ciclo de vida real da transação antes de escolher a ordem dos sistemas. Não assumir que o fluxo é linear nem que “pagamento aprovado” é o evento principal.

## 3. Contradições e lacunas relevantes

### Síncrono versus assíncrono não é uma escolha global

A pergunta anterior sobre comunicação síncrona ou orientada a eventos apresenta uma falsa alternativa. Uma solução real provavelmente terá ambos:

- resposta síncrona para aceitar a solicitação;
- processamento assíncrono para análise, confirmação, sincronização e notificações;
- webhooks ou consulta de status para conclusão posterior.

O ponto decisivo não é escolher um único estilo, mas definir quais estados precisam ser conhecidos imediatamente e quais podem ser eventualizados.

É necessário especificar:

- quando uma transação é considerada aceita;
- quando é considerada autorizada, capturada, liquidada, recusada ou em revisão;
- quem pode alterar cada estado;
- como atrasos, duplicidades e eventos fora de ordem serão tratados.

### Idempotência foi citada, mas não operacionalizada

Pagamentos, webhooks e notificações podem ser repetidos por clientes ou provedores. Não basta mencionar idempotência como requisito genérico.

É preciso decidir:

- qual chave será usada;
- por quanto tempo uma requisição repetida será reconhecida;
- se a mesma chave com payload diferente será rejeitada;
- como serão tratadas duplicidades de eventos externos;
- se operações como captura e estorno terão proteção própria.

Sem isso, há risco de cobrança duplicada, múltiplos estornos ou notificações repetidas.

### O modelo de dados está indefinido

“Cliente”, “pedido”, “transação”, “risco”, “evento” e “notificação” podem possuir identificadores e estados diferentes em cada provedor. Uma API de integração precisa definir o que é canônico e o que é apenas dado de origem.

Decisões necessárias:

- identificador interno versus identificador do provedor;
- sistema mestre de cada atributo;
- retenção de dados;
- tratamento de divergência entre CRM e pagamentos;
- versionamento de eventos e contratos;
- estratégia para dados parciais ou indisponíveis.

### Compliance não pode ser apenas uma observação genérica

A saída anterior menciona PCI-DSS, LGPD e possivelmente Bacen, mas sem saber se são aplicáveis ao caso. Isso é um alerta válido, porém ainda pouco acionável.

A validação humana deve determinar:

- se a solução tocará em dados de cartão ou usará tokenização externa;
- quais categorias de dados pessoais serão processadas;
- papéis de controlador, operador ou equivalentes aplicáveis ao contexto;
- requisitos de retenção, exclusão, auditoria e acesso;
- regiões de processamento e armazenamento;
- necessidade de avaliação jurídica e de segurança.

Não se deve transformar a simples menção a esses temas em requisito confirmado nem concluir conformidade apenas pela arquitetura.

## 4. Riscos de escopo

O maior risco é iniciar pelo desenho de endpoints antes de definir o núcleo de valor. Os quatro domínios podem gerar quatro linhas de produto:

- processamento de pagamentos;
- decisão ou consulta antifraude;
- sincronização de relacionamento com clientes;
- entrega confiável de comunicações.

Tentar cobrir todos no primeiro escopo pode resultar em contratos superficiais e nenhuma capacidade realmente robusta.

Um recorte inicial mais verificável poderia ser:

- um único fluxo de pagamento;
- um único provedor de pagamento;
- antifraude como decisão integrada, sem construir motor próprio;
- uma integração de CRM;
- um canal de notificação;
- consulta de status, idempotência e tratamento de falhas.

Esse recorte é uma recomendação, não uma decisão, e só é adequado se confirmar que o valor principal está no fluxo de pagamento integrado.

## 5. Dependências que precisam ser explicitadas

Antes de implementar, devem ser identificados:

- provedores e seus contratos, limites, webhooks e ambientes de teste;
- posse e qualidade dos dados de clientes e transações;
- disponibilidade de credenciais e permissões;
- requisitos de segurança e gestão de segredos;
- necessidade de conciliação financeira;
- processo para revisão manual de fraude;
- destino e política de reenvio de notificações;
- observabilidade, auditoria e suporte operacional;
- estratégia para indisponibilidade ou alteração de cada provedor;
- ambiente de homologação representativo.

A integração com terceiros não deve ser tratada como detalhe de implementação: seus limites, semântica de estados e mecanismos de retry podem definir o contrato da própria API.

## 6. Decisões que exigem validação humana

1. A API será interna, pública para clientes ou white-label?
2. O objetivo principal é reduzir esforço de integração, aumentar aprovação, reduzir fraude, centralizar dados ou automatizar comunicação?
3. A solução construirá capacidades próprias ou apenas adaptará provedores?
4. Qual domínio será o núcleo do produto?
5. Qual é o primeiro fluxo de negócio obrigatório, do início ao fim?
6. Qual sistema será a fonte de verdade para cada entidade?
7. Quais estados exigem resposta imediata?
8. Quais operações são financeiramente irreversíveis e exigem controles adicionais?
9. Quais dados sensíveis serão recebidos, armazenados ou apenas encaminhados?
10. Quais níveis de disponibilidade, latência, rastreabilidade e suporte são necessários?
11. Quais integrações e canais fazem parte do primeiro release?
12. Quem aprova decisões de segurança, privacidade, risco e operação?

## 7. Recomendações objetivas

- Substituir o objetivo amplo por uma frase mensurável, por exemplo: reduzir o tempo de integração de um novo meio de pagamento em determinado contexto.
- Escolher um fluxo vertical mínimo antes de definir uma API abrangente.
- Documentar, para cada domínio, o que é capacidade própria e o que é integração externa.
- Modelar explicitamente estados, transições, responsáveis e eventos fora de ordem.
- Definir idempotência, retries, timeouts, compensações e reconciliação como parte do contrato.
- Separar o modelo canônico interno dos payloads específicos dos provedores.
- Evitar que CRM e notificações bloqueiem o resultado financeiro quando não forem essenciais à transação.
- Não adotar arquitetura orientada a eventos como decisão antecipada; usar eventos onde houver processamento posterior, integração desacoplada ou necessidade de reprocessamento.
- Confirmar requisitos de segurança, privacidade e operação com responsáveis humanos antes de escolher persistência, logs e retenção.
- Adiar integrações adicionais até que o primeiro fluxo prove valor e tenha critérios de sucesso definidos.

## 8. Conclusão crítica

A ideia identifica uma possível oportunidade de centralização, mas ainda não define um produto implementável. O principal problema não é escolher endpoints ou tecnologia: é determinar se existe um único problema que conecte os quatro domínios e qual deles deve comandar o primeiro fluxo.

A recomendação de uma camada de orquestração de eventos pode ser válida, mas neste momento é prematura. A próxima etapa deve validar o problema, o público, o fluxo prioritário, a responsabilidade sobre os dados e o limite entre integração e construção de produto. Sem essas decisões, qualquer desenho arquitetural corre risco de formalizar um escopo excessivo e uma fronteira de API inadequada.
