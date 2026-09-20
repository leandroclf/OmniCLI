# Exploração de Produto: Plataforma de Colaboração

## Fatos fornecidos

- A única informação disponível é: "construir uma plataforma de colaboração".
- Nenhum detalhe adicional foi fornecido sobre público, escopo, funcionalidades, restrições técnicas, prazos ou orçamento.

## Problema (hipótese, não confirmada)

A ideia não descreve qual problema a plataforma resolve. "Colaboração" é um termo amplo que pode se referir a:

- Comunicação em tempo real (chat, videochamada).
- Edição conjunta de documentos/artefatos.
- Gestão de projetos e tarefas (kanban, backlog).
- Compartilhamento e versionamento de arquivos.
- Coordenação assíncrona entre equipes distribuídas.

**Sem uma dor específica identificada, qualquer direção de produto seria especulação.** Essa é a lacuna mais crítica do briefing.

## Público-alvo (hipótese)

Não há indicação de quem usaria a plataforma. Candidatos possíveis, cada um implicando produtos muito diferentes:

- Equipes internas de uma empresa (uso corporativo fechado).
- Times de desenvolvimento de software (foco técnico, integrações com Git/CI).
- Freelancers/agências colaborando com clientes externos.
- Comunidades abertas (colaboração pública, tipo wiki/fórum).

## Objetivos possíveis (hipótese)

- Reduzir fragmentação de ferramentas (unificar chat + tarefas + arquivos)?
- Melhorar visibilidade de progresso entre equipes?
- Viabilizar trabalho remoto/assíncrono?
- Ser um produto comercial (SaaS) ou uma ferramenta interna?

Nenhuma dessas metas foi declarada — todas precisam de validação com o solicitante.

## Funcionalidades candidatas (não compromissadas)

Se a direção for "gestão de projetos colaborativa" (hipótese mais comum para o termo genérico):
- Espaços de trabalho compartilhados
- Quadro de tarefas (kanban/lista)
- Comentários e menções
- Notificações
- Controle de permissões por papel

Se a direção for "comunicação":
- Chat em canais
- Chamadas de vídeo/áudio
- Compartilhamento de tela

**Recomendação:** não avançar para arquitetura ou escopo técnico até escolher entre essas famílias de produto — são investimentos de engenharia muito diferentes.

## Perguntas em aberto (bloqueantes)

1. Qual problema concreto motiva esta plataforma? Existe uma dor observada ou é uma ideia exploratória?
2. Quem são os usuários primários (interno vs. externo, técnico vs. não técnico)?
3. Colaboração em quê — documentos, código, tarefas, comunicação, design?
4. Já existe alguma ferramenta similar sendo substituída ou complementada (Slack, Notion, Jira, Google Docs)? Por quê ela não atende?
5. Este é um produto para uso próprio (interno) ou para venda (SaaS multi-tenant)?
6. Há restrições de prazo, orçamento, equipe ou stack tecnológica já definidas?
7. Tempo real é um requisito (edição simultânea, presença) ou colaboração assíncrona basta?
8. Existe necessidade de integração com sistemas externos? (Não devo presumir quais — isso não foi informado.)

## Recomendação para o próximo ciclo

Antes de detalhar funcionalidades ou arquitetura, é necessário responder às perguntas 1–4 acima. Sem isso, qualquer PRD ou especificação técnica seria construído sobre suposições não validadas.
