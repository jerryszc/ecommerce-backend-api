# HARNESS: Python & PostgreSQL Development Environment

## 1. Environment & Terminal Constraints
- **Operating System:** Windows 10.
- **Allowed Editors:** Visual Studio Code (primary) and IDLE (for quick syntax testing).
- **Mandatory Terminal:** Git Bash.
- **Path & Command Standards:** All file paths and terminal instructions must use Bash-compatible syntax, utilizing forward slashes (/) and POSIX commands. Backslashes (\) are strictly forbidden to prevent execution errors in scripts or console commands.

## 2. Code Standards & Version Control
- **Language:** Python 3.10+ with strict Type Hints and rigorous adherence to PEP 8.
- **Version Control:** Git and GitHub. Every relevant feature must be versioned with clean and descriptive commits.
- **Encoding:** Files must be strictly encoded in UTF-8. The use of accents or special characters in source code comments or strings is strictly prohibited to prevent decoding errors in Windows.

## 3. Mandatory Security Layer
- **Credentials:** Zero hardcoded passwords or connection strings. Mandatory use of environment variables via `python-dotenv`.
- **Database Integrity:** Explicit transaction management in PostgreSQL (`commit`/`rollback`) wrapped in exception blocks (`try/except/finally`) using context managers (`with`).
- **SQL Injection Prevention:** Strictly forbidden to concatenate variables directly into SQL queries. Mandatory use of parameterized queries with `psycopg2`.