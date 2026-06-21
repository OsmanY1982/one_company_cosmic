---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b11c9da246eaa2aacfce94adf18e4927_194384c6687c11f1a99c5254007bceed
    ReservedCode1: bQgwez8mvcj61rpTvUj850VENJiHBse1TmYt13JrL0YIXENj8fiIOOgrvegANv550bgA8pzloR3z0RRxV5CboHG2byfNNjVv1i1VW3wZOLzHteotvEvUBa+YbgaYOM+MsXzDZg+fWUwukXo7RHr0KbLcXh9RHxLfqZfjb6dsB0ukXKBMKc12oBaC4AE=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b11c9da246eaa2aacfce94adf18e4927_194384c6687c11f1a99c5254007bceed
    ReservedCode2: bQgwez8mvcj61rpTvUj850VENJiHBse1TmYt13JrL0YIXENj8fiIOOgrvegANv550bgA8pzloR3z0RRxV5CboHG2byfNNjVv1i1VW3wZOLzHteotvEvUBa+YbgaYOM+MsXzDZg+fWUwukXo7RHr0KbLcXh9RHxLfqZfjb6dsB0ukXKBMKc12oBaC4AE=
---

# Test Anthropic Skill

This is a test skill that uses the **Anthropic Skills format**.

## Purpose

Verify that the skill loader can:
1. Detect `metadata.yaml` in the skill directory
2. Parse it correctly
3. Read SKILL.md as plain body content (no YAML frontmatter)

## Instructions

When this skill is loaded, the agent should see this body text and the metadata from `metadata.yaml`.

### Key Verification Points

- Name should be `test-anthropic-skill`
- Description should match metadata.yaml
- Format flag should be `anthropic`
- Triggers should include `["test", "anthropic", "metadata"]`
*（内容由AI生成，仅供参考）*
