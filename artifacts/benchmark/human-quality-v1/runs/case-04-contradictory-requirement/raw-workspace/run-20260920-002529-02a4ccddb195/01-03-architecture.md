# Arquitetura proposta

## 1. Resumo executivo

A combinação literal de consistência forte global, custo mínimo e disponibilidade offline total não pode ser garantida para todo estado mutável simultaneamente. Durante uma partição de rede, uma réplica offline não consegue confirmar se sua alteração é compatível com alterações realizadas em outras réplicas.

A arquitetura tecnicamente viável deve separar os dados por criticidade e aplicar garantias diferentes:

- dados críticos e globais: consistência forte, com escrita condicionada à conectividade;
- dados sincronizáveis: operação offline com versionamento, consistência eventual e resolução explícita de conflitos;
- dados locais e cache: disponibilidade offline ampla, sem compromisso de consistência global;
- operações dependentes de serviços externos: execução offline apenas quando houver capacidade local equivalente ou dados previamente preparados.

A recomendação é adotar um modelo híbrido, com prioridade operacional nesta ordem:

1. não perder dados confirmados;
2. preservar consistência forte para o subconjunto realmente crítico;
3. manter funcionamento offline para operações locais e sincronizáveis;
4. minimizar infraestrutura e complexidade dentro desses limites.

---

## 2. Fatos fornecidos

Os requisitos apresentados são:

- consistência forte global;
- custo mínimo;
- disponibilidade offline total.

Não foram especificados:

- tipos de dados mantidos pelo sistema;
- número de dispositivos ou usuários;
- quantidade de escritores concorrentes;
- necessidade de operação multi-região;
- definição formal de “offline total”;
- tolerância a rejeição, reversão ou merge de alterações;
- orçamento de infraestrutura e operação;
- requisitos de retenção, privacidade e auditoria.

Consequentemente, os componentes abaixo representam uma arquitetura de referência, sujeita à validação desses pontos.

---

## 3. Hipóteses arquiteturais

As seguintes hipóteses são usadas apenas para viabilizar o desenho:

- haverá um estado local em cada instalação ou dispositivo;
- parte dos dados poderá ser alterada offline;
- algumas alterações precisarão ser compartilhadas globalmente;
- poderão existir múltiplos escritores concorrentes;
- a reconexão poderá ocorrer de forma intermitente;
- o sistema deverá continuar funcionando localmente quando o serviço remoto estiver indisponível.

Se essas hipóteses não forem verdadeiras, a solução pode ser simplificada, especialmente removendo o mecanismo de sincronização ou restringindo o armazenamento local.

---

## 4. Modelo de dados e níveis de consistência

Cada entidade deve declarar explicitamente seu nível de consistência, sua política offline e sua política de conflito.

| Categoria | Exemplos genéricos | Leitura offline | Escrita offline | Garantia recomendada |
|---|---|---:|---:|---|
| Global crítica | identidade, permissões, revogações, políticas de segurança | Com cache e indicação de validade | Não, salvo concessão explícita | Consistência forte |
| Global sincronizável | configurações compartilhadas, preferências de equipe, metadados | Sim | Sim | Consistência eventual com conflitos |
| Local | preferências do dispositivo, histórico local, rascunhos | Sim | Sim | Consistência local |
| Cache ou derivada | índices, resultados materializados, dados temporários | Sim, se disponíveis | Não diretamente | Recalculável e descartável |
| Artefato independente | arquivos, pacotes, snapshots ou documentos | Sim, se armazenado localmente | Sim | Versionamento e integridade |

### 4.1 Dados críticos globais

Esses dados devem ter uma autoridade única ou um mecanismo de consenso com quorum. Quando o dispositivo estiver offline:

- leituras podem usar o último estado confirmado;
- o estado deve ser marcado como potencialmente desatualizado;
- alterações que exigem garantia global devem ser bloqueadas;
- operações previamente autorizadas podem ser permitidas somente se houver uma concessão formal, com escopo e validade limitados.

A disponibilidade offline, nesse caso, é limitada intencionalmente para preservar a consistência forte.

### 4.2 Dados sincronizáveis

