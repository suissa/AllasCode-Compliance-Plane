# Catálogo de Compliance — MEI e ME no Brasil

Este catálogo define **intents do sistema**, não intenções expressas por usuários. Cada intent representa uma verificação, decisão ou obrigação de conformidade aplicada a dados, eventos, documentos, comandos e efeitos colaterais.

> Escopo: baseline horizontal para empresas brasileiras MEI e ME, com controles condicionais conforme atividade, município/estado, regime tributário, contratação de pessoas, tratamento de dados e setor regulado. Não existe uma lista universal que garanta conformidade para toda empresa: regras e prazos mudam e dependem do caso. Regras legais devem ter fonte oficial, vigência, jurisdição, versão e responsável pela validação.

## 1. Modelo de execução

Cada definição de Intent, Agent e Action aceita política granular de execução:

- `on_ingress`: ao receber dados, arquivos, eventos ou comandos.
- `before_egress`: antes de enviar dados para cliente, fornecedor, órgão público, API, canal ou sistema externo.
- `between_agents`: antes e depois de uma transferência entre Agents.
- `between_actions`: antes e depois de uma Action, inclusive antes de efeitos irreversíveis.
- `scheduled`: varredura periódica por prazo, validade, vencimento ou mudança normativa.
- `on_state_change`: quando cadastro, consentimento, contrato, regra, risco ou status muda.

Cada ponto pode ser habilitado independentemente por empresa, tenant, tipo de dado, entidade, canal, Agent, Action, destino, risco e jurisdição. Configuração sugerida:

```yaml
execution:
  on_ingress: true
  before_egress: true
  between_agents: true
  between_actions: true
  scheduled: false
  on_state_change: true
enforcement:
  mode: block | quarantine | warn | audit_only
  fail_closed_for: [personal_data_export, tax_filing, payment, credential_change]
  human_review_for: [ambiguous_legal_rule, high_impact_decision, exception_request]
  evidence_required: true
```

Os valores acima são um exemplo de esquema, não configuração ativada automaticamente. Para controles críticos, falha de verificação deve bloquear ou colocar em quarentena; para controles consultivos, alertar pode ser adequado. Toda exceção precisa de escopo, justificativa, aprovador, validade e trilha de auditoria.

## 2. Contrato mínimo de um registro

Todos os registros devem possuir identificador estável, descrição, categoria, escopo, gatilhos, severidade, modo de aplicação, entradas/saídas tipadas, dependências, evidências exigidas, versão e testes.

- **Intent**: regra de verificação de sistema, com predicados de conformidade e resultado `compliant | non_compliant | indeterminate | not_applicable`.
- **Agent**: responsável por coordenar um domínio de controles; não deve declarar conformidade sem evidência suficiente.
- **Action**: operação atômica e auditável de leitura, validação, cálculo, redação, bloqueio, notificação, retenção ou geração de evidência.
- **Evidence**: fonte, hash ou referência segura, timestamp, versão da regra, resultado e cadeia de custódia. Evitar copiar dados pessoais ou segredos para logs.
- **Policy**: liga Intent/Agent/Action a um ou mais pontos de execução, com escopo e modo de enforcement.
- **LegalRule**: fonte oficial, artigo/item, jurisdição, início/fim de vigência, aplicabilidade, data de revisão e responsável. Não codificar obrigação legal sem fonte e data de vigência.

## 3. Agents e seus domínios

### A. Governança e motor de regras
- `ComplianceOrchestratorAgent`: resolve políticas aplicáveis e encadeia verificações.
- `LegalRuleRegistryAgent`: mantém fontes oficiais, vigência, jurisdição e histórico.
- `ApplicabilityAssessmentAgent`: determina se regra se aplica ao CNPJ, CNAE, porte, regime, localidade e operação.
- `ComplianceEvidenceAgent`: gera e preserva evidências minimizadas e rastreáveis.
- `ExceptionAndHumanReviewAgent`: encaminha ambiguidade, exceções e decisões de alto impacto para revisão humana.
- `ComplianceMonitoringAgent`: reavalia regras alteradas, prazos, pendências e desvios.
- `PolicyConfigurationAgent`: administra os pontos de execução e o enforcement granular.
- `AuditTrailAgent`: registra decisões, versões, atores e resultados sem expor payloads sensíveis.

