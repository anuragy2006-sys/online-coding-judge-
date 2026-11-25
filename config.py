"""
Central configuration for the Online Judge.
Change values here (or set environment variables) to configure the app.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Security ---
ENVIRONMENT = os.environ.get("JUDGE_ENV", "development")   # "production" enables strict checks
_DEFAULT_SECRET = "change-this-secret-key-in-production"
SECRET_KEY = os.environ.get("JUDGE_SECRET_KEY", _DEFAULT_SECRET)
if ENVIRONMENT == "production" and SECRET_KEY == _DEFAULT_SECRET:
    raise RuntimeError("JUDGE_SECRET_KEY must be set to a long random value when JUDGE_ENV=production")
SESSION_COOKIE_NAME = "judge_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
COOKIE_SECURE = os.environ.get("JUDGE_COOKIE_SECURE", "1" if ENVIRONMENT == "production" else "0") == "1"
MIN_PASSWORD_LENGTH = 8   # enforced for NEW passwords; existing hashes keep working

# --- Rate limiting (requests per window, per client IP) ---
RATE_LIMITS = {
    "auth":   (10, 60),     # login/register: 10 / minute
    "run":    (30, 60),     # custom run
    "submit": (20, 60),     # graded submissions
    "ai":     (20, 60),     # AI features
    "default": (240, 60),
}

# --- Sandbox ---
MAX_SOURCE_BYTES = 64 * 1024
MAX_STDIN_BYTES = 256 * 1024
MAX_PROCESSES = 64

# --- Database ---
DATABASE_URL = os.environ.get("JUDGE_DATABASE_URL", f"sqlite:///{BASE_DIR}/judge.db")

# --- Code execution sandbox limits ---
EXECUTION_TIMEOUT_SECONDS = 5          # wall-clock timeout per run
MEMORY_LIMIT_MB = 256                  # rlimit for the child process (Linux only)
MAX_OUTPUT_CHARS = 20000               # truncate huge stdout to protect the UI/DB

# Directory used for temporary compile/run files
TEMP_RUN_DIR = os.path.join(BASE_DIR, "runtime_tmp")
os.makedirs(TEMP_RUN_DIR, exist_ok=True)

# --- Extensions (installed packages/libraries) ---
# Java has no per-run package manager the way pip/apt do, so downloaded .jar
# files are cached here and added to the classpath for every compile/run.
JAVA_LIB_DIR = os.path.join(BASE_DIR, "javalibs")
os.makedirs(JAVA_LIB_DIR, exist_ok=True)
PACKAGE_INSTALL_TIMEOUT_SECONDS = 90   # installs can be slower than a code run

# --- AI Code Review ---
# If set, the AI service will call the Anthropic API for real reviews.
# If not set, a built-in heuristic reviewer is used instead (still useful!).
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
# Similarity (plagiarism) threshold, percent, above which a submission pair is flagged.
SIMILARITY_FLAG_THRESHOLD = float(os.environ.get("JUDGE_SIMILARITY_THRESHOLD", "80"))

# --- Admin bootstrap ---
# The first user ever created with this username is auto-promoted to admin
# on first run of seed_data.py. You can also promote manually in the DB.
DEFAULT_ADMIN_USERNAME = "admin"
# Set JUDGE_ADMIN_PASSWORD to choose it; otherwise seed_data.py generates a random one and prints it once.
DEFAULT_ADMIN_PASSWORD = os.environ.get("JUDGE_ADMIN_PASSWORD", "")
