"""Create a teacher account in the local, git-ignored teachers.json file."""

import getpass
import json
import sys
from pathlib import Path

from app import TEACHERS_FILE, hash_password


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise SystemExit(f"Usage: {Path(sys.argv[0]).name} USERNAME")

    username = sys.argv[1].strip()
    password = getpass.getpass("Teacher password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if not password:
        raise SystemExit("Password cannot be empty")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    try:
        accounts = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        accounts = {}
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot read {TEACHERS_FILE}: {error}") from error

    if not isinstance(accounts, dict):
        raise SystemExit(f"{TEACHERS_FILE} must contain a JSON object")
    if username in accounts:
        raise SystemExit(f"Teacher account {username!r} already exists")

    accounts[username] = hash_password(password)
    TEACHERS_FILE.write_text(
        json.dumps(accounts, indent=2) + "\n", encoding="utf-8"
    )
    TEACHERS_FILE.chmod(0o600)
    print(f"Created teacher account {username!r} in {TEACHERS_FILE}")


if __name__ == "__main__":
    main()
