"""Startup/database bootstrap helpers for smoother first-run UX."""

from __future__ import annotations

from threading import Lock

from django.core.management import call_command
from django.db import connection

_bootstrap_lock = Lock()
_bootstrapped = False


def ensure_schema() -> None:
    """Ensure DB schema exists before hitting DipTest queries.

    Automatically runs migrations once when the `lab_diptest` table is missing.
    """

    global _bootstrapped
    if _bootstrapped:
        return

    with _bootstrap_lock:
        if _bootstrapped:
            return

        table_names = connection.introspection.table_names()
        if "lab_diptest" not in table_names:
            call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)

        _bootstrapped = True