Esses dados podem aceitar alterações offline. Cada alteração deve ser registrada como uma operação independente, contendo no mínimo:

- identificador único da operação;
- entidade e campo afetado;
- versão ou revisão observada;
- dispositivo ou instalação de origem;
- identidade do autor;
- instante lógico da operação;
- payload da alteração;
- dependências ou operações predecessoras;
- assinatura ou mecanismo de autenticação local;
- estado da sincronização.

A ordem baseada somente em relógio físico não deve ser usada como autoridade, pois relógios podem divergir. Deve-se utilizar versão de entidade, contador lógico, revisão do servidor ou outro mecanismo determinístico.

### 4.3 Dados locais

Podem ser mantidos em armazenamento local transacional. Não precisam participar da sincronização global, desde que:

- sejam claramente identificados como locais;
- não sejam utilizados para decidir políticas globais;
- tenham estratégia de backup ou exportação quando forem importantes;
- não sejam confundidos com o estado confirmado pelo servidor.

---

## 5. Componentes

### 5.1 Cliente ou agente local

Responsabilidades:

- disponibilizar a operação local;
- manter o estado materializado para uso offline;
- validar comandos antes da persistência;
- registrar alterações em um log local;
- expor o estado de conectividade e sincronização;
- indicar dados potencialmente obsoletos;
- impedir operações que exigem consistência forte quando não houver autorização válida.

O cliente não deve considerar que uma alteração local está globalmente confirmada apenas porque foi persistida com sucesso.

### 5.2 Armazenamento local

Requisitos:

- transações atômicas entre atualização de estado e registro da operação;
- controle de versões;
- recuperação após interrupção do processo;
- criptografia em repouso;
- limites de retenção para o log;
- verificação de integridade;
- exportação ou restauração quando aplicável.

O padrão recomendado é o chamado outbox local: a alteração e seu evento de sincronização são gravados na mesma transação local.

### 5.3 Motor de sincronização

Responsabilidades:

- detectar conectividade;
- enviar operações pendentes;
- reenviar operações de forma segura;
- aplicar confirmação, rejeição ou conflito;
- receber alterações remotas;
- atualizar o estado local;
- manter checkpoints de sincronização;
- limitar consumo de rede e bateria;
- retomar o processamento após falhas.

O motor deve ser idempotente. Repetir uma operação por timeout não pode gerar efeitos duplicados.

### 5.4 API de sincronização

A API deve suportar:

- autenticação e autorização;
- envio em lote;
- idempotência por identificador de operação;
- consulta de alterações desde uma revisão;
- confirmação individual ou em lote;
- resposta explícita para sucesso, rejeição, conflito e reprocessamento;
- paginação;
- compressão opcional;
- limitação de taxa;
- validação de esquema e tamanho.

Um resultado HTTP positivo não deve significar automaticamente que todos os dispositivos já receberam a alteração. A resposta deve distinguir:

- operação aceita e aplicada;
- operação aceita para processamento;
- operação rejeitada;
- operação conflitante;
- operação duplicada já processada.

### 5.5 Serviço de autoridade global

Responsável pelos dados que exigem consistência forte:

- validação de revisão;
- controle de concorrência otimista;
- aplicação serializada ou transacional;
- controle de permissões vigentes;
- geração de revisões globais;
- auditoria de mudanças;
- rejeição de alterações baseadas em estado obsoleto.

Esse serviço pode operar com uma única região inicialmente para reduzir custo, desde que a disponibilidade, o objetivo de recuperação e a tolerância a falhas sejam compatíveis com essa escolha. Multi-região ativa/ativa não deve ser presumida sem necessidade comprovada.

### 5.6 Serviço de resolução de conflitos

Deve classificar conflitos em níveis:

1. conflito automaticamente resolvível;
2. conflito resolvível por regra de domínio;
3. conflito que exige intervenção;
4. alteração inválida ou não autorizada.

Estratégias possíveis:

- merge por campo quando os campos forem independentes;
- merge por conjunto para operações aditivas;
- rejeição quando a alteração for incompatível;
- resolução por versão somente quando houver aceitação explícita de perda lógica;
- fila de conflitos para decisão posterior.

