#!/usr/bin/env python3
"""Fetch The Firmware Hub's catalogue and trim it to what the seer needs: src/data/firmwares.json, and the day it was
read in src/data/asof.txt (build.py prints that at the foot of the page). Then run build.py.

The hub asks that catalog.json be read at most once a day (https://thefirmwarehub.com/kb/#catalog): the scheduled build
in .github/workflows/refresh.yml does exactly that. The list is the hub's, CC BY 4.0; each description is its maker's."""
import json, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://thefirmwarehub.com/catalog.json"
DATA = Path(__file__).resolve().parent / "src" / "data"
FEWEST = 150   # fewer firmwares than this is a broken catalogue, not a real one: keep the list we have


def trim(f):
    """One firmware as the seer reads it. The short keys keep the page small: the list is inlined in it."""
    kind = f.get("kind") or "other"
    return {"n": f["name"], "a": f.get("author") or "", "r": f.get("repo") or "",
            "k": kind[0] if isinstance(kind, list) else kind, "w": f.get("what") or "",
            "am": int(bool(f.get("ambient"))), "vi": int(bool(f.get("vintage"))),
            "s": int(f.get("stars") or 0), "i": int(f.get("installs") or 0), "p": f.get("play") or "",
            "b": int(bool(f.get("beta"))), "id": f.get("product") or "", "v": f.get("version") or ""}


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "catalog-refresh/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        cat = json.load(r)
    fws = [trim(f) for f in cat["firmwares"] if f.get("name")]
    if len(fws) < FEWEST:
        sys.exit(f"refresh: only {len(fws)} firmwares in the catalogue: left the list as it was")
    if not any(f["n"] == "AISLING" for f in fws):
        sys.exit("refresh: no AISLING in the catalogue, and the Tilt switch needs it: left the list as it was")
    path = DATA / "firmwares.json"
    old = {f["n"] for f in json.loads(path.read_text())} if path.exists() else set()
    new = {f["n"] for f in fws}
    path.write_text(json.dumps(fws, ensure_ascii=False, separators=(",", ":")) + "\n")
    # the hub's own date for the list ("2026-11-15 12:01 UTC"), or today if it gives none
    try:
        day = datetime.strptime(cat.get("updated", "")[:10], "%Y-%m-%d")
    except ValueError:
        day = datetime.now(timezone.utc)
    (DATA / "asof.txt").write_text(f"{day.day} {day:%B %Y}\n")
    print(f"refresh: {len(fws)} firmwares as of {day.day} {day:%B %Y}"
          + (f"; new: {', '.join(sorted(new - old))}" if old and new - old else "")
          + (f"; gone: {', '.join(sorted(old - new))}" if old - new else ""))


if __name__ == "__main__":
    main()
