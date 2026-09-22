# Token Smart installed

Save avoidable work, not required work.

This is a **three-layer token economy** skill. Only the layer you need is read; layer 1 covers everyday work.

| Layer | What it solves | When |
| --- | --- | --- |
| 1. Live | Less reading, fewer repeated checks, less narration | Default, every task |
| 2. Storage | Old history cold-stored, not loaded by default, retrieved verbatim on demand | Slow or failing tasks; looking back at old records |
| 3. Evolution | Offline review of past sessions; consolidates skills and memory | Nightly or on-demand self-improvement |

**How it works**: read files and skills on demand; reuse existing evidence and implementations; prefer scriptable checks; stop repeating checks once they pass; add reasoning, review, and subtasks only when they pay off.

**How it feels**: fewer progress reports, results first, no heavyweight process for small tasks, long tasks resume from verified progress. Requested analysis, full code, and required tests are preserved.

On-demand by default. Type `$token-smart` in Codex or `/token-smart` in Claude Code, or just say “use Token Smart for this one”. Installing with `--activate` appends a short rule to the host's instruction file for later sessions; it does not change model or quota settings. If the current session has not discovered the new skill yet, start a new session.

Say “expand this one” to add detail, or “skip Token Smart mode this time” to override the preference for one turn. To uninstall the skill and its unmodified standing rule, rerun the installer with the same target and custom paths plus `--uninstall`, without `--activate`.

This is a working-method and storage convention, not a compression algorithm, quota unlock, or fixed discount. Savings depend on the task, context, model, and host; **this pack states no controlled saving percentage**.