### B. Privacidade e dados
- `LGPDComplianceAgent`
- `DataInventoryAndMappingAgent`
- `DataSubjectRightsAgent`
- `ConsentAndLegalBasisAgent`
- `RetentionAndDeletionAgent`
- `DataSharingAndTransferAgent`
- `PrivacyIncidentAgent`
- `DPOApplicabilityAgent`

### C. Segurança da informação
- `IdentityAndAccessComplianceAgent`
- `SecretsAndCredentialAgent`
- `EncryptionAndKeyManagementAgent`
- `SecurityLoggingAgent`
- `VulnerabilityAndPatchAgent`
- `BackupAndRecoveryAgent`
- `IncidentResponseAgent`
- `ThirdPartySecurityAgent`

### D. Cadastro empresarial, tributário e fiscal
- `BusinessRegistrationAgent`
- `CNAEAndPermitAgent`
- `TaxRegimeApplicabilityAgent`
- `DASAndTaxCalendarAgent`
- `RevenueThresholdAndEligibilityAgent`
- `InvoiceAndFiscalDocumentAgent`
- `TaxWithholdingAgent`
- `BookkeepingAndReconciliationAgent`
- `AnnualDeclarationsAgent`
- `MunicipalAndStateObligationsAgent`

### E. Financeiro e pagamentos
- `PaymentComplianceAgent`
- `CashFlowAndReconciliationAgent`
- `FraudAndChargebackAgent`
- `RefundAndCancellationAgent`
- `FinancialRecordRetentionAgent`

### F. Pessoas e trabalho (condicional)
- `EmploymentRelationshipRiskAgent`
- `PayrollAndBenefitsAgent`
- `eSocialAndLaborObligationsAgent`
- `OccupationalHealthAndSafetyAgent`
- `WorkingTimeAndLeaveAgent`
- `ContractorClassificationAgent`

### G. Consumidor, contratos e comércio
- `ConsumerRightsAgent`
- `OfferAndAdvertisingAgent`
- `ContractAndTermsAgent`
- `CancellationAndWarrantyAgent`
- `CustomerSupportAndComplaintAgent`
- `EcommerceDisclosureAgent`
- `IntellectualPropertyAgent`

### H. Operação e setores condicionais
- `EnvironmentalAndWasteAgent`
- `ProductSafetyAndTraceabilityAgent`
- `HealthAndSanitaryPermitAgent`
- `FoodHandlingAndTraceabilityAgent`
- `TransportAndMobilityComplianceAgent`
- `FinancialServicesApplicabilityAgent`
- `ProfessionalLicensingAgent`
- `PublicProcurementAgent`
- `AccessibilityAndDigitalServiceAgent`

## 4. Catálogo de Intents do sistema

Os IDs são estáveis e não devem ser derivados de texto livre. Cada Intent é uma verificação sistêmica.

