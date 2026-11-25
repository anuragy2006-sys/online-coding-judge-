# CodeJudge AI — Project documentation (Aavishkar)

## Problem
Students get a bare "Wrong Answer" from judges and faculty cannot see *why* a class struggles. CodeJudge AI combines
secure automated assessment with personalised learning and faculty analytics.

## Architecture
Browser (Jinja pages + vanilla JS + Monaco) → FastAPI routers → services → SQLAlchemy (SQLite/PostgreSQL).
Executor runs submissions in a hardened subprocess sandbox. AI layer calls Claude when configured, else rule-based logic.

## Key algorithms
* **Scoring:** score = points × (Σ weight of passed cases ÷ Σ weight). Contest rank = points desc, then penalty (minutes to first AC + penalty × wrong tries) asc.
* **Weakness score (0–100, higher = weaker):** 50% failure rate + 35% attempted-but-unsolved problems + 15% retries before success, shrunk toward neutral when attempts < 4. Weak ≥ 55, Developing ≥ 30.
* **Roadmap:** topics ordered Weak → Developing → Not started → Strong; each has Easy→Medium→Hard steps whose completion comes from real accepted submissions.
* **Recommendations:** weak-topic boost + difficulty matched to the student's current tier + unfinished attempts.
* **Plagiarism:** normalise tokens (identifiers→ID, literals→NUM/STR, comments dropped) → 5-gram hashes → winnowing (window 4) → Dice similarity; starter-code fingerprints ignored.
* **XP:** first AC 20/40/80 (Easy/Med/Hard), daily activity 5, weekly streak 50, contest participation 30; levels need 100, 150, 200… XP.

## Data model additions
users(role, xp, bio, last_active_at) · problems(points, is_published, tags) · test_cases(weight) · submissions(score, contest_id, max_memory_kb, similarity_score) ·
xp_events · user_badges · contests · contest_problems · contest_participants · similarity_reports · tutor_messages · hint_usage.

## Demo script
1. Register as student → solve a problem (watch XP/badge toast) → dashboard heatmap.
2. Ask the tutor / hints / line-by-line on the problem page; open **My Learning** for weakness + roadmap.
3. Admin creates a contest; two students compete; show live leaderboard + timer.
4. Faculty dashboard → topic weakness → download class PDF → plagiarism compare.
