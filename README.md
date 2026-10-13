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

O catálogo é um baseline amplo, não uma afirmação de que toda obrigação de todo setor foi exaustivamente coberta. Controles condicionais só são ativados após avaliação de aplicabilidade e validação da fonte oficial vigente.

## Contrato tipado e validação

O registro possui um contrato estrutural em [schemas/compliance-registry.schema.json](schemas/compliance-registry.schema.json), usando JSON Schema Draft 2020-12. O schema valida a estrutura e os vocabulários permitidos; ele **não** comprova que uma regra legal é aplicável, atual ou juridicamente correta.

Execute os testes localmente com Python 3.12+:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

O workflow `.github/workflows/validate-compliance-registry.yml` executa essa validação em pushes e pull requests. Os testes verificam o schema, unicidade de IDs/nomes, pontos de execução permitidos e invariantes de segurança: regras desconhecidas ficam `indeterminate`, controles críticos permanecem em `fail_closed_for`, e os metadados obrigatórios de fonte/vigência/revisão/responsável continuam exigidos.

Este estágio valida o **catálogo declarativo**. Ainda não implementa um motor de execução, avaliador jurídico ou interceptores de runtime para Agents/Actions.