“Última escrita vence” só deve ser adotado quando a perda silenciosa de alterações for aceitável. Em dados críticos, essa estratégia é inadequada.

### 5.7 Serviço de reconciliação e recuperação

Responsável por:

- reprocessar operações rejeitadas temporariamente;
- detectar lacunas no log;
- reconstruir estado a partir de snapshot e operações;
- identificar operações presas;
- executar compensações quando uma aplicação parcial for possível;
- fornecer ferramentas de diagnóstico e intervenção.

### 5.8 Armazenamento central

Deve manter, conforme a necessidade:

- estado autoritativo;
- revisões;
- log de operações;
- conflitos;
- auditoria;
- snapshots;
- metadados de sincronização.

O armazenamento de operações e auditoria deve ter retenção e proteção contra alteração compatíveis com os requisitos de negócio e segurança. Essas exigências ainda precisam ser definidas.

---

## 6. Fluxos principais

### 6.1 Operação online em dado crítico

1. O cliente autentica a solicitação.
2. O cliente envia a alteração junto com a revisão observada.
3. A autoridade global valida identidade, permissão e revisão.
4. A alteração é aplicada em transação.
5. Uma nova revisão global é gerada.
6. O resultado confirmado é retornado ao cliente.
7. Os demais clientes recebem a alteração por sincronização ou consulta incremental.

Se a revisão local estiver obsoleta, a operação deve ser rejeitada com informação suficiente para atualização e nova tentativa segura.

### 6.2 Operação offline em dado sincronizável

1. O cliente valida a operação localmente.
2. Estado e operação pendente são persistidos atomicamente.
3. A interface informa que a alteração foi aplicada localmente, mas ainda não confirmada globalmente.
4. O motor de sincronização envia a operação quando houver conectividade.
5. O servidor aplica, rejeita ou marca a operação como conflitante.
6. O cliente atualiza o estado com base na resposta.
7. Se necessário, o conflito é resolvido automaticamente ou encaminhado para intervenção.

### 6.3 Reconexão

Ao recuperar a conectividade:

1. o cliente autentica novamente;
2. consulta a revisão remota conhecida;
3. envia operações pendentes em ordem segura;
4. recebe confirmações e conflitos;
5. baixa alterações remotas posteriores ao checkpoint;
6. aplica as alterações de forma transacional;
7. atualiza o checkpoint;
8. repete o processo até não haver lacunas ou pendências processáveis.

A sincronização deve sobreviver a interrupções em qualquer etapa sem duplicar ou perder operações.

### 6.4 Alteração concorrente

Exemplo de sequência:

1. dois dispositivos leem a revisão `R`;
2. ambos alteram a mesma entidade offline;
3. o primeiro envia sua operação e gera a revisão `R+1`;
4. o segundo envia uma operação baseada em `R`;
5. o servidor detecta que a base está obsoleta;
6. a operação é rejeitada ou encaminhada ao resolvedor;
7. o cliente recebe o novo estado e o resultado do conflito.

A arquitetura não deve ocultar esse caso. Conflitos são um estado normal do sistema offline-first.

### 6.5 Revogação de acesso durante o modo offline

A revogação central não pode ser conhecida instantaneamente por um dispositivo desconectado. Portanto:

- credenciais locais devem ter validade limitada;
- tokens ou concessões offline devem possuir escopo restrito;
- operações sensíveis devem exigir reconexão;
- o sistema deve registrar a última verificação de autorização;
- após reconexão, operações realizadas com autorização expirada devem ser reavaliadas;
- dados removidos ou revogados devem ser eliminados ou bloqueados localmente conforme a política definida.

“Offline total” não pode ser interpretado como garantia de autorização sempre atualizada.

---

## 7. Contratos de sincronização

Cada operação deve possuir um identificador globalmente único e ser processada de forma idempotente.

Exemplo conceitual de contrato:

```text
Operation {
  operation_id
  entity_type
  entity_id
  operation_type
  payload
  base_revision
  logical_timestamp
  actor_id
  device_id
  created_at
  authorization_context
}
```

