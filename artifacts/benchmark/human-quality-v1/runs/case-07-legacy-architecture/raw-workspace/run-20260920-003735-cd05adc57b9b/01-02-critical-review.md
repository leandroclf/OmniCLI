# Revisão crítica — Migração de monólito crítico sem interromper clientes

## Síntese crítica

A proposta é válida como direção, mas está subespecificada e contém uma premissa potencialmente forte demais: “sem interromper” não é um objetivo operacional mensurável. Além disso, migrar um monólito crítico pode significar mudanças muito diferentes — infraestrutura, banco de dados, linguagem, arquitetura, fornecedor ou domínio funcional — com riscos e estratégias incompatíveis entre si.

Antes de escolher uma abordagem como strangler fig, dual-write ou shadow traffic, é necessário definir o que será migrado, quais comportamentos precisam permanecer compatíveis e qual nível de indisponibilidade ou inconsistência é aceitável.

## Fatos fornecidos

- O sistema é um monólito.
- O sistema é considerado crítico.
- Existe intenção de migrá-lo.
- Clientes existentes devem continuar utilizando o sistema durante o processo.
- A proposta não fornece stack, arquitetura-alvo, prazo, escopo funcional, perfil dos clientes, volume, dependências ou critérios de sucesso.

## Hipóteses presentes na proposta anterior

As seguintes ideias são plausíveis, mas ainda não foram comprovadas:

- O principal risco é a interrupção de clientes.
- A migração pode ser feita de forma incremental.
- O sistema novo terá paridade funcional suficiente para substituir o legado.
- Será possível manter dados sincronizados entre sistemas.
- Haverá uma forma segura de rollback.
- Observabilidade comparativa estará disponível.
- O problema pode ser resolvido predominantemente com decisões técnicas.

Essas hipóteses precisam ser validadas antes de serem tratadas como premissas de projeto.

## Contradições e premissas frágeis

### “Sem interrupção” pode conflitar com consistência e segurança

Uma migração sem indisponibilidade pode ainda causar:

- respostas diferentes entre o sistema antigo e o novo;
- duplicidade de comandos;
- perda ou reordenação de eventos;
- divergência de dados;
- alteração de permissões ou regras de negócio;
- degradação de desempenho sem erro explícito.

Portanto, disponibilidade não equivale a continuidade correta do serviço. O objetivo deveria distinguir pelo menos:

- indisponibilidade;
- perda de dados;
- inconsistência temporária;
- regressão funcional;
- degradação de latência;
- falha de integrações externas.

### Dual-write não deve ser tratado como solução padrão

Escrever simultaneamente no legado e no sistema novo pode aumentar, e não reduzir, o risco. Uma falha parcial pode deixar os sistemas divergentes, especialmente quando:

- as operações não são idempotentes;
- não existe transação distribuída confiável;
- os bancos possuem modelos diferentes;
- existem efeitos colaterais externos;
- a ordem dos eventos é relevante;
- não há reconciliação automatizada e procedimento de correção.

A decisão entre dual-write, replicação, CDC, migração por lote ou outra estratégia depende do modelo de dados e das garantias de consistência necessárias.

### Rollback de aplicação não implica rollback de dados

É possível redirecionar o tráfego de volta ao monólito e ainda assim não conseguir desfazer:

- gravações realizadas apenas no sistema novo;
- alterações de esquema;
- eventos publicados;
- chamadas a parceiros externos;
- mudanças de estado irreversíveis;
- operações financeiras ou logísticas já processadas.

O plano deve separar explicitamente rollback de tráfego, rollback de aplicação e recuperação/reconciliação de dados. Se os efeitos não forem reversíveis, o plano correto pode ser compensação, não rollback.

### “Paridade funcional” é insuficiente para sistemas críticos

Duas implementações podem produzir a mesma resposta em cenários comuns e divergir em:

- regras de exceção;
- arredondamentos;
- fusos horários;
- permissões;
- retentativas;
- ordenação;
- limites de volume;
- comportamento diante de falhas;
- integrações assíncronas.

A paridade precisa ser definida por capacidades e invariantes verificáveis, não apenas por uma lista de endpoints ou telas.

### A migração pode ampliar o escopo sem controle

O texto anterior menciona arquitetura, plataforma, fornecedor, banco e linguagem como possibilidades. Cada uma dessas mudanças pode ser um projeto distinto. Combiná-las na mesma iniciativa aumenta o risco de não ser possível atribuir a causa de uma regressão.

Recomendação objetiva: separar, salvo justificativa forte, a modernização estrutural da migração de plataforma, banco, fornecedor ou domínio funcional. Primeiro deve ser definido o menor corte que reduza o risco e produza evidência.

## Riscos que exigem investigação específica

### Dependências ocultas

O monólito pode ser consumido por:

- clientes externos;
- jobs agendados;
- sistemas internos;
- webhooks;
- integrações não documentadas;
- consultas diretas ao banco;
- relatórios;
- scripts operacionais;
- processos manuais dependentes de formatos específicos.

A ausência de documentação não significa ausência de dependência. É necessário produzir um inventário baseado em tráfego, código, configuração e evidências operacionais.

### Estado e transações

Devem ser identificados os fluxos que não toleram divergência, como:

