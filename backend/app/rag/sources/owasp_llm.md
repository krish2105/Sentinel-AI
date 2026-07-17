# OWASP Top 10 for LLM Applications (2025/2026)

> Original concise summaries with canonical IDs and mitigation guidance. Not a verbatim reproduction of the OWASP text.

## LLM01 | Prompt Injection | category: direct_injection
**Risk.** An attacker crafts input that overrides the developer's instructions, making the model follow attacker intent. *Direct* injection is typed by the user; *indirect* injection is smuggled in through retrieved documents, tool outputs, or web content the model ingests. Indirect injection is the more dangerous production case because the user may never see the payload.
**Impact.** Instruction override, data exfiltration, unauthorized tool use, safety-guardrail bypass.
**Mitigations.** Enforce structural separation between system and user content; treat all retrieved/tool content as untrusted and scan it with the same filters as user input; run a deterministic injection classifier as a fast first layer and a constrained LLM-as-judge as a reasoning second layer; normalize unicode to defeat hidden-character tricks; constrain model privileges (least privilege on tools).

## LLM02 | Sensitive Information Disclosure | category: sensitive_disclosure
**Risk.** The model reveals PII, credentials, secrets, proprietary data, or other sensitive content present in its context, training data, or connected systems.
**Impact.** Privacy violation, credential leakage, regulatory exposure.
**Mitigations.** Scan outputs for PII/secrets (regex + presidio-style detectors); maintain deny-lists for known sensitive tokens; never place secrets in the prompt; scope retrieval to the requesting user; redact before returning.

## LLM03 | Supply Chain | category: supply_chain
**Risk.** Compromised third-party models, datasets, plugins, or dependencies introduce vulnerabilities or backdoors.
**Impact.** Backdoored behavior, data poisoning at the source, license and integrity risk.
**Mitigations.** Pin and verify model/dataset provenance; use signed artifacts; vet plugins; SBOM for the AI stack; isolate untrusted components.

## LLM04 | Data and Model Poisoning | category: data_poisoning
**Risk.** Adversarial manipulation of training, fine-tuning, or embedding data to bias, backdoor, or degrade the model.
**Impact.** Persistent malicious behavior, biased or unsafe outputs.
**Mitigations.** Trusted-only ingestion pipelines; validate and provenance-check data; anomaly detection on training sets; sandbox any user-contributed knowledge.

## LLM05 | Improper Output Handling | category: output_handling
**Risk.** Downstream systems trust model output without validation, enabling XSS, SQLi, SSRF, or remote code execution when output is rendered or executed.
**Impact.** Injection into downstream systems, code execution.
**Mitigations.** Treat model output as untrusted user input; validate/escape before use; never `eval` model text; use structured, schema-validated outputs; context-aware encoding.

## LLM06 | Excessive Agency | category: excessive_agency
**Risk.** The model is granted excessive functionality, permissions, or autonomy, so a manipulation escalates into real-world actions (sending email, deleting data, spending money).
**Impact.** Unauthorized state-changing actions, privilege escalation.
**Mitigations.** Least-privilege tool allow-lists; separate read vs. write vs. external tools; require human approval (shadow mode) for high-impact actions; verify each action matches the declared objective.

## LLM07 | System Prompt Leakage | category: system_prompt_leak
**Risk.** The confidential system prompt (containing instructions, rules, sometimes secrets) is extracted by the attacker.
**Impact.** Reveals guardrail logic enabling targeted bypass; may leak embedded secrets.
**Mitigations.** Never store secrets in the system prompt; add an output leak detector comparing responses to the stored system prompt; flag and block extraction attempts; assume the prompt is discoverable and don't rely on its secrecy for security.

## LLM08 | Vector and Embedding Weaknesses | category: vector_weakness
**Risk.** Weaknesses in RAG/embedding pipelines allow poisoning, cross-tenant leakage, or retrieval of malicious content.
**Impact.** Indirect injection via retrieved content, data leakage across tenants.
**Mitigations.** Integrity-check ingested documents; per-tenant isolation of vector stores; access controls on retrieval; treat retrieved chunks as untrusted; monitor for anomalous embeddings.

## LLM09 | Misinformation | category: misinformation
**Risk.** The model produces confident but false information (hallucination) that users act on.
**Impact.** Bad decisions, reputational and legal harm.
**Mitigations.** Ground answers in retrieval with citations; measure faithfulness (RAGAS); communicate uncertainty; human review for high-stakes outputs.

## LLM10 | Unbounded Consumption | category: unbounded_consumption
**Risk.** Uncontrolled resource use (tokens, compute, tool calls) enables denial-of-wallet or denial-of-service.
**Impact.** Cost blowups, service degradation.
**Mitigations.** Rate limits and quotas per key; token/step budgets; circuit breakers; monitor consumption per user.
