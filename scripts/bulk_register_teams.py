#!/usr/bin/env python3
"""
Bulk register teams to ExploitFarm via API.

Features:
- Template-based generation for host/name/short with {i}, {j}
- Inclusive range or explicit list for indices
- Optional skip list (e.g., your own team id)
- Existing-host dedupe (by default)
- Batch POST to /api/teams
- Dry-run mode

Default base URL: http://localhost:5050/api
If authentication is enabled on server, pass --password to obtain a Bearer token.
"""

from __future__ import annotations

import argparse
import itertools
import json
from typing import Iterable, List, Optional, Set, Dict

import requests


def chunked(seq: List[dict], n: int) -> Iterable[List[dict]]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def login(base_url: str, password: Optional[str]) -> Optional[str]:
    if not password:
        return None
    url = base_url.rstrip("/") + "/login"
    data = {"grant_type": "password", "username": "user", "password": password}
    r = requests.post(url, data=data, timeout=15)
    if r.status_code != 200:
        raise SystemExit(f"Login failed: {r.status_code} {r.text}")
    token = r.json().get("access_token")
    if not token:
        raise SystemExit("Login OK but no access_token in response")
    return token


def get_existing_hosts(base_url: str, headers: Dict[str, str]) -> Set[str]:
    url = base_url.rstrip("/") + "/teams"
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 401:
        raise SystemExit("Unauthorized. Provide --password or disable auth on server.")
    r.raise_for_status()
    try:
        arr = r.json()
    except Exception:
        raise SystemExit(f"Invalid JSON from {url}: {r.text[:200]}")
    return {t["host"] for t in arr}


def build_teams(
    host_t: str,
    name_t: Optional[str],
    short_t: Optional[str],
    i_vals: List[int],
    j_vals: Optional[List[int]],
) -> List[dict]:
    teams: List[dict] = []
    if j_vals:
        for i, j in itertools.product(i_vals, j_vals):
            teams.append(
                {
                    "host": host_t.format(i=i, j=j),
                    "name": (name_t.format(i=i, j=j) if name_t else None),
                    "short_name": (short_t.format(i=i, j=j) if short_t else None),
                }
            )
    else:
        for i in i_vals:
            teams.append(
                {
                    "host": host_t.format(i=i),
                    "name": (name_t.format(i=i) if name_t else None),
                    "short_name": (short_t.format(i=i) if short_t else None),
                }
            )
    return teams


def main():
    ap = argparse.ArgumentParser(description="Bulk register teams to ExploitFarm")
    ap.add_argument(
        "--base-url",
        default="http://localhost:5050/api",
        help="API base URL (e.g. http://host:5050/api)",
    )
    ap.add_argument("--password", help="Server password if authentication is enabled")
    ap.add_argument(
        "--host-template",
        required=True,
        help="Host template with {i},{j}. Example: 10.60.{i}.1",
    )
    ap.add_argument(
        "--name-template",
        help="Name template with {i},{j}. Example: Team {i}",
    )
    ap.add_argument(
        "--short-template",
        help="Short name template with {i},{j}. Example: T{i}",
    )

    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument(
        "--i-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Inclusive range for i",
    )
    grp.add_argument("--i-list", nargs="+", type=int, help="Explicit list for i")

    ap.add_argument(
        "--j-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Optional inclusive range for j",
    )
    ap.add_argument("--j-list", nargs="+", type=int, help="Optional explicit list for j")
    ap.add_argument(
        "--skip",
        nargs="*",
        type=int,
        default=[],
        help="Values of i to skip (e.g. your own team id)",
    )
    ap.add_argument("--batch-size", type=int, default=200, help="POST batch size")
    ap.add_argument("--dry-run", action="store_true", help="Print JSON and exit")
    ap.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Do not fetch and remove already existing hosts",
    )
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    token = login(base, args.password) if args.password else None
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    i_vals = (
        list(range(args.i_range[0], args.i_range[1] + 1))
        if args.i_range
        else list(args.i_list)
    )
    i_vals = [i for i in i_vals if i not in set(args.skip)]
    j_vals = (
        list(range(args.j_range[0], args.j_range[1] + 1))
        if args.j_range
        else (list(args.j_list) if args.j_list else None)
    )

    teams = build_teams(
        args.host_template, args.name_template, args.short_template, i_vals, j_vals
    )

    # Clean None fields and internal duplicates
    cleaned, seen = [], set()
    for t in teams:
        t = {k: v for k, v in t.items() if v is not None}
        if t["host"] in seen:
            continue
        seen.add(t["host"])
        cleaned.append(t)

    if args.dry_run:
        print(json.dumps(cleaned, indent=2, ensure_ascii=False))
        print(f"Would send {len(cleaned)} teams")
        return

    to_add = cleaned
    if not args.no_dedupe:
        existing = get_existing_hosts(base, headers)
        to_add = [t for t in cleaned if t["host"] not in existing]

    if not to_add:
        print("Nothing to add")
        return

    url = base + "/teams"
    ok = 0
    for chunk in chunked(to_add, args.batch_size):
        r = requests.post(
            url,
            headers={**headers, "Content-Type": "application/json"},
            json=chunk,
            timeout=60,
        )
        if r.status_code != 200:
            print(f"Batch failed: {r.status_code} {r.text}")
            continue
        resp = r.json()
        ok += len(resp.get("response", [])) if isinstance(resp, dict) else 0

    print(f"Created: {ok}, Skipped/Failed: {len(to_add) - ok}")


if __name__ == "__main__":
    main()