A resposta deve diferenciar semanticamente:

```text
Applied       operação aplicada
AlreadyApplied operação já processada anteriormente
Pending       aceita, mas ainda não finalizada
Conflict      incompatível com o estado atual
Rejected      inválida, não autorizada ou não permitida
Retryable     falha temporária; pode ser reenviada
```

O contrato real deve ser definido conforme o domínio. Os nomes acima são ilustrativos, não uma integração existente.

---

## 8. Consistência, disponibilidade e custo

### 8.1 Consistência forte

Deve ser reservada para:

- regras de autorização;
- revogações;
- identidade;
- controle de recursos exclusivos;
- operações financeiras ou equivalentes, se existirem;
- mudanças cuja duplicação ou perda seja inaceitável.

Essas operações terão menor disponibilidade offline por definição.

### 8.2 Disponibilidade offline

Deve abranger:

- leitura de dados previamente sincronizados;
- execução de operações locais;
- alterações em dados locais;
- criação de alterações sincronizáveis;
- consulta ao estado da fila e dos conflitos.

Não deve prometer:

- confirmação global offline;
- autorização global atualizada;
- disponibilidade de serviços externos sem substituto local;
- ausência de conflitos;
- sincronização durante a desconexão.

### 8.3 Minimização de custo

A redução de custo deve ser tratada como otimização sujeita a limites de qualidade. Recomendações:

- iniciar com uma autoridade central simples;
- evitar multi-região ativa/ativa sem requisito comprovado;
- usar sincronização incremental;
- compactar ou agrupar operações;
- manter snapshots para reduzir reconstrução;
- limitar retenção do log conforme necessidades de auditoria;
- evitar replicar todos os dados em todos os dispositivos;
- usar armazenamento local proporcional ao escopo;
- medir tráfego, armazenamento, processamento e custo operacional.

O custo de desenvolvimento e suporte deve ser considerado junto com o custo de infraestrutura. Uma solução aparentemente barata pode se tornar cara se produzir muitos conflitos ou exigir intervenção manual frequente.

---

## 9. Requisitos não funcionais

Os valores abaixo devem ser confirmados em uma etapa de requisitos. São metas iniciais, não compromissos já aprovados.

### 9.1 Integridade e durabilidade

- nenhuma operação local confirmada deve desaparecer silenciosamente;
- persistência transacional entre estado e fila de sincronização;
- recuperação após desligamento abrupto;
- detecção de corrupção de armazenamento;
- snapshots e restauração testados;
- idempotência em todos os pontos de reenvio.

### 9.2 Disponibilidade

Separar metas por classe:

- dados locais: disponibilidade offline;
- dados sincronizáveis: disponibilidade local com sincronização posterior;
- dados críticos globais: disponibilidade condicionada à autoridade e à conectividade.

Não é recomendável definir um único percentual de disponibilidade para o sistema inteiro.

### 9.3 Latência

Medir separadamente:

- latência da operação local;
- latência da confirmação global;
- tempo até sincronização;
- tempo até resolução de conflito;
- tempo de recuperação após reconexão.

### 9.4 Escalabilidade

Avaliar:

- quantidade de dispositivos;
- operações por dispositivo;
- tamanho médio e máximo das operações;
- crescimento do log;
- taxa de conflitos;
- número de entidades compartilhadas;
- volume de sincronização após longos períodos offline.

### 9.5 Recuperação

Definir:

- RPO para dados locais e globais;
- RTO da autoridade central;
- comportamento durante corrupção parcial;
- restauração de um único dispositivo;
- restauração do estado global;
- reprocessamento após perda de conectividade prolongada.

Não é possível recomendar valores específicos sem conhecer a criticidade do produto.

### 9.6 Compatibilidade e evolução

- versionamento de esquema;
- compatibilidade entre clientes antigos e servidores novos;
- migrações locais;
- migração de operações pendentes;
- rejeição segura de versões incompatíveis;
- capacidade de desativar uma regra de conflito sem corromper o histórico.

---

## 10. Segurança

### 10.1 Identidade e autenticação

