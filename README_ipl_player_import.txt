IPL 2026 mock-auction import files

Files:
- ipl_2026_players_supabase_import.csv: normalized 327-player import dataset
- ipl_2026_player_import_schema.sql: adds metadata columns to auction_player_pool
- import_ipl_players.py: imports into a selected room without changing auction_state or sold records

Price policy:
- Base prices are stored in crore units (for example, 0.75 means ₹75 lakh).
- Where the source file had no price, the dataset uses 0.20 Cr and sets base_price_is_mock=true.
- Source-listed prices are converted from lakh/crore text into crore numbers.
- All players, including the source-listed unsold players, start as status='available' for the mock auction.
- Career stats and photos are blank, not fabricated.

Before using:
1. Copy the CSV and Python script into D:\ipl-mock-auction.
2. Run the SQL file in Supabase SQL Editor.
3. Create a NEW test room in your app.
4. In the project terminal, run:
   .\venv\Scripts\python.exe -m pip install supabase
5. Get the room code from the lobby, then run:
   .\venv\Scripts\python.exe import_ipl_players.py ROOMCODE --replace-available

The replace option is intended only for a new test room. It checks that all existing rows
are still available and no sold_to/sold_price values exist before deleting sample rows.
If any player has auction history, it refuses to delete anything.

The script reads SUPABASE_URL and SUPABASE_KEY from .streamlit/secrets.toml.
Do not paste or share that file.
