# RULES.md — 顶层协作规则

Applies to every line: gaming / quant / media.
If a line README conflicts with this file, this file wins.

---

## 1. Onboarding order (for any human or AI)

Read in this exact order before writing anything:
1. `/README.md`
2. `/BRAND.md`
3. `/docs/philosophy.md`
4. `/RULES.md` (this file)
5. The target line's own `README.md`

Never skip to coding. Never invent context.

---

## 2. Naming rules

- File and directory names: **English only, no spaces, no Chinese, no special chars**.
- Use kebab-case for files (`backtest-runner.py`), PascalCase for classes, UPPER for constants.
- Do NOT name files or folders after people, agents, sessions, or task IDs.
- Product/sub-brand names must follow `BRAND.md` section 7 and be registered there before use.
- **Legacy exception (2026-09-23)**: established subsidiaries keep their internal naming systems
  under their own charters — gaming/MiniGame governs its Chinese doc system by its own
  09号§7 naming law (grandfathered). English-only naming governs group-layer files and any
  new line / product / file created inside this repo after this rule.

---

## 3. Code rules

- No Chinese in code comments, identifiers, or strings that ship. English only.
- Every script must be runnable from its own directory with a one-line command documented in the line README.
- No secrets, tokens, API keys in code. Put them in `.env` (gitignored).
- Test before declaring done: run it, read the output, do not assume.

---

## 4. Directory convention for every line

```
<line>/
├── README.md          <- line identity, stack, rules, run commands
├── src/               <- source code
├── data/              <- input datasets (gitignored if large)
├── output/            <- generated artifacts (gitignored)
├── docs/              <- line-specific notes
└── tests/             <- tests
```

Create these as needed. Do not nest arbitrary folders without a reason.

---

## 5. Red lines (from philosophy.md)

- No extractive attention farming / dopamine-max content.
- No fake need, no planned obsolescence.
- AI extends the human; it does not replace their judgment.
- Build for the decade, not the quarter.
- When in doubt, choose the option that survives the origin test: *why did we start?*

---

## 6. Change control

- Brand names: only changed via `BRAND.md`.
- Culture: only changed via `/docs/philosophy.md`.
- These rules: edit this file and note the date in the changelog below.
- Group ↔ subsidiary governance: see `/docs/governance.md`（边界/拓扑/生命周期/指挥/记忆/安全）.

---

## 7. CEO order trigger (2026-09-23 user order)

- `/CEO` at the start of a user message in any AI session on any machine = a formal CEO order (用户令).
- The receiving session must treat it as highest priority, record it in that company's order ledger (BigMoney: `quant/bigmoney/fleet/orders/`; MiniGame: 《用户限制登记簿》 U-rows per its own protocol), commit/push, then execute or dispatch, and close the loop with a receipt.
- Headless loops receive orders through their existing git channels (orders ledger / inbox / task tickets), not this trigger.
- A CEO order outranks everything: fix-red queues, tasks, and autonomous rounds.

### Changelog
- 2026-09-23: initial rules.
- 2026-09-23: added §7 CEO order trigger `/CEO` (user order).
- 2026-09-23: governance reference added (§6).
- 2026-09-23: added §2 legacy-exception clause — subsidiary internal naming systems (MiniGame Chinese docs per its 09号§7) grandfathered; English-only governs group-layer + new files.
