# Workflow doc template

Every workflow doc uses the same six sections, in this order. The n8n canvas carries the same content as sticky notes: one overview note, then one note per section of nodes.

```
# WP · NN Name

> One sentence: what the workflow does and where it sits in the chain.

## 1. Inputs
Where the data comes from (trigger, Notion database, filter) and which fields are read.

## 2. How the nodes work together
| # | Section (sticky note) | Nodes | What happens | Why this way |

## 3. Outputs
What is written where (Notion fields, statuses, messages), and what the next workflow picks up.

## 4. Logic and decisions
The rules, thresholds and trade-offs, with the alternative that was rejected and why.

## 5. Failure modes and recovery
| What breaks | What you see | What the workflow does | What you do |

## 6. Settings you can change
Config node values, with safe ranges.

## Changelog
vN · date · what changed · why (link to the decision log)
```

**Sticky notes in n8n:**
- **Note · 0 Overview:** Purpose, Input, Output, Flow in one line, Models, Runtime.
- **Notes 1…n:** one per section, each with In, Nodes, Logic, Why and Fails when.
- **Long workflows** (30, 40) get 5–6 notes; short ones get 2–3.
