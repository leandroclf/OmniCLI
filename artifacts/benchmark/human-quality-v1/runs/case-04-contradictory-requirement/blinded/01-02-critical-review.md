# Revisão crítica da proposta

## Síntese

A proposta — “exigir consistência forte global, custo mínimo e disponibilidade offline total” — combina objetivos que não podem ser garantidos simultaneamente para o mesmo estado mutável e em todos os dispositivos.

O conflito principal não é apenas de implementação: durante uma desconexão, uma réplica offline não consegue confirmar que sua escrita é compatível com as escritas feitas em outras réplicas. Portanto, é necessário escolher entre:

- aceitar escritas offline e resolver divergências depois; ou
- preservar consistência forte bloqueando escritas que exigem coordenação.

A proposta precisa ser reformulada antes de servir como requisito de produto ou arquitetura.

## Fatos fornecidos

- Consistência forte global é exigida.
- Custo mínimo é exigido.
- Disponibilidade offline total é exigida.
- Não foram definidos:
  - quais dados precisam dessas garantias;
  - se “consistência forte” significa linearizabilidade, serialização ou apenas ausência de conflitos;
  - se “global” se refere a dispositivos, regiões, usuários ou instalações;
  - se o modo offline deve permitir leitura, escrita ou execução completa;
  - quais custos devem ser minimizados.

## Hipóteses que não devem virar requisitos sem validação

A saída anterior inferiu que o OmniCLI sincronizaria configurações, memória, regras e skills entre máquinas. Essa hipótese pode ser útil para exploração, mas não está comprovada pela ideia original.

Também não está comprovado que:

- haverá múltiplas réplicas escrevendo simultaneamente;
- o estado será compartilhado entre usuários;
- haverá operação multi-região;
- toda a aplicação precisará permanecer disponível offline;
- todos os dados terão o mesmo nível de criticidade.

Essas incertezas são importantes porque podem permitir uma solução mais simples: por exemplo, consistência forte apenas para metadados críticos e funcionamento offline para dados locais ou somente leitura.

## Contradições e riscos

### 1. Consistência forte e escrita offline total são incompatíveis

Se dois dispositivos podem ficar offline e alterar o mesmo dado, não existe como garantir simultaneamente que:

- ambos aceitem as escritas imediatamente;
- cada dispositivo permaneça totalmente disponível;
- o resultado global seja forte e único;
- nenhuma escrita seja perdida, rejeitada ou sujeita a conflito.

Para preservar consistência forte, o sistema precisa bloquear determinadas operações offline, utilizar autoridade local previamente concedida ou aceitar que algumas operações não sejam realmente globais.

A formulação correta não deve prometer “offline total” sem definir quais operações continuam disponíveis.

### 2. “Custo mínimo” não é um requisito operacional suficiente

Custo mínimo pode significar:

- menor custo de infraestrutura;
- menor custo de armazenamento e tráfego;
- menor esforço de desenvolvimento;
- menor custo de operação e suporte;
- menor latência ou consumo local.

Essas metas podem entrar em conflito. Uma arquitetura com consenso global pode reduzir conflitos de aplicação, mas aumentar custos de rede, operação e disponibilidade. Já uma arquitetura offline-first pode reduzir dependência de infraestrutura, mas aumentar complexidade de sincronização, testes e suporte a conflitos.

É necessário definir uma função de custo e um limite aceitável, não apenas declarar “mínimo”.

### 3. “Disponibilidade offline total” é amplo demais

A expressão pode significar desde abrir a CLI sem internet até executar qualquer comando, modificar qualquer configuração e sincronizar depois.

Esses cenários têm riscos diferentes. Em particular:

- leitura de estado local pode ser viável offline;
- alteração de dados não compartilhados pode ser viável offline;
- alteração de dados globais exige coordenação ou uma política de conflitos;
- operações que dependem de serviços externos não podem ser garantidas offline sem cache ou substituição local;
- autenticação, revogação e controle de acesso podem ficar desatualizados offline.