### PRIV — privacidade e LGPD
- `PRIV-001 LGPD`: verificar se coleta, uso, armazenamento, compartilhamento e descarte de dados pessoais têm finalidade, base legal e transparência adequadas.
- `PRIV-002 DataMinimization`: verificar necessidade e proporcionalidade dos campos coletados.
- `PRIV-003 PurposeLimitation`: impedir uso incompatível com a finalidade documentada.
- `PRIV-004 LegalBasis`: verificar base legal por finalidade e categoria de dado.
- `PRIV-005 SensitiveData`: identificar dados pessoais sensíveis e exigir salvaguardas reforçadas.
- `PRIV-006 ChildrenAndAdolescents`: aplicar controles específicos quando houver dados de crianças/adolescentes.
- `PRIV-007 TransparencyNotice`: verificar aviso de privacidade e informação ao titular.
- `PRIV-008 ConsentValidity`: verificar consentimento quando essa for a base utilizada; não presumir consentimento como base universal.
- `PRIV-009 DataSubjectRights`: validar fluxo de confirmação, acesso, correção, anonimização, bloqueio, eliminação e demais direitos aplicáveis.
- `PRIV-010 RetentionLimit`: verificar prazo e fundamento de retenção, incluindo obrigações legais de guarda.
- `PRIV-011 SecureDeletion`: verificar descarte seguro e propagação a cópias/operadores quando cabível.
- `PRIV-012 ProcessorContract`: verificar instruções, responsabilidades e cláusulas com operadores.
- `PRIV-013 SharingAndTransfer`: verificar compartilhamento, destinatários e transferência internacional quando houver.
- `PRIV-014 IncidentNotification`: classificar incidente com dados pessoais, preservar evidências e avaliar notificações exigidas.
- `PRIV-015 DPOApplicability`: verificar obrigação e exceções aplicáveis à indicação de encarregado, sem presumir dispensa universal.
- `PRIV-016 PrivacyByDesign`: verificar minimização, controles e proteção desde a concepção.
- `PRIV-017 AutomatedDecision`: verificar transparência e revisão de decisões automatizadas quando aplicável.
- `PRIV-018 DataAccuracy`: verificar atualização, origem e correção de dados pessoais.
- `PRIV-019 AnonymizationClaim`: validar alegação de anonimização e risco de reidentificação.
- `PRIV-020 CrossContextLeakage`: impedir que dados de um cliente/tenant sejam expostos a outro.

### SEC — segurança e controle de acesso
- `SEC-001 Authentication`: validar mecanismo de autenticação adequado ao risco.
- `SEC-002 Authorization`: verificar menor privilégio e autorização por recurso/ação.
- `SEC-003 TenantIsolation`: impedir leitura ou mutação entre empresas.
- `SEC-004 SecretsExposure`: impedir segredos, tokens e credenciais em payloads, logs, erros ou exports.
- `SEC-005 Encryption`: verificar proteção criptográfica em trânsito e em repouso conforme política.
- `SEC-006 KeyLifecycle`: verificar rotação, acesso, revogação e recuperação de chaves.
- `SEC-007 InputValidation`: validar esquema, tamanho, tipo, encoding e limites de entrada.
- `SEC-008 OutputFiltering`: remover dados/atributos proibidos antes da saída.
- `SEC-009 AuditIntegrity`: proteger integridade, acesso e retenção de trilhas.
- `SEC-010 VulnerabilityStatus`: verificar vulnerabilidades e dependências relevantes.
- `SEC-011 BackupRecoverability`: verificar backup, restauração e objetivos de recuperação.
- `SEC-012 IncidentReadiness`: verificar contatos, plano, severidade e resposta a incidentes.
- `SEC-013 ThirdPartyAccess`: validar acesso de fornecedores e integrações.
- `SEC-014 RateAbuseProtection`: detectar abuso, automação indevida e exfiltração.
- `SEC-015 DataExportAuthorization`: exigir autorização, minimização e registro em exportações.
- `SEC-016 SecureConfiguration`: verificar configuração segura e ausência de defaults perigosos.

### CORP — cadastro e regularidade empresarial
- `CORP-001 CNPJStatus`: verificar situação cadastral e consistência do CNPJ.
- `CORP-002 LegalFormEligibility`: verificar compatibilidade da forma empresarial com a operação.
- `CORP-003 CNAECompatibility`: verificar compatibilidade entre atividade efetiva, CNAE e permissões.
- `CORP-004 AddressAndJurisdiction`: verificar endereço e jurisdição para obrigações locais.
- `CORP-005 PermitApplicability`: identificar alvarás/licenças aplicáveis sem presumir dispensa automática.
- `CORP-006 RegistrationConsistency`: comparar cadastros federal, estadual e municipal quando relevantes.
- `CORP-007 CertificateValidity`: verificar validade de certidões exigidas para uma operação específica.
- `CORP-008 BusinessChangeReporting`: detectar mudanças cadastrais que exigem atualização ou comunicação.

