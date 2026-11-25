# Testing report
Environment: Python 3.12, Ubuntu, gcc/g++ 13, OpenJDK 21. Command: `cd tests && python -m pytest -q` → **23 passed**.

| Area | Verified |
|---|---|
| Auth | registration validation, password policy, bcrypt login, cookie flags, wrong password, role-gated pages |
| Security | cross-origin POST blocked (403), login rate limit (429), JSON APIs return 401 when logged out, extension install admin-only, malformed JSON → 400, unsupported language → 422 |
| Sandbox (manual attack run) | infinite loop → TLE; 1 GB allocation → MLE (C++/Python/Java); `os.system`, `socket`, `fork`, `#include "/etc/passwd"`, `Runtime.exec` → rejected; output flood capped; environment secrets not visible; compile errors reported |
| Judging | AC in Python/C/C++/Java; WA with partial score (50/100); TLE; compile error; hidden cases never leak in messages or pages |
| Learning | hints (3 levels), tutor chat + history, line-by-line, weakness = "Weak" after 4 failed attempts, roadmap focus, recommendations |
| Gamification | XP awarded once per problem, badge unlock, streak, heatmap |
| Similarity | renamed-variable copy flagged ≥80%, different approach <40%, report page |
| Contests | create, run, join, scoring + penalty, live leaderboard JSON, closed-contest submissions rejected, upcoming problems hidden, history |
| Faculty/Admin | analytics page, student page, class & student PDFs (valid `%PDF`), plagiarism list/compare, problem/test-case CRUD, unpublish/delete |
| Migration | original `judge.db` (4 users, 6 problems, 1 submission) upgraded in place; data intact; second run is a no-op |
| Server | real `uvicorn` start, `/health`, pages and static assets return 200 |

## Not verified here (be transparent in your demo)
* Claude-powered AI paths (need an API key); the rule-based fallbacks are what was tested.
* Visual/browser rendering (dark/light, mobile) and Monaco editor were not exercised in a real browser — open the app once and click through before the exhibition.
* `unshare -n` network isolation depends on the host kernel; `/health` reports whether it is active.
* Memory usage (MB) display is only filled when measurable; limits are enforced regardless.
