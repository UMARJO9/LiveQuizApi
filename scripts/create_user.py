import argparse
import os
import sys
from pathlib import Path


def setup_django() -> None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    import django

    django.setup()


def prompt(prompt_text: str, required: bool = True) -> str:
    try:
        value = input(prompt_text).strip()
    except EOFError:
        value = ""
    if required and not value:
        return ""
    return value


def prompt_password() -> str:
    try:
        import getpass

        pwd = getpass.getpass("Password: ").strip()
    except Exception:
        pwd = prompt("Password: ")
    return pwd


def parse_args():
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("--email", "-e", help="User email")
    parser.add_argument("--password", "-p", help="User password")
    parser.add_argument("--first-name", "-f", help="First name")
    parser.add_argument("--last-name", "-l", help="Last name")
    parser.add_argument("--specialty", "-s", default="", help="Specialty (optional)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_django()

    from users.models import User

    print("=== Create User ===")

    # Use args or prompt interactively
    email = args.email or prompt("Email: ")
    if not email:
        print("Error: Email is required.")
        return 1

    if User.objects.filter(email__iexact=email).exists():
        print(f"Error: A user with email '{email}' already exists.")
        return 1

    password = args.password or prompt_password()
    if len(password) < 4:
        print("Error: Password must be at least 4 characters long.")
        return 1

    first_name = args.first_name or prompt("First name: ")
    if not first_name:
        print("Error: First name is required.")
        return 1

    last_name = args.last_name or prompt("Last name: ")
    if not last_name:
        print("Error: Last name is required.")
        return 1

    specialty = args.specialty or prompt("Specialty (optional): ", required=False)

    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        specialty=specialty,
    )

    print("User successfully created:")
    print(f"ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Name: {user.first_name} {user.last_name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nAborted by user.")
        raise SystemExit(130)

