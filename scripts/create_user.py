import os
import sys
from pathlib import Path


def setup_django() -> None:
    # Ensure project root is on sys.path (script is in scripts/)
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    import django  # noqa: WPS433 (runtime import needed after env var)

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
        import getpass  # noqa: WPS433

        pwd = getpass.getpass("Password: ").strip()
    except Exception:  # pragma: no cover - fallback for rare terminals
        pwd = prompt("Password: ")
    return pwd


def main() -> int:
    setup_django()

    from users.models import User  # noqa: WPS433 (import after django.setup)

    print("=== Create User ===")
    email = prompt("Email: ")
    if not email:
        print("Error: Email is required.")
        return 1

    # Check if user exists (case-insensitive)
    if User.objects.filter(email__iexact=email).exists():
        print(f"Error: A user with email '{email}' already exists.")
        return 1

    password = prompt_password()
    if len(password) < 4:
        print("Error: Password must be at least 4 characters long.")
        return 1

    first_name = prompt("First name: ")
    if not first_name:
        print("Error: First name is required.")
        return 1

    last_name = prompt("Last name: ")
    if not last_name:
        print("Error: Last name is required.")
        return 1

    specialty = prompt("Specialty (optional): ", required=False)

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

