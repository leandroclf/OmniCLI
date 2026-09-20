# Revisão de viabilidade — aplicativo local de lista de tarefas

## 1. Veredito geral

A proposta é tecnicamente viável e coerente para uma equipe pequena, mas está **superdimensionada para um MVP**. O documento entrega uma arquitetura de produto (health check, métricas, controle otimista de concorrência, plano de autenticação, 4 fases) para um problema cuja hipótese central — "quantas pessoas realmente vão usar isso ao mesmo tempo" — ainda não foi confirmada. Antes de aprovar a arquitetura, é preciso resolver a pergunta que o próprio documento levanta e não responde: uso individual ou compartilhado.

---

## 2. Fatos, hipóteses e recomendações

### Fatos (fornecidos pelo pedido original)
- É uma lista de tarefas.
- Deve ser local.
- Público: equipe pequena.

Tudo o mais no documento anterior — SQLite, controle otimista, health check, backup versionado, 4 usuários simultâneos, etc. — é **hipótese de arquitetura**, não fato. O documento já sinaliza isso corretamente na seção 2, o que é positivo; mas o restante do texto trata essas hipóteses como decisões praticamente fechadas.

### Minha avaliação das hipóteses
- "Equipe pequena" (ideia original) provavelmente significa 3–10 pessoas. Nesse volume, um servidor único em rede local é razoável, mas é a opção com **mais partes móveis** entre as alternativas plausíveis, não a mais simples.
- Não há indicação de que a equipe tenha alguém disponível para operar um servidor, cuidar de backup e responder por indisponibilidade. Isso é uma hipótese operacional crítica que o documento assume otimisticamente na Fase 0 sem propor um plano B se a resposta for "ninguém".

---

## 3. Custos e complexidade não totalmente explicitados

| Item proposto | Custo real por trás |
|---|---|
| Servidor local sempre ligado | Depende de um computador dedicado ou de alguém desligar/ligar; se for o notebook de alguém da equipe, a app cai sempre que a pessoa sai/fecha a tampa |
| Controle otimista de concorrência (`version`, HTTP 409) | Exige lógica de comparação, tratamento de conflito na UI e testes — não é trivial para uma "lista de tarefas simples" |
| Backup + restauração testada | Exige rotina, responsável nomeado e teste periódico — facilmente esquecido em equipes pequenas sem operação dedicada |
| Autenticação local opcional | Se ativada, adiciona hashing de senha, gestão de contas e mais uma decisão de segurança para manter |
| 4 fases + observabilidade (logs, health check, métricas) | Razoável para um produto que vai crescer; é overhead real se o uso for de 3 pessoas marcando tarefas |

Nenhum desses itens é absurdo isoladamente, mas juntos formam uma **arquitetura de produto interno de médio porte**, não o menor artefato que resolve "lista de tarefas compartilhada para equipe pequena".

---

## 4. Alternativas mais simples que deveriam ser consideradas antes

1. **Ferramenta já existente**: para "equipe pequena + lista de tarefas local", vale perguntar explicitamente por que uma ferramenta pronta (mesmo self-hosted, ex. Kanban simples open-source) foi descartada. O documento não menciona essa opção nem justifica construir do zero — isso é uma lacuna, não um erro, mas deveria estar registrado como decisão explícita.
2. **Arquivo compartilhado único (SQLite em pasta compartilhada, ou até um CSV/JSON versionado)**: o próprio documento reconhece que SQLite não deve ser acessado por múltiplos processos ao mesmo tempo — o que é correto — mas isso significa que a alternativa "banco em pasta de rede" nunca foi realmente uma opção; ok mencionar como risco, mas não precisa ocupar espaço como algo "não recomendado", já que é tecnicamente inviável, não apenas subótimo.
3. **"Última gravação vence" em vez de controle otimista**: para 3–10 pessoas atualizando tarefas esparsamente, colisões reais são raras. O documento já cogita isso como "aceitável", mas enterra a opção mais simples sob uma recomendação padrão de concorrência otimista. Recomendação: **começar sem controle de conflito** e só adicionar `version`/409 se colisões forem observadas na prática.
4. **Sem health check/métricas na Fase 1–2**: um log de erros em arquivo texto e "abrir a página e ver se carrega" cobrem a mesma necessidade operacional para uma equipe de poucas pessoas. Health check HTTP formal é justificável quando há automação de monitoramento — que não existe aqui.

---

## 5. Riscos operacionais reais (fatos ausentes que travam a decisão)

- **Não há dono operacional definido.** Backup, atualização e reinício do servidor recaem sobre "alguém da equipe" — em equipes pequenas isso costuma significar "ninguém", até o dia em que os dados somem.
- **Dependência de rede local estável.** Não foi informado se a equipe é presencial, híbrida ou remota. Se houver qualquer trabalho remoto, "rede local" deixa de ser viável sem VPN — e isso não foi mencionado nem pelo pedido original nem pela proposta.
- **Sem SLA nem stakeholders formais** (não informado): reduz a pressão por HA, mas também reduz a tolerância a complexidade desnecessária — outro argumento a favor de simplificar o MVP.

---

## 6. Limitações de ferramentas sinalizadas corretamente

- A ressalva sobre **SQLite não poder ser acessado por múltiplos clientes num arquivo em pasta de rede** está correta e é uma limitação real e conhecida do SQLite (concorrência de escrita é serializada por processo, não pensada para acesso multi-host via filesystem compartilhado).
- A recomendação de migrar para PostgreSQL "apenas se necessário" é sólida e evita engenharia prematura.

Não há, no restante do documento, alegações de capacidades de ferramentas que pareçam inventadas ou não verificáveis.

---

## 7. Recomendação final

Aprovar a direção geral (web local, backend único, SQLite, sem integrações), mas **cortar escopo do MVP antes de iniciar a Fase 1**:

1. Responder primeiro: uso é compartilhado ou individual, e é 100% presencial? Isso muda a arquitetura, não é detalhe de implementação.
2. MVP mínimo real = CRUD de tarefas + status + responsável + filtro, **sem** controle otimista, **sem** autenticação, **sem** health check/métricas formais. Adicionar cada um só quando um problema concreto aparecer (conflito de edição observado, incidente de indisponibilidade, etc.).
3. Backup pode começar como "copiar o arquivo `.sqlite` manualmente uma vez por dia" — script de uma linha, sem endpoint `/api/backups` dedicado no início.
4. Antes de escrever qualquer código, verificar se uma ferramenta pronta (mesmo self-hosted) não resolve com custo de implementação zero.

A arquitetura de 15 seções é um bom mapa de **evolução futura**, não um MVP. O risco maior não é técnico — é a equipe pequena gastar mais tempo operando o sistema (backup, servidor, conflitos) do que usando-o.
