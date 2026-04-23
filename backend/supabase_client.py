"""Thin wrapper around the Supabase Python SDK.

The worker uses the **service role key** so it can bypass RLS to write
into any user's tables. NEVER ship this key to the browser — it lives in
backend/.env on whatever host runs the worker.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    # python-dotenv is optional; env vars can also come from the shell.
    pass

from supabase import Client, create_client


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required env var: {name}. "
            f"Copy backend/.env.example → backend/.env and fill it in."
        )
    return value


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return a singleton Supabase client authed as service_role."""
    url = _required("SUPABASE_URL")
    key = _required("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


def storage_download(bucket: str, path: str, dest: Path) -> None:
    """Download an object from a Supabase Storage bucket to a local path."""
    client = get_client()
    blob = client.storage.from_(bucket).download(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
