# Proposta Mestra de Arquitetura — Aplicativo Local de Lista de Tarefas para Equipe Pequena

## 1. Escopo

**Fato fornecido:** aplicativo local de lista de tarefas para equipe pequena. Nenhum outro requisito foi fornecido pela ideia original (número exato de pessoas, presencial/remoto, dono operacional, orçamento, prazo).

**Escopo desta proposta (recomendação):**
- Incluído: CRUD de tarefas, status, responsável, filtro básico, acesso compartilhado entre os membros da equipe em rede local.
- Explicitamente fora do MVP: autenticação formal, health check/métricas HTTP, controle otimista de concorrência, múltiplas fases de observabilidade, integrações externas.
- Decisão pendente que bloqueia o escopo final: **uso é compartilhado ou individual, e a equipe é 100% presencial?** Ver seção 8.

## 2. Premissas

| Premissa | Origem | Status |
|---|---|---|
| Equipe pequena = 3–10 pessoas | Inferência (não fornecida) | A confirmar com o solicitante |
| Uso predominantemente presencial | Inferência a partir de "local" | **Não confirmado** — se houver trabalho remoto, "rede local" deixa de ser viável sem VPN |
| Existe alguém disponível para operar backup/servidor | Hipótese assumida pela revisão anterior | **Frágil** — não há fato que sustente isso; tratar como risco em aberto, não como premissa aceita |
| Não há necessidade de integrações externas | Inferência por ausência de menção | Válida até indicação contrária |

Nenhuma dessas premissas deve ser tratada como decisão fechada até confirmação explícita do solicitante.

## 3. Decisões

Decisões preservadas da revisão anterior, por serem tecnicamente sólidas e já justificadas:

- **SQLite como banco de dados do MVP**, com caminho de migração para PostgreSQL apenas se necessário. Justificativa preservada: SQLite não deve ser acessado por múltiplos processos via arquivo em pasta de rede compartilhada — essa limitação é real e conhecida (escrita serializada por processo, não desenhada para acesso multi-host via filesystem compartilhado). Por isso, "banco em pasta de rede" é tratado como **inviável**, não como alternativa subótima.
- **Servidor único local**, acessado pela equipe via rede local (não é arquitetura distribuída).
- **Backup simples no início**: cópia manual/agendada do arquivo `.sqlite`, sem endpoint dedicado de backup no MVP.
- **Sem controle de conflito de edição no MVP**: para 3–10 pessoas atualizando tarefas esparsamente, colisões reais tendem a ser raras. Adotar "última gravação vence" e só evoluir para controle otimista (`version` + HTTP 409) se colisões forem observadas na prática.
- **Sem autenticação formal no MVP**, a menos que a equipe exija isolamento de identidade (ver seção 8).
- **Sem health check/métricas formais no MVP.** Log de erros em arquivo texto cobre a necessidade operacional nesse porte, na ausência de automação de monitoramento.

Correção explícita de inconsistência da entrada anterior: a proposta original tratava alternativas mais simples (ferramenta pronta, "última gravação vence", ausência de observabilidade formal) como itens de rodapé ou riscos, quando na prática deveriam ser o ponto de partida do MVP, não uma evolução futura condicionada.

## 4. Requisitos

### Funcionais (MVP)
- Criar, editar, listar e remover tarefas.
- Atribuir responsável e status (ex.: pendente/em andamento/concluída).
- Filtrar tarefas por responsável e status.
- Acesso simultâneo de múltiplos membros da equipe à mesma lista.

### Não funcionais
- Disponibilidade dependente da disponibilidade do servidor local (sem SLA formal — não informado que exista necessidade).
- Persistência local, sem dependência de serviços externos.
- Simplicidade operacional priorizada sobre robustez de produto, dado o porte da equipe.

## 5. Arquitetura (MVP)

```
[Navegador dos membros da equipe]
        │  HTTP (rede local)
        ▼
[Backend único] ── lê/escreve ──▶ [SQLite (arquivo local no servidor)]
```

- Um único processo backend, acessado via navegador pelos membros da equipe na mesma rede.
- Sem múltiplos serviços, sem fila, sem cache, sem camada de autenticação separada no MVP.
- Evolução futura (não incluída no MVP, apenas mapeada): controle otimista de concorrência, autenticação, observabilidade formal, migração para PostgreSQL — cada item adicionado somente quando um problema concreto for observado, não preventivamente.

**Sinalização de incerteza:** nenhuma tecnologia de frontend/backend específica foi definida aqui; a proposta é agnóstica de stack até essa escolha ser feita, para não presumir capacidade de ferramenta não confirmada.

## 6. Riscos

| Risco | Natureza | Mitigação proposta |
|---|---|---|
| Ausência de dono operacional definido | Fato ausente, crítico | Nomear responsável por backup/reinício antes de ir ao ar; sem isso, risco de perda de dados é real |
| Equipe com qualquer parcela remota | Hipótese não confirmada | Confirmar antes de arquitetar; "rede local" torna-se inviável sem VPN nesse cenário |
| Servidor rodando em máquina pessoal (ex.: notebook de alguém) | Risco operacional | Definir máquina dedicada, mesmo que modesta, antes do lançamento |
| Ferramenta pronta não avaliada | Lacuna de decisão | Registrar explicitamente por que não se optou por uma ferramenta self-hosted existente, antes de iniciar implementação do zero |
| Escopo crescer por analogia a "produto real" | Risco de processo | Manter disciplina de adicionar controle de conflito, autenticação e observabilidade somente mediante problema concreto observado |

## 7. Critérios de aceite (MVP)

- Membros da equipe conseguem criar, editar, listar, remover e filtrar tarefas simultaneamente pela rede local.
- Dados persistem corretamente entre reinícios do servidor.
- Existe rotina definida (mesmo manual) e responsável nomeado para backup do arquivo SQLite.
- Ausência de controle de conflito documentada como decisão consciente, não como omissão.
- Nenhuma dependência de serviço externo introduzida sem necessidade demonstrada.

## 8. Decisões pendentes

1. **Uso compartilhado vs. individual, e presença 100% presencial vs. remoto/híbrido** — decisão estrutural, não de implementação; muda a viabilidade de "rede local" como arquitetura.
2. **Quem é o dono operacional** (backup, reinício, disponibilidade) — sem essa definição, o MVP corre risco real de abandono operacional.
3. **Por que não usar uma ferramenta pronta (mesmo self-hosted)?** — não avaliado nem descartado explicitamente; deveria ser decisão registrada antes de iniciar desenvolvimento.
4. **Stack técnica concreta** (linguagem, framework) — não definida nesta proposta; nenhuma capacidade de ferramenta foi presumida para evitar alegação não verificável.
5. **Necessidade de autenticação** — depende da resposta à pergunta 1; se houver qualquer necessidade de isolar identidade além de "quem está usando na rede local", isso muda o MVP.
