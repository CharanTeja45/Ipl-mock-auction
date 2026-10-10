r"""
Import the prepared IPL player CSV into one Supabase auction room.

Run from D:\\ipl-mock-auction:
  .\venv\Scripts\python.exe import_ipl_players.py ROOMCODE

Optional for a NEW TEST ROOM only:
  .\venv\Scripts\python.exe import_ipl_players.py ROOMCODE --replace-available

The replace option deletes existing rows only when every existing player row is
still available and no sold_to/sold_price values exist. It refuses to delete
rows from a room that has sold/unsold/in-progress history.
"""
import argparse
import csv
import os
import tomllib
from supabase import create_client

CSV_PATH = os.path.join(os.path.dirname(__file__), "ipl_2026_players_supabase_import.csv")
SECRETS_PATH = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")

def get_credentials():
    if not os.path.exists(SECRETS_PATH):
        raise FileNotFoundError(
            f"Could not find {SECRETS_PATH}. Run this script from your project folder "
            "and make sure .streamlit/secrets.toml exists."
        )
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    url = secrets.get("SUPABASE_URL")
    key = secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("secrets.toml must contain SUPABASE_URL and SUPABASE_KEY.")
    return url, key

def read_players():
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def as_optional_int(value):
    return int(value) if value not in (None, "") else None

def as_optional_float(value):
    return float(value) if value not in (None, "") else None

def make_row(p, room_code):
    # Keep the auction state separate from the source classification:
    # every imported player begins as available in this mock auction.
    return {
        "room_code": room_code,
        "player_name": p["player_name"],
        "role": p["role"] or "Unknown",
        "nationality": (p["nationality"].strip() if p.get("nationality") and p["nationality"].strip() else "Unknown"),
        "base_price": float(p["base_price"]),
        "status": "available",
        "sold_to": None,
        "sold_price": None,
        "photo_url": p["photo_url"] or None,
        "batting_style": p["batting_style"] or None,
        "bowling_style": p["bowling_style"] or None,
        "matches": as_optional_int(p["matches"]),
        "runs": as_optional_int(p["runs"]),
        "batting_average": as_optional_float(p["batting_average"]),
        "strike_rate": as_optional_float(p["strike_rate"]),
        "highest_score": p["highest_score"] or None,
        "fifties": as_optional_int(p["fifties"]),
        "hundreds": as_optional_int(p["hundreds"]),
        "wickets": as_optional_int(p["wickets"]),
        "bowling_economy": as_optional_float(p["bowling_economy"]),
        "base_price_is_mock": p["base_price_is_mock"].strip().lower() == "true",
        "previous_team": p["previous_team"] or None,
        "squad_status": p["squad_status"] or None,
        "source_type": p["source_type"] or None,
        "bowling_style_group": p["bowling_style_group"] or None,
        "bowling_style_note": p["bowling_style_note"] or None,
        "source_season": p["source_season"] or None,
        "unsold_list_source": p["unsold_list_source"] or None,
        "auction_order": as_optional_int(p["auction_order"]),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room_code", help="Existing room code from your lobby")
    parser.add_argument(
        "--replace-available",
        action="store_true",
        help="For a NEW TEST ROOM only: replace sample players if none have auction history",
    )
    args = parser.parse_args()
    room_code = args.room_code.strip().upper()
    if not room_code:
        raise SystemExit("Room code cannot be empty.")

    url, key = get_credentials()
    supabase = create_client(url, key)
    source_players = read_players()
    existing_resp = (
        supabase.table("auction_player_pool")
        .select("id,player_name,status,sold_to,sold_price")
        .eq("room_code", room_code)
        .execute()
    )
    existing = existing_resp.data or []

    if args.replace_available and existing:
        unsafe = [
            p for p in existing
            if (str(p.get("status") or "").lower() != "available")
            or p.get("sold_to") is not None
            or p.get("sold_price") is not None
        ]
        if unsafe:
            raise SystemExit(
                "Safety stop: this room has non-available or sold-player history. "
                "No rows were deleted. Use a new test room instead."
            )
        # Delete only rows in this room and only after the safety check above.
        supabase.table("auction_player_pool").delete().eq("room_code", room_code).execute()
        existing = []

    existing_names = {
        str(p.get("player_name", "")).strip().casefold()
        for p in existing
    }
    to_insert = [
        make_row(p, room_code)
        for p in source_players
        if p["player_name"].strip().casefold() not in existing_names
    ]

    if not to_insert:
        print(f"No new players to insert for room {room_code}; existing rows were left unchanged.")
        return

    inserted = 0
    batch_size = 50
    for start in range(0, len(to_insert), batch_size):
        batch = to_insert[start:start + batch_size]
        supabase.table("auction_player_pool").insert(batch).execute()
        inserted += len(batch)

    print(f"Imported {inserted} players into room {room_code}.")
    print("All imported players start with status='available'.")
    print("Players with base_price_is_mock=true use the mock default ₹0.20 Cr.")
    print("Existing sold-player records and auction_state were not changed.")

if __name__ == "__main__":
    main()