- pagamento;
- faturamento;
- estoque;
- autorização;
- cadastro;
- expiração de sessão;
- processamento de pedidos;
- geração de documentos;
- envio de notificações.

Esses fluxos talvez não possam usar a mesma estratégia de migração adotada para consultas ou funcionalidades de baixo risco.

### Identidade e compatibilidade de sessão

Uma troca gradual pode falhar se sessões, tokens, permissões, cache ou regras de autenticação não forem compatíveis entre o legado e o destino. Isso pode interromper clientes mesmo quando as APIs aparentam estar disponíveis.

### Integrações externas e efeitos irreversíveis

A migração precisa considerar o comportamento de parceiros que podem:

- rejeitar novas credenciais;
- aplicar limites de requisição;
- não suportar duplicidade;
- não fornecer idempotência;
- enviar callbacks para endereços antigos;
- depender de uma ordem específica de chamadas.

Essas dependências podem tornar o corte parcial mais complexo do que o sistema interno.

### Capacidade operacional

Uma migração gradual normalmente exige operar dois caminhos por algum período. Isso pode demandar:

- suporte a duas versões;
- monitoramento comparativo;
- reconciliação;
- treinamento operacional;
- correção de dados;
- gestão de incidentes;
- critérios de avanço e parada.

Se a equipe não puder sustentar essa operação, a estratégia incremental pode criar mais risco que uma migração mais curta e controlada.

## Correções objetivas recomendadas

1. Substituir “sem interromper clientes” por metas mensuráveis, incluindo:
   - indisponibilidade máxima;
   - erro máximo aceitável;
   - impacto máximo de latência;
   - perda de dados permitida, idealmente zero;
   - janela máxima para detectar e conter regressões;
   - tempo máximo para redirecionar tráfego;
   - tempo e escopo de reconciliação.

2. Definir o significado de “migrar”:
   - infraestrutura;
   - banco de dados;
   - runtime ou linguagem;
   - arquitetura;
   - fornecedor;
   - módulos funcionais;
   - ou combinação desses itens.

3. Classificar os fluxos por risco e reversibilidade, em vez de migrar todo o monólito como uma unidade.

4. Criar critérios explícitos de entrada, avanço, pausa e encerramento para cada etapa da migração.

5. Exigir evidência de compatibilidade antes do corte:
   - testes de contrato;
   - testes de comportamento;
   - comparação de respostas;
   - testes de carga;
   - testes de falha;
   - validação de permissões;
   - reconciliação de dados.

6. Tratar rollback como uma decisão com escopo definido. Documentar separadamente:
   - reversão do roteamento;
   - reversão da versão;
   - tratamento dos dados já alterados;
   - compensação de efeitos externos;
   - comunicação e suporte aos clientes.

7. Proibir dual-write como decisão automática. Para cada fluxo, registrar:
   - fonte de verdade;
   - garantia de idempotência;
   - comportamento em falha parcial;
   - estratégia de reconciliação;
   - limite aceitável de divergência.

8. Definir o período de convivência entre legado e destino, incluindo a condição objetiva para desligar o legado. Sem essa condição, a migração pode virar operação permanente de dois sistemas.

9. Validar se há uma forma de reduzir o escopo inicial, por exemplo migrando primeiro um fluxo de leitura, um cliente interno ou um segmento de baixo risco. Essa opção só é válida se não introduzir uma arquitetura provisória difícil de remover.

## Decisões que exigem validação humana

A equipe responsável pelo negócio e pela operação precisa decidir:

- Qual indisponibilidade é realmente aceitável, inclusive em situações de emergência?
- Quais clientes, contratos ou fluxos não podem participar de uma migração gradual?
- Quais dados podem ficar temporariamente divergentes, se algum?
- Quem autoriza avançar, pausar ou reverter uma etapa?
- Qual é o impacto aceitável de manter dois sistemas em produção?
- Há restrições regulatórias, contratuais ou de auditoria aplicáveis?
- Qual prazo é fixo e qual pode ser renegociado?
- Qual é o custo operacional máximo aceitável para a convivência?
- O objetivo é reduzir risco do sistema atual, reduzir custo, aumentar escala ou habilitar novas capacidades?
- Qual resultado justificará a migração, independentemente da tecnologia escolhida?

## Critérios mínimos para considerar a proposta pronta para planejamento

A proposta só deveria avançar para desenho detalhado quando houver, no mínimo:

- arquitetura atual e arquitetura-alvo descritas;
- inventário de clientes e consumidores;
- mapa das integrações críticas;
- classificação dos dados e fluxos por criticidade;
- métricas de sucesso e limites de falha;
- estratégia de migração por fatias;
- fonte de verdade para cada dado;
- plano de reconciliação;
- plano de contenção e recuperação;
- responsáveis com autoridade para decisões de corte;
- evidência de que a equipe consegue operar o legado e o destino simultaneamente.

## Conclusão

A intenção de preservar clientes durante a migração é correta, mas não basta como requisito técnico. A maior lacuna não é escolher entre ferramentas ou padrões de arquitetura; é definir quais falhas são intoleráveis, quais efeitos podem ser compensados e qual escopo pode ser migrado com evidência.

A recomendação é transformar a frase original em uma iniciativa com limites claros: migrar um escopo inicialmente delimitado, preservar contratos observáveis, medir impacto real e avançar apenas após validar dados, integrações, operações e recuperação.