- autenticação central quando houver conectividade;
- credenciais locais protegidas pelo armazenamento seguro do sistema operacional;
- tokens de curta duração para operações sensíveis;
- concessões offline com escopo, limite temporal e permissões reduzidas;
- reautenticação após períodos configuráveis;
- bloqueio local após suspeita de comprometimento.

### 10.2 Autorização

A autorização deve ocorrer em duas camadas:

- validação local para usabilidade e feedback rápido;
- validação autoritativa no servidor para qualquer operação global ou sensível.

A validação local nunca deve ser tratada como prova de autorização global atualizada.

### 10.3 Proteção dos dados

- criptografia em trânsito;
- criptografia do banco local;
- proteção das chaves;
- minimização de dados replicados;
- separação de dados por usuário, organização ou instalação quando aplicável;
- remoção segura de dados revogados;
- prevenção de exposição em logs.

A permanência de dados sensíveis offline exige decisão explícita de privacidade e risco.

### 10.4 Integridade das operações

- identificadores não previsíveis;
- autenticação das mensagens;
- proteção contra replay;
- validação de origem e escopo;
- controle de versões;
- assinatura ou MAC quando o modelo de ameaça exigir;
- auditoria de rejeições, conflitos e alterações administrativas.

### 10.5 Modelo de ameaça mínimo

Devem ser analisados, pelo menos:

- dispositivo perdido ou roubado;
- cliente modificado;
- replay de operação;
- alteração de relógio local;
- duplicação de mensagens;
- armazenamento local copiado;
- usuário revogado enquanto offline;
- servidor comprometido;
- vazamento por logs ou mensagens de erro;
- conflito usado para sobrescrever dados válidos.

---

## 11. Observabilidade

A observabilidade deve distinguir falha de conectividade de falha de integridade ou de regra de negócio.

### 11.1 Métricas

Por dispositivo:

- operações locais criadas;
- operações pendentes;
- idade da operação mais antiga;
- tempo desde a última sincronização bem-sucedida;
- bytes enviados e recebidos;
- conflitos pendentes;
- rejeições;
- falhas de autenticação;
- tamanho do armazenamento local.

No serviço central:

- taxa de operações aplicadas;
- operações duplicadas;
- conflitos por tipo de entidade;
- rejeições por motivo;
- latência de aplicação;
- backlog de sincronização;
- falhas temporárias;
- falhas permanentes;
- crescimento do log;
- tempo de retenção;
- taxa de clientes com revisão obsoleta.

### 11.2 Logs estruturados

Todo evento de sincronização deve conter, quando possível:

- identificador de operação;
- identificador de correlação;
- dispositivo ou instalação;
- entidade sem expor conteúdo sensível;
- revisão de origem;
- revisão de destino;
- resultado;
- motivo de rejeição ou conflito;
- tentativa de processamento;
- timestamp do servidor.

Dados sensíveis não devem ser gravados diretamente no log.

### 11.3 Rastreamento

O fluxo de uma operação deve ser rastreável entre:

```text
alteração local → fila local → envio → autoridade → resposta → aplicação local
```

O identificador de operação deve permanecer estável durante reenvios.

### 11.4 Alertas

Alertas recomendados:

- crescimento anormal do backlog;
- operações pendentes acima do limite de idade;
- aumento súbito de conflitos;
- repetição excessiva de uma operação;
- falha de atualização de checkpoint;
- divergência entre snapshots e log;
- queda de autenticação;
- armazenamento local próximo do limite;
- aumento de clientes com estado obsoleto.

---

## 12. Estratégia de testes

A arquitetura exige testes além do caminho feliz:

- dois dispositivos alterando a mesma entidade;
- perda de conexão durante envio;
- timeout após o servidor aplicar a operação;
- reenvio da mesma operação;
- desligamento durante gravação local;
- corrupção ou indisponibilidade do armazenamento local;
- reconexão após longo período offline;
- cliente antigo com servidor novo;
- revogação de acesso durante desconexão;
- mensagens fora de ordem;
- duplicação de mensagens;
- relógio local incorreto;
- conflito não resolvível;
- restauração a partir de snapshot;
- falha parcial durante aplicação em lote;
- esgotamento de armazenamento;
- alteração remota enquanto o dispositivo está offline.