### TAX — tributário, declarações e limites
- `TAX-001 RegimeEligibility`: verificar elegibilidade e condições do regime tributário declarado.
- `TAX-002 MEIEligibility`: verificar atividade permitida, participação societária, empregados e demais condições atuais do MEI.
- `TAX-003 RevenueThreshold`: monitorar receita acumulada e limites aplicáveis, com período e regra versionados.
- `TAX-004 RevenueClassification`: classificar receita por atividade, competência e natureza.
- `TAX-005 DASDueDate`: monitorar vencimentos e status de DAS/tributos aplicáveis.
- `TAX-006 TaxCalculation`: verificar cálculo, alíquota, base e arredondamento contra regra vigente.
- `TAX-007 WithholdingApplicability`: verificar retenções conforme serviço, tomador, município e regra.
- `TAX-008 AnnualDeclaration`: monitorar declarações anuais aplicáveis ao enquadramento.
- `TAX-009 SimplesObligations`: verificar obrigações do Simples Nacional quando aplicável.
- `TAX-010 TaxRegimeTransition`: detectar desenquadramento, excesso de limite ou mudança de regime e encaminhar revisão.
- `TAX-011 TaxEvidence`: garantir vínculo entre cálculo, documentos, regra e período.
- `TAX-012 TaxCalendar`: manter calendário por empresa, atividade, jurisdição e regime.
- `TAX-013 FiscalReconciliation`: comparar vendas, recebimentos, notas e declarações.
- `TAX-014 TaxRecordRetention`: verificar retenção de documentos fiscais e contábeis pelo prazo aplicável.
- `TAX-015 NoUnsupportedTaxAdvice`: não apresentar estimativa automatizada como parecer contábil definitivo sem premissas e revisão.

### FISC — documentos fiscais e faturamento
- `FISC-001 InvoiceRequired`: determinar se a operação exige documento fiscal conforme regra e contraparte.
- `FISC-002 InvoiceSchema`: validar campos, identificadores, totais e formato do documento.
- `FISC-003 InvoiceSequence`: verificar numeração, duplicidade e integridade de série quando aplicável.
- `FISC-004 InvoiceAuthorization`: verificar autorização, rejeição, cancelamento ou contingência junto ao sistema competente.
- `FISC-005 InvoiceRecipient`: validar dados do destinatário na medida legalmente necessária.
- `FISC-006 ServiceMunicipalRule`: aplicar regras de NFS-e e município conforme atividade e sistema vigente.
- `FISC-007 ProductTaxRule`: verificar classificação e tributação de mercadorias quando aplicável.
- `FISC-008 CorrectionAndCancellation`: verificar prazos e procedimentos para correção/cancelamento.
- `FISC-009 InvoiceOutboundDisclosure`: impedir envio de documento a destinatário incorreto.
- `FISC-010 FiscalDocumentIntegrity`: detectar alteração, duplicidade ou divergência entre documento e transação.

### FIN — pagamentos e registros financeiros
- `FIN-001 PaymentAuthorization`: verificar autorização, valor, moeda, destinatário e idempotência.
- `FIN-002 PixAndPaymentData`: minimizar dados de pagamento e proteger identificadores.
- `FIN-003 Reconciliation`: conciliar pedidos, notas, recebimentos, estornos e extratos.
- `FIN-004 RefundEligibility`: verificar política e direitos legais para estorno/reembolso.
- `FIN-005 ChargebackEvidence`: preservar evidências necessárias sem retenção excessiva.
- `FIN-006 FraudSignals`: identificar transações anômalas e encaminhar revisão.
- `FIN-007 CashFlowConsistency`: detectar inconsistências entre caixa e registros.
- `FIN-008 PaymentExport`: validar destinatário e minimização antes de exportar dados financeiros.
- `FIN-009 FinancialRecordRetention`: aplicar prazos de guarda e restrição de acesso.
- `FIN-010 NoCredentialStorage`: impedir armazenamento indevido de senha, CVV ou segredo de pagamento.

