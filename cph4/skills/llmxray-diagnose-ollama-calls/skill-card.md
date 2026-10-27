## Description:

Helps developers diagnose slow, truncated, or inefficient local Ollama calls using LLMxRay's read-only diagnostic tools.

This skill is ready for commercial/non-commercial use.

## Publisher:

[lognebudo](https://clawhub.ai/user/lognebudo)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and engineers use this skill to inspect their own Ollama calls, identify prompt-cache, context, speed, and memory issues, and choose adjustments to test.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Installing the npm package executes third-party code.

Mitigation: Use a pinned or otherwise verified llmxray version in sensitive environments.

Risk: Prompts routed through the local proxy are recorded locally and may contain secrets.

Mitigation: Route only traffic suitable for local logging; avoid sending secret-bearing prompts through the proxy.

## Reference(s):

- [LLMxRay project homepage](https://github.com/LogneBudo/llmxray)
- [LLMxRay ClawHub release](https://clawhub.ai/lognebudo/skills/llmxray-diagnose-ollama-calls)

## Skill Output:

**Output Type(s):** [Text, Guidance, Configuration instructions, Shell commands]

**Output Format:** [Plain text and Markdown]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Read-only diagnostic findings and suggested fixes; no settings are changed by the tools.]

## Skill Version(s):

0.8.6 (source: skill frontmatter and ClawHub release)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
