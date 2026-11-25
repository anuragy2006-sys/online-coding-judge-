"""
Run once to set up the database with sample problems and an admin account.

Usage (from the project root):
    python seed_data.py
"""
import secrets
from app.database import engine, SessionLocal
from app import models
from app.migrations import run_migrations
from app.auth import hash_password
from app.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

run_migrations(engine)      # safe on both fresh and existing databases
db = SessionLocal()

# --- Admin user ---
admin = db.query(models.User).filter(models.User.username == DEFAULT_ADMIN_USERNAME).first()
if not admin:
    pw = DEFAULT_ADMIN_PASSWORD or secrets.token_urlsafe(12)
    admin = models.User(
        username=DEFAULT_ADMIN_USERNAME,
        email="admin@example.com",
        hashed_password=hash_password(pw),
        is_admin=True, role="admin",
    )
    db.add(admin)
    db.commit()
    print(f"Created admin user: admin@example.com / {pw}   <- save this password now (shown once)")
else:
    print("Admin user already exists, skipping.")


def add_problem(title, slug, description, constraints, difficulty, topic,
                 starter_code, test_cases, time_limit=2.0):
    existing = db.query(models.Problem).filter(models.Problem.slug == slug).first()
    if existing:
        print(f"Problem '{title}' already exists, skipping.")
        return
    problem = models.Problem(
        title=title, slug=slug, description=description, constraints=constraints,
        difficulty=difficulty, topic=topic, starter_code=starter_code,
        time_limit_seconds=time_limit,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    for input_data, expected_output, is_sample in test_cases:
        db.add(models.TestCase(
            problem_id=problem.id, input_data=input_data,
            expected_output=expected_output, is_sample=is_sample,
        ))
    db.commit()
    print(f"Created problem: {title}")


# --- Problem 1: Sum of Array ---
add_problem(
    title="Sum of Array",
    slug="sum-of-array",
    description=(
        "Given an integer n followed by n integers, print their sum.\n\n"
        "Read input from stdin: first line is n, second line has n space-separated integers.\n"
        "Print a single integer: the sum."
    ),
    constraints="1 <= n <= 10^5\n-10^9 <= each element <= 10^9",
    difficulty="Easy",
    topic="Arrays",
    starter_code=(
        "n = int(input())\n"
        "arr = list(map(int, input().split()))\n"
        "# write your solution below\n"
        "print(sum(arr))\n"
    ),
    test_cases=[
        ("5\n1 2 3 4 5", "15", True),
        ("3\n-1 -2 -3", "-6", True),
        ("1\n100", "100", False),
        ("4\n0 0 0 0", "0", False),
    ],
)

# --- Problem 2: Two Sum ---
add_problem(
    title="Two Sum",
    slug="two-sum",
    description=(
        "Given an array of integers and a target, print the 0-based indices of the two "
        "numbers that add up to the target (space-separated, smaller index first). "
        "Assume exactly one solution exists.\n\n"
        "Input: first line n, second line n integers, third line the target.\n"
        "Output: two indices separated by a space."
    ),
    constraints="2 <= n <= 10^4\nExactly one valid answer exists.",
    difficulty="Easy",
    topic="Hashing",
    starter_code=(
        "n = int(input())\n"
        "arr = list(map(int, input().split()))\n"
        "target = int(input())\n"
        "seen = {}\n"
        "for i, x in enumerate(arr):\n"
        "    need = target - x\n"
        "    if need in seen:\n"
        "        print(seen[need], i)\n"
        "        break\n"
        "    seen[x] = i\n"
    ),
    test_cases=[
        ("4\n2 7 11 15\n9", "0 1", True),
        ("3\n3 2 4\n6", "1 2", True),
        ("2\n3 3\n6", "0 1", False),
    ],
)

# --- Problem 3: Reverse a String ---
add_problem(
    title="Reverse a String",
    slug="reverse-a-string",
    description=(
        "Read a single line string and print it reversed."
    ),
    constraints="1 <= |s| <= 10^5",
    difficulty="Easy",
    topic="Strings",
    starter_code="s = input()\nprint(s[::-1])\n",
    test_cases=[
        ("hello", "olleh", True),
        ("racecar", "racecar", True),
        ("abcdef", "fedcba", False),
    ],
)

# --- Problem 4: Binary Search ---
add_problem(
    title="Binary Search",
    slug="binary-search",
    description=(
        "Given a sorted array of n integers and a target value, print the 0-based index "
        "of the target if found, otherwise print -1.\n\n"
        "Input: first line n, second line n sorted integers, third line target."
    ),
    constraints="1 <= n <= 10^6\narray is sorted ascending",
    difficulty="Medium",
    topic="Binary Search",
    starter_code=(
        "n = int(input())\n"
        "arr = list(map(int, input().split()))\n"
        "target = int(input())\n"
        "lo, hi = 0, n - 1\n"
        "ans = -1\n"
        "while lo <= hi:\n"
        "    mid = (lo + hi) // 2\n"
        "    if arr[mid] == target:\n"
        "        ans = mid\n"
        "        break\n"
        "    elif arr[mid] < target:\n"
        "        lo = mid + 1\n"
        "    else:\n"
        "        hi = mid - 1\n"
        "print(ans)\n"
    ),
    test_cases=[
        ("5\n1 3 5 7 9\n7", "3", True),
        ("5\n1 3 5 7 9\n4", "-1", True),
        ("1\n5\n5", "0", False),
    ],
)

# --- Problem 5: Valid Parentheses ---
add_problem(
    title="Valid Parentheses",
    slug="valid-parentheses",
    description=(
        "Given a string containing only the characters ()[]{}, print 'true' if the "
        "brackets are balanced and properly nested, otherwise print 'false'."
    ),
    constraints="0 <= |s| <= 10^4",
    difficulty="Medium",
    topic="Stack",
    starter_code=(
        "s = input()\n"
        "stack = []\n"
        "pairs = {')': '(', ']': '[', '}': '{'}\n"
        "ok = True\n"
        "for ch in s:\n"
        "    if ch in '([{':\n"
        "        stack.append(ch)\n"
        "    elif ch in ')]}':\n"
        "        if not stack or stack.pop() != pairs[ch]:\n"
        "            ok = False\n"
        "            break\n"
        "if stack:\n"
        "    ok = False\n"
        "print('true' if ok else 'false')\n"
    ),
    test_cases=[
        ("()[]{}", "true", True),
        ("(]", "false", True),
        ("([)]", "false", False),
        ("{[]}", "true", False),
    ],
)

# --- Problem 6: Fibonacci Number ---
add_problem(
    title="Fibonacci Number",
    slug="fibonacci-number",
    description="Given an integer n, print the n-th Fibonacci number (0-indexed: F(0)=0, F(1)=1).",
    constraints="0 <= n <= 40",
    difficulty="Easy",
    topic="Dynamic Programming",
    starter_code=(
        "n = int(input())\n"
        "a, b = 0, 1\n"
        "for _ in range(n):\n"
        "    a, b = b, a + b\n"
        "print(a)\n"
    ),
    test_cases=[
        ("0", "0", True),
        ("1", "1", True),
        ("10", "55", True),
        ("20", "6765", False),
    ],
)

db.close()
print("\nSeeding complete. Run the server with: uvicorn app.main:app --reload")
