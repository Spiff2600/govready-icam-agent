# Why Claude

A rules engine can reliably detect simple conditions such as SMS MFA or permanent Global Administrator assignments, but it struggles to synthesize multi-step narratives across clouds. This demo intentionally includes cases like Tamara Osei's internal transfer, Jenny Tran's credential sharing, and Sandra Okafor's stale emergency access because they require evidence gathering plus explanation.

A smaller model could summarize one signal at a time, but frontier-class Claude is better suited for:

- combining Azure and AWS evidence into one cross-cloud risk story,
- preserving distinctions between facts, assumptions, and recommendations,
- following structured output instructions while using tools,
- producing executive and technical prose that remains grounded in deterministic evidence.

Claude is therefore used as the reasoning and communication layer, while deterministic Python handles data retrieval, scoring, and enforcement logic.
