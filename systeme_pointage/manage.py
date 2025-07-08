#!/usr/bin/env python
import sys
import os

def main():
    """Run administrative tasks."""
    # Ajout du dossier racine (contenant manage.py) dans sys.path
    current_path = os.path.dirname(os.path.abspath(__file__))
    if current_path not in sys.path:
        sys.path.insert(0, current_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "systeme_pointage.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
