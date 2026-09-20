# Revisão crítica da proposta

## Fatos fornecidos

- A proposta limita-se a: “Construir uma plataforma de colaboração”.
- Não foram informados problema, público, contexto de uso, modelo de negócio, prazo, orçamento, equipe, requisitos técnicos ou critérios de sucesso.
- O material anterior reconhece corretamente que “colaboração” é um conceito amplo e que avançar diretamente para arquitetura ou escopo seria prematuro.

## Premissas frágeis identificadas

### 1. “Construir” pode ser uma premissa precipitada

A proposta assume que a resposta adequada é criar uma nova plataforma. Ainda não há evidência de que:

- exista uma dor relevante não atendida;
- ferramentas existentes sejam insuficientes;
- uma integração ou configuração de ferramentas atuais não resolva o problema;
- o custo de desenvolver e operar uma nova plataforma seja justificável.

**Correção recomendada:** validar primeiro o problema e as alternativas existentes. A decisão inicial deve ser entre construir, integrar, adaptar ou não prosseguir.

### 2. O conceito de colaboração está amplo demais

A lista anterior apresenta chat, videochamadas, documentos, tarefas, arquivos e comunidades. Esses domínios têm usuários, modelos de dados, requisitos de segurança e complexidades operacionais diferentes.

Agrupar tudo sob “plataforma de colaboração” cria risco de transformar a proposta em um produto excessivamente abrangente, sem um caso de uso central.

**Correção recomendada:** exigir uma frase de problema no formato:

> “Para [público], que enfrenta [problema observável], a solução deve melhorar [resultado mensurável], em comparação com [alternativa atual].”

### 3. A exploração introduz uma direção sem evidência suficiente

O material anterior chama “gestão de projetos colaborativa” de “hipótese mais comum”. Isso não é uma base suficiente para priorização. A frequência presumida do caso de uso não demonstra que seja o caso relevante deste projeto.

**Correção recomendada:** remover essa preferência ou classificá-la explicitamente como uma opção entre várias, sem tratá-la como direção padrão.

### 4. As perguntas estão corretas, mas não estão priorizadas por decisão

As perguntas 1–8 misturam decisões fundamentais com detalhes que só fazem sentido depois. Por exemplo, stack tecnológica, integrações e requisitos de tempo real podem depender da definição do problema e do público.

Além disso, o texto declara que as perguntas 1–4 são necessárias, mas também lista 5–8 como questões abertas. Isso gera uma inconsistência sobre o que realmente bloqueia a próxima etapa.

**Correção recomendada:** separar as perguntas em camadas:

1. **Bloqueantes imediatas:** problema, usuário, contexto e resultado esperado.
2. **Decisões de produto:** alternativa atual, escopo inicial e modelo de acesso.
3. **Restrições de execução:** prazo, equipe, orçamento e tecnologia.
4. **Requisitos derivados:** tempo real, integrações, permissões, retenção e auditoria.

### 5. O escopo funcional aparece antes da validação do problema

A enumeração de funcionalidades — espaços de trabalho, kanban, comentários, notificações e permissões — pode induzir o solicitante a aceitar um escopo por inércia, mesmo sem evidência de necessidade.

Também há risco de confundir funcionalidades essenciais com expectativas genéricas de uma plataforma.

**Correção recomendada:** não criar backlog funcional ainda. Primeiro definir um único fluxo principal e o menor resultado útil que precisa ser entregue. As funcionalidades devem ser derivadas desse fluxo.

## Riscos principais

- **Risco de produto:** desenvolver algo genérico que não resolve uma dor prioritária.
- **Risco de escopo:** tentar combinar comunicação, gestão, documentos e arquivos em um único produto inicial.
- **Risco de adoção:** exigir que usuários migrem de ferramentas já consolidadas sem uma vantagem clara.
- **Risco de complexidade:** permissões, compartilhamento, notificações, histórico e colaboração em tempo real podem ampliar significativamente a implementação.
- **Risco de requisitos ocultos:** podem surgir necessidades de segurança, auditoria, retenção de dados, disponibilidade e administração corporativa.
- **Risco de validação insuficiente:** decisões importantes podem ser tomadas apenas com base em opiniões, sem entrevistas, protótipo ou teste com usuários.

Esses riscos são inferências a partir da ausência de contexto; não há dados suficientes para estimar sua probabilidade ou impacto real.

## Decisões que exigem validação humana

Antes de aprovar qualquer especificação, o responsável pelo produto precisa definir:

- Qual grupo de usuários será atendido primeiro.
- Qual problema concreto justifica a plataforma.
- Qual é o contexto: uso interno, produto comercial, projeto experimental ou outro.
- Qual alternativa é usada atualmente.
- Qual mudança de comportamento ou resultado indicará sucesso.
- Qual é o menor escopo aceitável para uma primeira versão.
- Se a colaboração precisa ser síncrona, assíncrona ou ambas.
- Se a plataforma precisa ser multiusuário, multi-organização ou multi-tenant.
- Quais restrições de prazo, equipe, orçamento e tecnologia são reais.
- Quais requisitos de segurança, privacidade, auditoria e integração são obrigatórios.

## Correções objetivas para o próximo ciclo

1. Substituir a descrição atual por um problema específico, com público e resultado esperado.
2. Escolher um único caso de uso primário para a primeira versão.
3. Comparar construir versus integrar ou adaptar ferramentas existentes.
4. Definir de três a cinco critérios de sucesso mensuráveis.
5. Separar requisitos bloqueantes de decisões posteriores.
6. Adiar arquitetura, stack e backlog até que o problema e o escopo inicial estejam validados.
7. Registrar explicitamente quais decisões continuam como hipóteses.
8. Validar a direção com usuários representativos antes de comprometer desenvolvimento significativo.

## Conclusão

A recomendação anterior está correta ao não avançar diretamente para arquitetura, mas ainda concede atenção excessiva a possíveis tipos de produto e funcionalidades. O principal ajuste é tornar a etapa seguinte uma decisão de problema e escopo, não uma escolha prematura entre módulos de uma plataforma.

No estado atual, a proposta não está pronta para implementação. A próxima saída deveria conter, no mínimo, um público-alvo definido, uma dor observável, um caso de uso prioritário e um critério de sucesso verificável.