Critérios de sucesso devem medir integridade, não apenas ausência de erros: nenhuma operação deve desaparecer silenciosamente, e todo conflito deve ter resultado observável.

---

## 13. Plano de implementação

### Fase 1 — Definição do domínio

Entregáveis:

- inventário de entidades;
- classificação de cada entidade por consistência;
- operações permitidas offline;
- política de conflito por entidade;
- requisitos de retenção e privacidade;
- definição de autorização offline;
- metas de disponibilidade e recuperação.

Sem essa classificação, a implementação corre o risco de aplicar uma garantia uniforme e inadequada.

### Fase 2 — Núcleo local

Implementar:

- armazenamento local transacional;
- controle de versões;
- outbox;
- identificadores de operação;
- recuperação após interrupção;
- estado explícito de sincronização;
- indicação de dados não confirmados globalmente.

Validar primeiro com dados locais e sincronizáveis simples.

### Fase 3 — API e autoridade central

Implementar:

- autenticação;
- autorização;
- idempotência;
- aplicação transacional;
- revisões;
- consulta incremental;
- respostas de conflito e rejeição;
- auditoria.

A autoridade deve ser testada independentemente do cliente.

### Fase 4 — Sincronização bidirecional

Implementar:

- envio de pendências;
- download incremental;
- checkpoints;
- retry com backoff;
- retomada após falha;
- ordenação e dependências;
- controle de lote;
- limites de tamanho e taxa.

### Fase 5 — Conflitos e operações críticas

Adicionar:

- regras determinísticas de merge;
- fila de conflitos;
- intervenção manual quando necessário;
- bloqueio offline para dados críticos;
- concessões offline, somente se justificadas;
- fluxos de revogação e expiração.

### Fase 6 — Segurança e observabilidade

Adicionar:

- criptografia local;
- proteção de credenciais;
- logs estruturados;
- métricas;
- rastreamento;
- alertas;
- auditoria;
- testes de ameaça e recuperação.

### Fase 7 — Piloto controlado

Executar com:

- pequeno conjunto de usuários ou dispositivos;
- dados não críticos inicialmente;
- métricas de conflito e atraso;
- simulação de desconexões;
- avaliação do custo real;
- validação da experiência de recuperação de conflitos.

A expansão para dados críticos deve depender dos resultados do piloto, especialmente da taxa de conflitos e da capacidade de suporte.

---

## 14. Decisões que precisam ser confirmadas

Antes da implementação definitiva, é necessário decidir:

1. Quais entidades exigem consistência forte?
2. Quais entidades podem aceitar conflitos?
3. É aceitável rejeitar ou reverter uma alteração offline?
4. O modo offline precisa permitir apenas leitura ou também escrita?
5. Qual o período máximo de operação sem sincronização?
6. Quais dados podem permanecer armazenados localmente?
7. Qual o comportamento quando uma autorização expira offline?
8. Qual o atraso máximo aceitável para sincronização?
9. Qual o RPO e o RTO do estado global?
10. Qual métrica representa “custo mínimo”?
11. Existe necessidade comprovada de multi-região?
12. Qual percentual de conflitos pode ser resolvido automaticamente?

---

## 15. Recomendação final

Adotar inicialmente uma arquitetura híbrida offline-first:

- estado local transacional;
- outbox de operações;
- sincronização incremental idempotente;
- consistência eventual para dados sincronizáveis;
- conflitos explícitos e auditáveis;
- autoridade central para dados críticos;
- bloqueio offline de operações que exigem confirmação global;
- observabilidade desde o primeiro protótipo;
- implantação inicial simples, com uma autoridade central, evitando complexidade multi-região até que exista requisito comprovado.

Essa abordagem preserva a disponibilidade offline onde ela é tecnicamente possível, mantém consistência forte onde ela é realmente necessária e reduz custo ao evitar replicação e coordenação global indiscriminadas. A expressão “disponibilidade offline total” deve ser substituída por uma matriz de capacidades por tipo de dado e operação, pois somente essa formulação é testável e operacionalmente segura.