Sem delimitação, o requisito cria uma expectativa impossível de testar objetivamente.

### 4. A proposta não define o comportamento após a reconexão

Mesmo que a operação offline seja aceita, faltam decisões sobre:

- detecção de conflitos;
- prioridade entre alterações;
- rejeição ou compensação de escritas;
- merge automático;
- intervenção manual;
- auditoria;
- idempotência;
- ordenação temporal;
- recuperação após falha durante a sincronização.

“Sincronizar depois” não é uma política suficiente.

### 5. O custo de operação pode ser subestimado

Uma solução que tenta oferecer simultaneamente consistência global, tolerância a falhas e offline pode exigir:

- armazenamento local completo;
- logs de alterações;
- controle de versões;
- resolução de conflitos;
- testes de partições e reconexões;
- observabilidade;
- mecanismos de recuperação;
- políticas para dados obsoletos ou revogados.

Mesmo que a infraestrutura seja barata, a complexidade operacional pode tornar o custo total alto.

### 6. O requisito pode estar superdimensionado

Exigir consistência forte global para todos os dados provavelmente é excesso de escopo. Configurações, preferências, cache, histórico e artefatos podem ter necessidades distintas.

Aplicar a mesma garantia a todo o estado aumenta custo e reduz disponibilidade sem evidência de que todos os dados precisem disso.

## Correções recomendadas

Substituir o requisito único por uma política por categoria de dado e por tipo de operação. Uma formulação inicial mais realista seria:

> O sistema deve operar offline com leitura e alterações locais previamente autorizadas. Dados que exigem consistência global devem ser alterados apenas quando houver conectividade suficiente; alterações feitas offline em dados sincronizáveis devem seguir uma política explícita de versionamento e resolução de conflitos. O custo deve ser minimizado dentro de limites definidos de consistência, disponibilidade e recuperação.

Como alternativa, se a consistência forte for realmente inegociável:

> O sistema deve oferecer operação offline para leitura e para dados estritamente locais. Operações que alterem estado global devem ser bloqueadas ou limitadas offline até que possam ser confirmadas pela autoridade responsável.

Se a disponibilidade offline for a prioridade:

> O sistema deve aceitar alterações offline e sincronizá-las posteriormente, com consistência eventual, detecção de conflitos, resolução determinística e possibilidade de intervenção manual nos casos não resolvíveis automaticamente.

## Escopo mínimo recomendado

Antes de escolher tecnologia ou arquitetura, validar apenas estas decisões:

1. Quais dados são globais e quais podem ser locais?
2. Quais operações precisam de escrita offline?
3. Em caso de conflito, alguma escrita pode ser rejeitada ou revertida?
4. Qual atraso de sincronização é aceitável?
5. O modo offline precisa suportar somente leitura ou também execução completa?
6. Qual dimensão de custo deve ser minimizada?
7. Qual garantia é realmente obrigatória: consistência forte, ausência de perda de dados ou disponibilidade?

## Decisões que exigem validação humana

As seguintes decisões não devem ser inferidas pela implementação:

- prioridade entre consistência, disponibilidade e custo;
- definição formal de “offline total”;
- dados sujeitos a consistência forte;
- autorização para manter dados sensíveis em réplicas locais;
- política de conflitos;
- possibilidade de rejeitar ou desfazer alterações;
- nível mínimo aceitável de desatualização;
- orçamento ou limite operacional;
- quantidade esperada de dispositivos e escritores concorrentes.

## Conclusão

A proposta, como está escrita, não é implementável como um conjunto simultâneo de garantias universais. O ponto a corrigir não é escolher uma tecnologia, mas decompor o requisito por dado, operação e estado de conectividade.

A recomendação é adotar uma destas direções:

- consistência forte para um subconjunto crítico e offline limitado;
- disponibilidade offline ampla com consistência eventual e conflitos explícitos; ou
- operação offline predominantemente local, com sincronização controlada após a reconexão.

Sem essa escolha, qualquer estimativa de custo, arquitetura ou cronograma será pouco confiável.
