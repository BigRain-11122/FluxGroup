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

### Changelog
- 2026-09-23: initial rules.
