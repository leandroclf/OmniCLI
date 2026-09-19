# Status da transição para produção

Atualizado em 2026-09-19. Este documento separa evidência local reproduzível de
gates que dependem de provedores autenticados e avaliadores desenvolvedores.

## Estado atual

O OmniCLI permanece em **beta controlado / pré-produção operacional**. O CI
local está verde, mas isso não autoriza declarar compatibilidade de fornecedor
ou qualidade humana.

### Evidências locais concluídas

- [x] Testes, Ruff, mypy, `pip check`, `pip-audit` e build executados.
- [x] Laboratório determinístico de transporte, timeout, falha e limite de saída.
- [x] Diagnóstico offline e inspeção JSON de execuções.
- [x] Métricas agregadas por execução: duração, falhas, retries, contexto e volume.
- [x] Release gera wheel, source distribution, checksums e SBOM CycloneDX.
- [x] Manifestos preservam a versão do schema e rejeitam versões futuras.
- [x] Casos/rubric do benchmark humano e matriz de compatibilidade versionados.
- [x] Schema JSON definido para o relatório consolidado de transição.

### Gates ainda bloqueantes

- [ ] Compatibilidade autenticada completa por provedor e versão, em ambiente opt-in.
- [ ] Benchmark humano versionado, cego ou parcialmente cego, com rubric.
- [ ] Piloto técnico controlado com material não sensível e aprovação humana.
- [ ] Instalação limpa, upgrade, downgrade, rollback e limites de recursos testados.
- [ ] Runbook de suporte, incidentes, retenção, exclusão e responsável técnico aprovados.

## Critério de promoção

Não marcar uma release como produtiva enquanto os dois primeiros gates acima
estiverem pendentes. O resultado sintético de `omnicli lab verify` deve ser
descrito apenas como evidência local; ele não substitui teste de fornecedor nem
benchmark humano.

## Próxima execução controlada

1. Selecionar os provedores e versões que terão suporte oficial.
2. Executar `omnicli doctor --capabilities --json` antes de cada caso.
3. Registrar comando, versão, autenticação, duração, tamanho da resposta,
   falhas previsíveis e evidência redigida, sem persistir credenciais ou prompts.
4. Repetir os casos aprovados e anexar a matriz ao release candidate.
5. Conduzir o benchmark humano sem usar o nome do provedor como critério.

## Evidência parcial de 2026-09-19

Claude Code `2.1.273` e Codex CLI `0.154.0` responderam corretamente a duas
sondagens sintéticas repetidas. Isso valida apenas o caminho de sucesso mínimo,
o transporte e a superfície de capacidades observada. A matriz completa ainda
está `partial`: não foram executados timeout, saída inválida, limite de saída,
quota, sessão expirada, rollback nem o pipeline completo de concepção.

O Gemini CLI está instalado na versão `0.60.0`, mas foi retirado do escopo desta
validação. A execução autenticada anterior excedeu o timeout de cinco segundos;
ele permanece registrado como `deferred-next-stage` para ser reavaliado quando o
provedor estiver estabilizado.

O Copilot permanece explicitamente `out-of-scope`, conforme decisão do projeto.

O escopo oficial desta release é exclusivamente **Claude Code e Codex CLI**.

Durante o piloto, o Codex excedeu o limite genérico de stderr de 20.000
caracteres apesar de produzir saída válida. O limite específico do Codex foi
ajustado para 100.000 caracteres; stdout, prompt, timeout e transporte seguro
continuam limitados.

### Pipeline linear validado

Em 2026-09-19, o pipeline completo com cinco etapas foi executado com sucesso
usando somente Claude e Codex: `discovery`, `critical-review`, `architecture`,
`feasibility` e `master-proposal`. A execução durou 218.210 ms, não teve
retries, produziu qualidade sintética `100/100` e não persistiu conteúdo no
repositório. A evidência detalhada está na matriz de compatibilidade.