### LAB — trabalho e folha (quando houver empregados ou relação relevante)
- `LAB-001 EmploymentApplicability`: identificar obrigações trabalhistas conforme vínculo real, não apenas rótulo contratual.
- `LAB-002 MEIEmployeeLimit`: verificar limite e condições de contratação permitida ao MEI na regra vigente.
- `LAB-003 PayrollAccuracy`: validar folha, descontos, benefícios e pagamentos.
- `LAB-004 eSocialObligations`: monitorar eventos e prazos aplicáveis.
- `LAB-005 FGTSAndSocialContributions`: verificar recolhimentos exigidos.
- `LAB-006 WorkingTime`: verificar jornada, intervalos, descanso e registros quando aplicáveis.
- `LAB-007 LeaveAndTermination`: validar férias, afastamentos, rescisão e prazos.
- `LAB-008 OccupationalSafety`: identificar obrigações de saúde e segurança conforme atividade e porte.
- `LAB-009 WorkerDataPrivacy`: limitar acesso e tratamento de dados de trabalhadores.
- `LAB-010 ContractorMisclassification`: sinalizar risco de vínculo e exigir análise humana.

### CONS — consumidor, venda e publicidade
- `CONS-001 ConsumerDisclosure`: verificar identificação do fornecedor, preço, características e condições essenciais.
- `CONS-002 AdvertisingTruthfulness`: verificar alegações objetivas e comprovação de ofertas.
- `CONS-003 TotalPriceTransparency`: apresentar preço total e custos obrigatórios antes da contratação.
- `CONS-004 EcommerceInformation`: verificar informações e confirmação exigidas para contratação eletrônica.
- `CONS-005 RightOfWithdrawal`: avaliar direito de arrependimento e prazo quando aplicável.
- `CONS-006 CancellationFlow`: verificar cancelamento acessível e rastreável.
- `CONS-007 WarrantyAndDefect`: controlar garantia legal/contratual e tratamento de defeitos.
- `CONS-008 ComplaintHandling`: registrar e encaminhar reclamações nos prazos aplicáveis.
- `CONS-009 DarkPatterns`: detectar padrões que induzam erro ou dificultem escolhas/cancelamentos.
- `CONS-010 CustomerDataDisclosure`: evitar divulgação de dados de clientes a destinatários errados.
- `CONS-011 TermsVersioning`: registrar versão dos termos aceitos e sua vigência.
- `CONS-012 Accessibility`: verificar requisitos de acessibilidade aplicáveis ao canal e serviço.

### CONT — contratos e propriedade intelectual
- `CONT-001 ContractCompleteness`: verificar partes, objeto, preço, prazos, responsabilidades e condições essenciais.
- `CONT-002 ContractAuthority`: verificar autoridade para aceitar ou assinar em nome da empresa.
- `CONT-003 ContractVersion`: preservar versão, aceite, timestamp e evidência.
- `CONT-004 RenewalAndExpiry`: monitorar vencimentos, renovação e aviso prévio.
- `CONT-005 LiabilityAndWarranty`: sinalizar cláusulas de responsabilidade e garantia que exigem revisão jurídica.
- `CONT-006 Confidentiality`: verificar obrigações de confidencialidade e classificação.
- `CONT-007 IPOwnership`: verificar licença, titularidade e permissões de uso de conteúdo/software.
- `CONT-008 ThirdPartyLicense`: verificar licenças de bibliotecas, imagens, fontes e materiais de terceiros.
- `CONT-009 ESignatureEvidence`: preservar evidências de autoria, integridade e aceite eletrônico.
- `CONT-010 UnfairOrAmbiguousTerms`: sinalizar cláusulas ambíguas, potencialmente abusivas ou inconsistentes para revisão humana.

### OPS — licenças, produtos e operação
- `OPS-001 ActivityLicense`: verificar licenças por atividade, local e risco.
- `OPS-002 SanitaryPermit`: verificar exigências sanitárias para atividades abrangidas.
- `OPS-003 ProductTraceability`: verificar lote, origem, validade e rastreabilidade quando aplicável.
- `OPS-004 ProductSafety`: verificar alertas, recolhimento e restrições de venda.
- `OPS-005 EnvironmentalDuty`: identificar licenciamento, resíduos e obrigações ambientais conforme atividade.
- `OPS-006 WasteDestination`: verificar destinação e evidência para resíduos sujeitos a controle.
- `OPS-007 ProfessionalLicense`: verificar registro profissional quando a atividade exigir.
- `OPS-008 SectorRegulation`: determinar se há regulação setorial (saúde, alimentos, transporte, finanças etc.).
- `OPS-009 PublicProcurement`: verificar requisitos de habilitação, certidões e integridade em contratação pública.
- `OPS-010 ImportExport`: verificar obrigações aduaneiras e restrições se houver comércio internacional.
- `OPS-011 RecallAndSafetyNotice`: interromper venda/expedição e notificar responsáveis quando houver risco confirmado.
- `OPS-012 LocalRuleApplicability`: determinar exigências estaduais e municipais por localidade.

