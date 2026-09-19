# Arquitetura do OmniCLI

## Decisões da V1

### Subprocessos locais

Os provedores são executados como processos locais. Essa escolha evita acoplamento inicial a APIs específicas, mas não elimina dependências de autenticação, versões, quotas ou mudanças de interface.

### Adaptadores

O orquestrador não conhece detalhes particulares de Gemini, Claude, Codex ou Copilot. Cada provedor é descrito no YAML e executado pelo `SubprocessAdapter`. Uma integração que exigir protocolo próprio poderá implementar `ProviderAdapter` dedicado.

### Contexto entre etapas

Cada etapa recebe a ideia original e a saída da etapa anterior. O prompt orienta crítica e expansão, evitando o padrão de concordância automática. Em ciclos adicionais, o último resultado retorna ao início do pipeline.

### Persistência

O workspace mantém um manifesto JSON e artefatos por etapa. O manifesto é atualizado após cada etapa concluída ou falha, permitindo diagnóstico sem depender apenas da saída do terminal.

### Segurança

O OmniCLI não é sandbox. Os subprocessos herdam o contexto do usuário. A V1 não executa código gerado nem altera repositórios automaticamente.

## Contrato de etapa

Cada etapa define:

- `name`: identificador único;
- `provider`: chave do adaptador;
- `role`: função editorial/técnica;
- `instruction`: objetivo da etapa;
- `timeout_seconds`: limite de execução;
- `max_retries`: número máximo de novas tentativas.

## Evolução prevista

O modo de implementação deverá gerar alterações em workspace temporário, apresentar diff e aguardar aprovação antes de aplicar qualquer mudança. Autocorreção deverá seguir o mesmo modelo: diagnóstico, patch, testes e aprovação.
