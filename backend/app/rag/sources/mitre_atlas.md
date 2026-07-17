# MITRE ATLAS — Adversarial Threat Landscape for AI Systems (condensed)

> Original condensed summaries of selected ATLAS tactics/techniques aligned to LLM/agent threats.

## AML.T0051 | LLM Prompt Injection | category: direct_injection
**Technique.** Adversary crafts prompts that cause the model to ignore prior instructions or perform unintended actions. Includes direct and indirect (via ingested content) variants.
**Defense.** Input validation and injection detection; instruction/data separation; least privilege on downstream actions.

## AML.T0054 | LLM Jailbreak | category: jailbreak
**Technique.** Adversary bypasses safety guardrails via role-play, obfuscation, or multi-step framing to elicit restricted behavior.
**Defense.** Constrained safety classifier; refusal on guardrail-removal personas; monitor for jailbreak patterns.

## AML.T0057 | LLM Data Leakage | category: sensitive_disclosure
**Technique.** Adversary extracts sensitive data (PII, secrets, training data) from the model via crafted queries.
**Defense.** Output filtering/redaction; membership-inference resistance; scope data access.

## AML.T0024 | Exfiltration via ML Inference API | category: sensitive_disclosure
**Technique.** Sensitive information is exfiltrated through the model's outputs or side channels.
**Defense.** Egress/output scanning; rate limiting; anomaly detection on queries.

## AML.T0018 | Manipulate AI Model (Poisoning) | category: data_poisoning
**Technique.** Adversary poisons training/fine-tuning/embedding data to implant backdoors or bias.
**Defense.** Trusted data pipelines; provenance; anomaly detection; sandbox untrusted contributions.

## AML.T0053 | LLM Plugin Compromise | category: excessive_agency
**Technique.** Adversary abuses model plugins/tools to perform unauthorized actions or reach external systems.
**Defense.** Least-privilege plugins; validate arguments; human approval on high-impact tools.
