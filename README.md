# AllasCode-Compliance-Plane

Catálogo e runtime de controles sistêmicos de conformidade para empresas brasileiras, começando pelo baseline comum a MEI e ME.

**Um Intent é uma intenção do sistema:** verificar se dados, eventos, documentos, transições entre Agents/Actions e operações estão em conformidade com regras aplicáveis. Não é uma intenção do usuário.

## Princípios
- Compliance como política executável, versionada, auditável e baseada em evidências.
- Execução granular na entrada, antes da saída, entre Agents, entre Actions e em eventos agendados/de mudança de estado.
- Aplicabilidade dinâmica por CNPJ, enquadramento, atividade/CNAE, jurisdição, regime, dados tratados e contexto operacional.
- Resultado explícito: `compliant`, `non_compliant`, `indeterminate` ou `not_applicable`.
- Não afirmar conformidade quando a regra estiver desatualizada ou a evidência for insuficiente.
- Privacidade por padrão: minimizar payloads, isolar tenants e não registrar PII/segredos em logs.
- Controles legais devem apontar para fonte oficial e vigência; catálogo não substitui revisão contábil/jurídica.

## Catálogo
- [Catálogo de Agents, Intents e Actions](docs/catalog/mei-me-brazil.md)
- [Registro de políticas em YAML](catalog/compliance-registry.yaml)
- [Definições tipadas de todos os Agents, Actions e Intents](catalog/compliance-definitions.json)
- [Schema das definições tipadas](schemas/compliance-definitions.schema.json)

O catálogo é um baseline amplo, não uma afirmação de que toda obrigação de todo setor foi exaustivamente coberta. Controles condicionais só são ativados após avaliação de aplicabilidade e validação da fonte oficial vigente.

## Contrato tipado e validação

O registro possui um contrato estrutural em [schemas/compliance-registry.schema.json](schemas/compliance-registry.schema.json), usando JSON Schema Draft 2020-12. O schema valida a estrutura e os vocabulários permitidos; ele **não** comprova que uma regra legal é aplicável, atual ou juridicamente correta.

Execute os testes localmente com Python 3.12+:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

O workflow `.github/workflows/validate-compliance-registry.yml` executa essa validação em pushes e pull requests. Os testes verificam o schema, unicidade de IDs/nomes, pontos de execução permitidos e invariantes de segurança: regras desconhecidas ficam `indeterminate`, controles críticos permanecem em `fail_closed_for`, e os metadados obrigatórios de fonte/vigência/revisão/responsável continuam exigidos.

O catálogo declarativo agora é acompanhado por um motor inicial de políticas em `compliance/runtime.py`. Ele resolve precedência, protege Intents obrigatórios contra desativação e gera decisões tipadas. Ainda não inclui interceptores automáticos no pipeline de produção, nem evaluators legais específicos ou integrações com os sistemas fiscais.


## Runtime e Intents obrigatórios

O arquivo `catalog/compliance-definitions.json` define individualmente os 64 Agents, 80 Actions e 137 Intents, com descrições, domínios, contratos, pontos de execução, responsáveis e vínculos entre Intents/Agents/Actions. O módulo `compliance/runtime.py` implementa primitivas tipadas para carregar o manifest, resolver precedência de policies, avaliar aplicabilidade e produzir decisões auditáveis. A avaliação concreta de cada regra legal continua sendo fornecida por adaptadores/evaluators com evidências e fontes versionadas; o runtime não substitui uma interpretação jurídica nem integra automaticamente com Receita Federal, prefeitura ou sistemas de emissão.

Cada Intent expõe `mandatory` e `user_can_disable`. Quando `mandatory: true`, a tentativa de desativar o controle é ignorada pelo runtime e registrada na razão da decisão. Isso não presume aplicabilidade universal: o resultado ainda pode ser `not_applicable` após uma avaliação documentada, ou `indeterminate` se faltarem evidências.

O catálogo inclui controles específicos para omissão de recibos/documentos na saúde: `FISC-011`, `FISC-012` e `FISC-013`. O Receita Saúde é aplicável, conforme a regra oficial, a profissionais de saúde específicos atuando como pessoa física; clínicas/PJs precisam passar pela avaliação fiscal correspondente, sem generalizar indevidamente essa obrigação.

Para validar:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```


## Entidade Person e execução dos controles LGPD

O módulo `compliance/person.py` fornece uma entidade `Person` e um `PersonService`
de referência. Criação, leitura e exclusão passam pelo interceptor e avaliam os
20 controles `PRIV-001` a `PRIV-020` nos pontos `on_ingress`, `before_egress`
e `between_actions`. Evidência ausente ou inválida resulta em `indeterminate`
e bloqueia a operação; o serviço não permite rebaixar esses controles para
`warn` ou `audit_only`.

`compliance/telemetry.py` fornece `JsonEvidenceSink`, que grava eventos JSON
estruturados com `trace_id`, `operation_id`, Intent, resultado, versão da regra
e referências de evidência. Nomes, telefone, e-mail e payloads pessoais não são
incluídos nos logs. Veja [guia da entidade Person e evidências LGPD](docs/person-lgpd.md).

Exemplo de validação: `python -m pytest -q`. O exemplo de evidências na documentação
ilustra o contrato da API; em produção, cada referência deve apontar para evidência
real produzida por avaliadores confiáveis e revisados. Isso instrumenta os controles
do catálogo, mas não certifica por si só conformidade legal integral.
