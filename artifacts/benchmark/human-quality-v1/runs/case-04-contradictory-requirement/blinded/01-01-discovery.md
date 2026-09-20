# Exploração de Produto: OmniCLI

## Ideia original (dado fornecido pelo usuário)
> "Exigir consistência forte global, custo mínimo e disponibilidade offline total."

Isto é uma frase de requisitos, não uma ideia de produto completa. Antes de expandir, é preciso sinalizar uma tensão técnica que ela contém.

## ⚠️ Inconsistência a resolver

As três exigências, combinadas, são **mutuamente conflitantes** em qualquer sistema distribuído real:

- **Consistência forte global** normalmente exige coordenação síncrona entre nós/réplicas (ex.: consenso, locks distribuídos, quorum), o que implica dependência de rede e de um número mínimo de nós disponíveis.
- **Disponibilidade offline total** significa operar sem rede, aceitando escritas locais que podem divergir de outras réplicas.
- Isso é essencialmente o **teorema CAP** (e sua extensão PACELC): sob partição de rede — que é exatamente o que "offline total" garante que vai acontecer — o sistema tem que escolher entre consistência e disponibilidade. Não é possível ter as duas de forma "forte" e "total" simultaneamente.
- "Custo mínimo" agrava o problema, pois as técnicas que aproximam consistência forte com tolerância a partição (consenso tipo Raft/Paxos, quorum multi-região, relógios sincronizados) tendem a ser as mais caras em infraestrutura e operação.

Isso não é uma opinião — é uma restrição matemática conhecida. Não vou tratar a frase como se as três propriedades fossem simultaneamente alcançáveis sem trade-off explícito.

**Recomendação:** decidir qual das três é a prioridade inegociável e quais podem ser relaxadas (ex.: consistência *eventual* com resolução de conflitos, ou "offline com sincronização posterior", ou "consistência forte apenas quando online"). Sem essa decisão, qualquer especificação seguinte estará mal fundamentada.

---

## Problema (hipótese, não fato)
*Não foi fornecido contexto sobre qual problema o OmniCLI resolve.* Hipótese razoável a partir do nome e do domínio (CLI + múltiplos agentes de IA, conforme AGENTS.md do projeto): um usuário que opera CLIs de IA (Claude Code, Codex etc.) em múltiplas máquinas/ambientes precisa que configuração, memória, skills e regras estejam sincronizadas e utilizáveis mesmo sem conexão — mas essa é uma inferência do repositório, não algo declarado na ideia original.

**Pergunta em aberto:** qual é o problema real que motivou esses três requisitos? Sem isso, todo o restante deste documento é especulativo.

## Público-alvo (hipótese)
- Desenvolvedores que usam múltiplos dispositivos/ambientes (ex.: notebook + servidor + CI).
- Equipes que precisam de comportamento determinístico e auditável de ferramentas de CLI.
*Não confirmado pelo usuário — apenas inferência a partir do contexto do repositório.*

## Objetivos possíveis (a validar)
1. Garantir que o estado (configuração, regras, memória) seja idêntico em todos os pontos de acesso — se essa é a intenção real de "consistência forte global".
2. Minimizar custo de infraestrutura (armazenamento, rede, sincronização).
3. Permitir uso completo sem internet.

## Funcionalidades candidatas (especulativas — sinalizadas como tal)
- Modo de sincronização diferida (fila local → sync quando há rede) — isto seria consistência **eventual**, não forte; incompatível com o requisito literal.
- Réplica local completa (cache total) para uso offline.
- Mecanismo de resolução de conflitos quando múltiplas réplicas offline reconectam.
- Modo "somente leitura garantida" offline com escrita bloqueada até sincronizar (preserva consistência forte, sacrifica disponibilidade de escrita).

*Nenhuma dessas funcionalidades foi mencionada pelo usuário — são sugestões para resolver o conflito acima, não requisitos confirmados.*

## Perguntas ainda não respondidas
1. Qual das três propriedades (consistência forte, custo mínimo, offline total) é a prioridade quando elas colidem?
2. "Consistência forte" se refere a quê especificamente — dados do usuário, configuração do agente, estado de execução de comandos?
3. "Global" significa múltiplos dispositivos do mesmo usuário, múltiplos usuários, ou múltiplas regiões geográficas?
4. Existe uma janela de tolerância aceitável para desatualização quando offline (ex.: "consistente após sincronizar")?
5. "Custo mínimo" é custo de infraestrutura, custo de desenvolvimento, ou custo operacional (manutenção)?
6. Qual é o público-alvo real e o problema concreto que motivou este requisito? (não fornecido)
7. Existem restrições de plataforma, escala esperada (quantos nós/usuários) ou requisitos regulatórios não mencionados?
