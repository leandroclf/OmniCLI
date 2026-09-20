# Execução e auditoria do benchmark humano

O benchmark humano deve ser executado com casos anonimizados e sem revelar o
provedor ao avaliador. O arquivo de caso é
[`human-quality-v1.yaml`](human-quality-v1.yaml); o formato de resultado é
`human-quality-result-v1`.

## Fluxo recomendado

1. Escolha um caso e gere uma execução com configuração fixa.
2. Atribua um `blind_run_id` que não contenha provedor, modelo ou conta.
3. Entregue ao avaliador a proposta e os artefatos necessários sem metadados de
   provedor. O manifesto pode ser uma cópia redigida.
4. Preencha um resultado por avaliador usando
   [`human-quality-v1-result.example.yaml`](human-quality-v1-result.example.yaml)
   como modelo.
5. Valide o resultado:

   ```bash
   python scripts/validate-benchmark-result.py resultado.yaml
   ```

6. Preserve o resultado, a versão do benchmark, o fingerprint da configuração,
   o manifesto redigido e os artefatos de saída em um diretório de evidências.

## Escala

Cada dimensão recebe uma nota independente de 0 a 4:

- `0`: ausente ou incorreto;
- `1`: muito insuficiente;
- `2`: parcialmente útil, exige retrabalho relevante;
- `3`: adequado para uma decisão técnica;
- `4`: excelente, claro e acionável.

A média é apenas um resumo. Uma falha crítica reprova a proposta ou exige uma
decisão explícita de ressalva. Nunca substitua as justificativas textuais por
uma nota única.

## Evidências obrigatórias

Cada resultado deve apontar para:

- manifesto da execução;
- saída final;
- saídas intermediárias das etapas;
- artefatos de prompt, com conteúdo ou apenas hash conforme a política de dados;
- fingerprint da configuração;
- notas por dimensão;
- falhas críticas, observações e decisão final;
- tempo de revisão e identificador pseudônimo do avaliador.

O resultado não deve conter campos `provider`, `model`, `vendor` ou equivalentes.
O validador rejeita esses identificadores para preservar o cegamento.

O exemplo incluído é somente um exemplo estrutural e não constitui evidência de
qualidade ou aprovação do produto.

## Execução atual

Os oito casos de `human-quality-v1` possuem execução e pacote cego em
`artifacts/benchmark/human-quality-v1/`. As avaliações em `results/` foram
preenchidas pelo Codex como revisão assistida, com `decision:
approved-with-reservations`. Elas servem para triagem e diagnóstico do
benchmark, mas não encerram o gate humano: cada caso ainda precisa de uma
revisão independente sem acesso à identidade dos executores.
