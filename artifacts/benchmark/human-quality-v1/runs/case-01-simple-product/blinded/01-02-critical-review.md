# Revisão Crítica da Proposta

## Fatos fornecidos

- O produto seria um aplicativo de lista de tarefas.
- O aplicativo seria local.
- O público seria uma equipe pequena.

Não foram fornecidos quantidade de usuários, forma de colaboração, ambiente de execução, prazo, restrições técnicas ou motivo para evitar soluções existentes.

## Hipóteses presentes na exploração anterior

A exploração anterior levantou, de forma razoável, três interpretações para “local”:

- aplicativo isolado em cada computador;
- aplicativo compartilhado na rede local;
- sistema self-hosted, sem depender de SaaS externo.

Também presumiu que a equipe talvez precise de tarefas compartilhadas, atribuição, status, prazos e permissões. Essas funcionalidades são plausíveis, mas ainda não são requisitos.

## Pontos críticos

### 1. “Local” continua sendo a decisão bloqueadora

A proposta não pode avançar para arquitetura ou backlog enquanto “local” não for definido. Um aplicativo desktop individual não resolve colaboração; um sistema em LAN exige armazenamento compartilhado, concorrência, backup e operação; um sistema self-hosted exige manutenção e disponibilidade.

A recomendação anterior identifica essa ambiguidade, mas ainda trata as três opções com peso semelhante. É necessário escolher uma interpretação principal ou declarar explicitamente que o primeiro produto será apenas single-user.

### 2. “Equipe pequena” não é uma especificação suficiente

O tamanho da equipe influencia diretamente a solução. Duas ou três pessoas em uma mesma máquina têm necessidades muito diferentes de uma equipe distribuída em vários computadores.

É preciso validar pelo menos:

- número atual e máximo esperado de usuários;
- se todos usam a mesma rede;
- se haverá acesso simultâneo;
- se existe alguém responsável por instalar, atualizar e fazer backup.

Sem essas respostas, não é possível justificar requisitos como autenticação, permissões ou sincronização em tempo real.

### 3. Há risco de transformar uma lista simples em um clone de ferramenta de gestão

A lista de funcionalidades candidatas já inclui atribuição, status, comentários, histórico, prazos, notificações, projetos, quadros e permissões. Somadas, essas opções podem produzir um sistema comparável a Trello, Asana ou Jira, contrariando implicitamente a ideia de um aplicativo simples para uma equipe pequena.

O escopo inicial deveria ser reduzido a:

- criar e editar tarefas;
- concluir ou reabrir tarefas;
- atribuir uma tarefa, caso colaboração seja confirmada;
- filtrar por responsável e status;
- persistir e exportar os dados.

Comentários, histórico detalhado, notificações, múltiplos projetos e permissões devem ficar fora do MVP, salvo necessidade comprovada.

### 4. A motivação foi corretamente tratada como hipótese, mas está recebendo atenção excessiva

Privacidade, custo, aprendizado e insatisfação com uma ferramenta existente são explicações possíveis, não fatos. A exploração anterior dedica espaço significativo a essas alternativas sem evidência de que sejam relevantes.

A pergunta mais útil não é apenas “por que construir?”, mas:

> Qual problema concreto a equipe enfrenta hoje e qual resultado tornaria o aplicativo útil?

Se uma ferramenta existente já atende ao problema, construir e manter uma aplicação local pode aumentar o custo operacional sem benefício claro.

### 5. “Sem internet” e “sem terceiros” não são equivalentes

A proposta pode estar misturando dois objetivos diferentes:

- funcionar sem conexão com a internet;
- manter os dados sob controle da equipe.

Um sistema self-hosted pode depender de uma rede interna e ainda exigir administração. Um aplicativo desktop pode funcionar offline, mas não compartilhar dados. Essa distinção precisa ser validada antes de tratar “local” como requisito técnico.

### 6. Backup, recuperação e concorrência são riscos funcionais, não detalhes técnicos

Caso várias pessoas compartilhem dados, os seguintes pontos precisam ser requisitos explícitos:

- onde os dados ficam armazenados;
- como ocorre o backup;
- como recuperar dados após falha;
- o que acontece quando duas pessoas editam a mesma tarefa;
- como identificar o usuário que realizou uma alteração.

Ignorar esses aspectos pode tornar o aplicativo aparentemente funcional, mas frágil para uso real. Por outro lado, implementá-los antes de confirmar colaboração multiusuário seria excesso de escopo.

## Decisões que exigem validação humana

Antes de qualquer planejamento técnico, o responsável pelo produto deve responder:

1. “Local” significa desktop individual, rede local compartilhada ou servidor self-hosted?
2. Quantas pessoas usarão o sistema?
3. Elas precisam visualizar e editar as mesmas tarefas?
4. O acesso ocorrerá em um único computador ou em vários dispositivos?
5. O sistema precisa funcionar sem internet ou apenas evitar serviços externos?
6. Qual problema atual justifica criar uma nova ferramenta?
7. Quem instalará, atualizará e fará backup do sistema?
8. Há dados sensíveis que exigem autenticação ou controle de acesso?
9. Qual é o menor conjunto de funcionalidades que resolveria o problema?
10. Existe prazo ou restrição de ambiente que limite a solução?

## Recomendações objetivas

### Caminho recomendado para reduzir risco

Definir inicialmente um MVP de lista compartilhada simples, apenas se a colaboração for confirmada:

- uma fonte única de dados;
- tarefas com título, descrição opcional, status e responsável;
- criação, edição, conclusão e reabertura;
- filtro por status e responsável;
- exportação ou backup manual;
- operação restrita à rede local, se essa for a interpretação escolhida.

Deixar para uma fase posterior:

- notificações;
- comentários;
- histórico completo;
- múltiplos projetos;
- permissões granulares;
- sincronização entre instalações independentes;
- integrações com e-mail, chat ou calendário.

Se a necessidade for apenas individual, eliminar completamente colaboração, autenticação, sincronização e servidor compartilhado do primeiro escopo.

## Conclusão

A ideia é viável, mas ainda não constitui uma proposta suficientemente definida para planejamento técnico. O maior risco é interpretar “local” como uma solução colaborativa e, em seguida, incorporar funcionalidades demais para compensar requisitos que nunca foram confirmados.

A próxima decisão deve ser exclusivamente sobre o modelo de uso e o problema real. Depois disso, o escopo deve ser limitado ao menor fluxo que resolva esse problema, com backup e operação compatíveis com a responsabilidade da equipe.
