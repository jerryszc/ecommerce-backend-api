# HARNESS: Python & PostgreSQL Development Environment

## 1. Environment & Terminal Constraints
- **Operating System:** Windows 10.
- **Allowed Editors:** Visual Studio Code.
- **Mandatory Terminal:** Git Bash.
- **Path & Command Standards:** All file paths and terminal instructions must use Bash-compatible syntax, utilizing forward slashes (/) and POSIX commands. Backslashes (\) are strictly forbidden to prevent execution errors in scripts or console commands.

## 2. Code Standards & Version Control
- **Language:** Python 3.10+ with strict Type Hints and rigorous adherence to PEP 8.
- **Version Control:** Git and GitHub. Every relevant feature must be versioned with clean and descriptive commits.
- **Encoding:** Files must be strictly encoded in UTF-8.

## 3. Mandatory Security Layer
- **Credentials:** Zero hardcoded passwords or connection strings. Mandatory use of environment variables via `pydantic-settings` and `.env`.
- **Database Integrity & ORM:** Mandatory use of SQLModel / SQLAlchemy session management, explicit transaction handling, and parameterized queries handled securely by the ORM layer to prevent SQL Injection.