### GOV — governança e evidências
- `GOV-001 RuleVersionCurrent`: verificar que a regra usada está vigente na data da operação.
- `GOV-002 EvidenceCompleteness`: verificar evidência mínima para sustentar resultado.
- `GOV-003 DecisionTraceability`: vincular resultado a dados de entrada, regra, versão, Agent e Action.
- `GOV-004 PolicyCoverage`: verificar cobertura de pontos de execução obrigatórios.
- `GOV-005 ExceptionExpiry`: expirar exceções e reavaliar operações relacionadas.
- `GOV-006 HumanReviewRequired`: exigir revisão humana em caso ambíguo, de alto impacto ou com fonte insuficiente.
- `GOV-007 RegulatoryChange`: detectar alteração normativa e identificar políticas potencialmente afetadas.
- `GOV-008 DataLineage`: preservar proveniência e transformações de dados.
- `GOV-009 ControlConflict`: detectar regras conflitantes e bloquear decisão automática até resolução.
- `GOV-010 ComplianceStatusDisclosure`: não declarar “conforme” quando resultado for indeterminado ou houver controles críticos pendentes.

## 5. Actions reutilizáveis

Actions são operações atômicas; a execução é limitada por permissões e pelo resultado dos Intents.

### Coleta e validação
- `ValidateSchema`, `NormalizeInput`, `ClassifyData`, `DetectPersonalData`, `DetectSensitiveData`, `ResolveEntity`, `ResolveJurisdiction`, `AssessApplicability`, `ValidateLegalBasis`, `ValidateRuleVersion`, `ValidateDocument`, `ValidateSignature`, `ValidateTotals`, `DetectDuplicate`, `CompareRecords`.

### Proteção e minimização
- `MinimizePayload`, `RedactPersonalData`, `RedactSecrets`, `EncryptPayload`, `DecryptAuthorizedPayload`, `TokenizeIdentifier`, `EnforceTenantBoundary`, `CheckAuthorization`, `CheckPurpose`, `CheckRetention`, `DeleteEligibleData`, `RestrictAccess`, `RotateCredential`, `RevokeCredential`.

### Decisão e enforcement
- `EvaluateIntent`, `EvaluatePolicy`, `BlockOperation`, `QuarantinePayload`, `WarnOperator`, `RequireHumanReview`, `RequestMissingEvidence`, `ApplyApprovedException`, `RevalidateAfterMutation`, `FailClosed`, `FailOpenWithAudit` (somente quando política permitir explicitamente).

### Evidência e monitoramento
- `CreateEvidenceRecord`, `HashArtifact`, `AppendAuditEvent`, `RecordRuleVersion`, `RecordDecision`, `MonitorDeadline`, `ScheduleRecheck`, `DetectRegulatoryChange`, `OpenComplianceCase`, `CloseComplianceCase`, `ExportAuditBundle`, `VerifyEvidenceIntegrity`.

### Fiscal, financeiro e documentos
- `CalculateTax`, `ReconcileRevenue`, `CheckRevenueThreshold`, `GenerateDueDateAlert`, `ValidateInvoice`, `CheckInvoiceAuthorization`, `ReconcilePayment`, `ValidateRefund`, `ValidatePayroll`, `ValidateDeclarationReadiness`, `GenerateComplianceReport`.

### Comunicação e direitos
- `GeneratePrivacyNotice`, `AcknowledgeDataSubjectRequest`, `RouteDataSubjectRequest`, `NotifyIncidentOwner`, `PrepareRegulatoryNotificationDraft`, `SendApprovedNotice`, `DeliverCustomerDisclosure`, `RecordCustomerAcceptance`. Notificações legais externas devem ser submetidas a aprovação quando os fatos ou prazos forem incertos.

