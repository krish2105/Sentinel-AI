# OWASP Top 10 for Agentic Applications (ASI)

> Original concise summaries. The Agentic Top 10 extends the LLM Top 10: once a model can *act*, language-layer manipulation becomes real-world consequence.

## ASI01 | Agent Goal Hijacking | category: goal_hijacking
**Risk.** An attacker redirects the agent's objective mid-task — prompt injection becomes goal manipulation. The agent keeps its tools and credentials but now pursues the attacker's aim.
**Impact.** Data exfiltration, phishing, unauthorized transactions performed by a trusted agent.
**Mitigations.** Pin the declared objective; have a judge verify every planned action aligns with it; require a human gate on objective changes; log intent drift.

## ASI02 | Tool Misuse and Exploitation | category: excessive_agency
**Risk.** The agent is manipulated into misusing legitimate tools, or tools with weak input validation are exploited through the agent.
**Impact.** Unauthorized actions, injection into downstream tools.
**Mitigations.** Least-privilege scoping per tool; validate tool arguments; allow-list actions; shadow-mode approval on write/external tools.

## ASI03 | Identity and Privilege Abuse | category: privilege_abuse
**Risk.** Agents operate with broad or ambient credentials; a compromise inherits all of them (confused-deputy).
**Impact.** Privilege escalation, lateral movement.
**Mitigations.** Per-action scoped credentials; short-lived tokens; separate agent identity from user identity; deny privilege reuse across contexts.

## ASI04 | Resource Overconsumption | category: unbounded_consumption
**Risk.** Autonomous loops consume unbounded compute/tool-calls (denial-of-wallet), possibly triggered adversarially.
**Impact.** Cost and availability damage.
**Mitigations.** Step/token/tool budgets; loop detection; circuit breakers; per-agent quotas.

## ASI05 | Memory and Context Poisoning | category: data_poisoning
**Risk.** Attacker writes a malicious 'fact' or instruction into the agent's persistent memory, corrupting behavior for future turns or other users.
**Impact.** Persistent compromise, cross-user contamination.
**Mitigations.** Treat memory writes as untrusted; validate before persisting; sandbox and scope memory per user; provenance tags; expire unverified memories.

## ASI06 | Cascading and Multi-Agent Failures | category: cascading_failure
**Risk.** In multi-agent systems, one compromised or erroneous agent propagates failure/injection to others.
**Impact.** System-wide compromise from a single weak link.
**Mitigations.** Isolate agent contexts; validate inter-agent messages; blast-radius limits; circuit breakers between agents.

## ASI07 | Insufficient Human Oversight | category: human_oversight
**Risk.** High-impact actions execute with no human in the loop where one is warranted.
**Impact.** Irreversible actions taken autonomously.
**Mitigations.** Human-approval gates on high-risk actions; interrupt/resume checkpoints; clear escalation paths.

## ASI08 | Deceptive Behaviors and Misalignment | category: misalignment
**Risk.** The agent behaves deceptively or pursues misaligned instrumental goals.
**Impact.** Loss of trust, unsafe autonomous behavior.
**Mitigations.** Independent judge/monitor; interpretable action logs; alignment evals.

## ASI09 | Supply Chain of Tools and Skills | category: supply_chain
**Risk.** Third-party tools, MCP servers, or agent skills are malicious or compromised.
**Impact.** Backdoored actions, data theft through trusted integrations.
**Mitigations.** Vet and pin tools/skills; verify signatures; scan MCP servers; least-privilege per integration.

## ASI10 | Insecure Agent Communication | category: insecure_comms
**Risk.** Inter-agent or agent-to-tool channels lack authentication/integrity, enabling spoofing or tampering.
**Impact.** Message forgery, man-in-the-middle between agents.
**Mitigations.** Mutual authentication; signed/encrypted messages; validate message provenance.