## 6. Matriz de pontos de execução recomendados

| Domínio | Entrada | Antes da saída | Entre Agents | Entre Actions |
|---|---|---|---|---|
| LGPD / dados pessoais | detectar finalidade, base, minimização | minimização, destinatário, direitos | escopo e tenant | antes de persistir, compartilhar ou apagar |
| Segurança | schema, autenticação, autorização | segredo, classificação, destino | autorização e isolamento | antes de mutação privilegiada |
| Tributário/fiscal | classificar operação e período | validar documento/declaração | regra vigente e evidência | antes de emitir, transmitir ou cancelar |
| Financeiro | valor, idempotência, fraude | destinatário e dados mínimos | autorização de pagamento | antes de cobrar, estornar ou transferir |
| Trabalhista | vínculo, dados necessários | destinatário autorizado | segregação de folha | antes de calcular, transmitir ou pagar |
| Consumidor | oferta e preço | informação completa e canal correto | consistência da oferta | antes de cobrar, negar, cancelar ou reembolsar |
| Contratos | partes e versão | destinatário e conteúdo permitido | poderes e confidencialidade | antes de assinar, renovar ou rescindir |
| Operação regulada | atividade e licença | rótulo, alerta e destinatário | aplicabilidade setorial | antes de vender, despachar ou executar |
| Governança | versão e escopo | evidência sem vazamento | proveniência | antes de concluir ou publicar status |

## 7. Resultados e política de falha

- `compliant`: evidências suficientes e todos os predicados aplicáveis aprovados.
- `non_compliant`: ao menos um predicado obrigatório falhou.
- `indeterminate`: evidência, fonte, jurisdição ou regra vigente insuficiente.
- `not_applicable`: inaplicabilidade comprovada e registrada; não usar como default.

Para `indeterminate`, não transformar ausência de evidência em conformidade. Operações críticas devem ser bloqueadas ou encaminhadas para revisão humana. Alertas não substituem obrigações legais nem parecer profissional.

## 8. MEI e ME: aplicabilidade dinâmica

Não tratar “MEI” e “ME” como se fossem regimes tributários equivalentes. O motor deve verificar separadamente natureza jurídica, enquadramento como MEI, porte ME, opção tributária (incluindo Simples Nacional quando aplicável), CNAE, faturamento, município/estado, existência de empregados e atividade efetivamente exercida. Uma ME pode estar no Simples Nacional ou em outro regime permitido; o porte, sozinho, não determina todas as obrigações.

Regras devem ser consultadas em fontes oficiais, conforme a matéria: Portal do Empreendedor e gov.br, Receita Federal, Portal do Simples Nacional, legislação federal (Planalto), ANPD, eSocial, SEFAZ estadual, prefeitura e órgãos reguladores setoriais. O catálogo identifica controles; não substitui assessoria contábil/jurídica nem garante conformidade automática.

## 9. Critérios de aceite para implementação

1. Cada ID possui definição tipada, entradas/saídas e testes positivos, negativos e indeterminados.
2. Todas as entidades têm `execution_points` configuráveis independentemente e herdáveis com precedência explícita: override por operação > Action > Agent > Intent > padrão da empresa.
3. Toda decisão registra ID/versão da regra, jurisdição, timestamp, resultado, evidências referenciadas e versão da política.
4. O sistema suporta `not_applicable` com justificativa e evidência, nunca por ausência de configuração.
5. Dados pessoais e segredos não são replicados em logs; evidências usam minimização, referências seguras e controles de acesso.
6. Mudança de regra gera análise de impacto e revalidação de políticas relacionadas.
7. Falhas de dependência resultam em `indeterminate`; o enforcement decorre do risco configurado.
8. Há testes de isolamento entre tenants, replay/idempotência, concorrência, expiração de exceções e vazamento entre Agents.
9. Toda Action com efeito externo exige autorização explícita e Intent de pré-condição.
10. Cada controle regulatório possui fonte oficial, versão, vigência e responsável por revisão antes de produção.
