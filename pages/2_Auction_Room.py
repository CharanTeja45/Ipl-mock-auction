import csv
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import streamlit as st
from supabase import create_client
# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="IPL Mock Auction - Auction Room",
    page_icon="🏏",
    layout="wide",
)
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top left, #172e50, transparent 55%),
        #0b1020;
    color: #ffffff;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}
h1, h2, h3, p, label {
    color: white;
}
div.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 700;
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.06);
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)
# =========================================================
# CONSTANTS AND IPL TEAMS
# =========================================================
STARTING_PURSE = Decimal("120.00")
BID_INCREMENT = Decimal("0.05")
BIDDING_SECONDS = 10
ANNOUNCEMENT_SECONDS = 3
RESULT_SECONDS = 2
TEAMS = {
    "CSK": "Chennai Super Kings",
    "MI": "Mumbai Indians",
    "RCB": "Royal Challengers Bengaluru",
    "KKR": "Kolkata Knight Riders",
    "SRH": "Sunrisers Hyderabad",
    "RR": "Rajasthan Royals",
    "DC": "Delhi Capitals",
    "PBKS": "Punjab Kings",
    "GT": "Gujarat Titans",
    "LSG": "Lucknow Super Giants",
}
TEAM_COLORS = {
    "CSK": "#F9CD05",
    "MI": "#1976D2",
    "RCB": "#D32F2F",
    "KKR": "#8E44AD",
    "SRH": "#F57C00",
    "RR": "#E91E63",
    "DC": "#2196F3",
    "PBKS": "#D32F2F",
    "GT": "#26A69A",
    "LSG": "#26C6DA",
}
# =========================================================
# PLAYER DATASET
# =========================================================
# Keep this CSV in the project root beside app.py. A new room imports it
# automatically the first time someone opens that room's auction page.
PLAYER_CSV_PATH = Path(__file__).resolve().parent.parent / "ipl_2026_all_teams_players_with_unsold.csv"
DEFAULT_BASE_PRICE = Decimal("0.20")  # mock default, in crore

OVERSEAS_COUNTRIES = {'Dewald Brevis': 'South Africa', 'Jamie Overton': 'England', 'Noor Ahmad': 'Afghanistan', 'Nathan Ellis': 'Australia', 'Akeal Hosein': 'West Indies', 'Matt Henry': 'New Zealand', 'Matthew Short': 'Australia', 'Zakary Foulkes': 'New Zealand', 'Ryan Rickelton': 'South Africa', 'Mitchell Santner': 'New Zealand', 'Corbin Bosch': 'South Africa', 'Trent Boult': 'New Zealand', 'Allah Ghazanfar': 'Afghanistan', 'Will Jacks': 'England', 'Sherfane Rutherford': 'West Indies', 'Quinton de Kock': 'South Africa', 'Sunil Narine': 'West Indies', 'Rovman Powell': 'West Indies', 'Cameron Green': 'Australia', 'Matheesha Pathirana': 'Sri Lanka', 'Mustafizur Rahman': 'Bangladesh', 'Finn Allen': 'New Zealand', 'Tim Seifert': 'New Zealand', 'Rachin Ravindra': 'New Zealand', 'Phil Salt': 'England', 'Tim David': 'Australia', 'Romario Shepherd': 'West Indies', 'Jacob Bethell': 'England', 'Josh Hazlewood': 'Australia', 'Nuwan Thushara': 'Sri Lanka', 'Jacob Duffy': 'New Zealand', 'Jordan Cox': 'England', 'Marcus Stoinis': 'Australia', 'Azmatullah Omarzai': 'Afghanistan', 'Marco Jansen': 'South Africa', 'Mitchell Owen': 'Australia', 'Xavier Bartlett': 'Australia', 'Lockie Ferguson': 'New Zealand', 'Cooper Connolly': 'Australia', 'Ben Dwarshuis': 'Australia', 'Jos Buttler': 'England', 'Kagiso Rabada': 'South Africa', 'Rashid Khan': 'Afghanistan', 'Glenn Phillips': 'New Zealand', 'Jason Holder': 'West Indies', 'Luke Wood': 'England', 'Tom Banton': 'England', 'Lhuan-Dre Pretorius': 'South Africa', 'Shimron Hetmyer': 'West Indies', 'Jofra Archer': 'England', 'Kwena Maphaka': 'South Africa', 'Nandre Burger': 'South Africa', 'Sam Curran': 'England', 'Adam Milne': 'New Zealand', 'Pat Cummins': 'Australia', 'Travis Head': 'Australia', 'Heinrich Klaasen': 'South Africa', 'Kamindu Mendis': 'Sri Lanka', 'Brydon Carse': 'England', 'Eshan Malinga': 'Sri Lanka', 'Liam Livingstone': 'England', 'Jack Edwards': 'Australia', 'Aiden Markram': 'South Africa', 'Matthew Breetzke': 'South Africa', 'Nicholas Pooran': 'West Indies', 'Mitchell Marsh': 'Australia', 'Josh Inglis': 'Australia', 'Anrich Nortje': 'South Africa', 'Wanindu Hasaranga': 'Sri Lanka', 'Tristan Stubbs': 'South Africa', 'Mitchell Starc': 'Australia', 'Dushmantha Chameera': 'Sri Lanka', 'Pathum Nissanka': 'Sri Lanka', 'Ben Duckett': 'England', 'David Miller': 'South Africa', 'Lungi Ngidi': 'South Africa', 'Kyle Jamieson': 'New Zealand'}


def parse_base_price(value):
    """Convert values such as '30 lakh' or '1.50 crore' to crore units."""
    text = str(value or "").strip().lower().replace(",", "")
    if not text:
        return DEFAULT_BASE_PRICE
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return DEFAULT_BASE_PRICE
    amount = Decimal(match.group(1))
    if "lakh" in text:
        amount /= Decimal("100")
    # The dataset's unqualified numeric values are treated as crore values.
    return amount if amount > 0 else DEFAULT_BASE_PRICE


def resolve_nationality(player_name, country=""):
    """Resolve nationality from the CSV or known overseas players in this pool."""
    country = str(country or "").strip()
    if country:
        return "Indian" if country.casefold() in {"india", "indian"} else "Overseas"
    known_country = OVERSEAS_COUNTRIES.get(str(player_name or "").strip())
    if known_country:
        return "Indian" if known_country.casefold() == "india" else "Overseas"
    # The source CSV leaves Country blank for most players in this squad dataset.
    return "Indian"


def load_players_from_csv():
    """Read the complete player pool from the project CSV."""
    if not PLAYER_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Player dataset not found: {PLAYER_CSV_PATH}. "
            "Place ipl_2026_all_teams_players_with_unsold.csv in the project root."
        )

    rows = []
    with PLAYER_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"Player_Name", "Player_Role", "Country", "Base_Price"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Player CSV is missing required columns: " + ", ".join(sorted(missing))
            )

        for player in reader:
            name = (player.get("Player_Name") or "").strip()
            if not name:
                continue

            country = (player.get("Country") or "").strip()
            nationality = resolve_nationality(name, country)

            role = (player.get("Player_Role") or "").strip() or "Player"
            rows.append({
                "player_name": name,
                "role": role,
                "nationality": nationality,
                "base_price": float(parse_base_price(player.get("Base_Price"))),
                "status": "available",
            })

    if not rows:
        raise ValueError("The player CSV did not contain any usable player names.")
    return rows


# =========================================================
# SUPABASE CONNECTION
# =========================================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )
try:
    supabase = get_supabase()
except Exception:
    st.error(
        "Could not connect to Supabase. Check your "
        ".streamlit/secrets.toml settings."
    )
    st.stop()
# =========================================================
# CHECK LOBBY SESSION
# =========================================================
if (
    not st.session_state.get("room_code")
    or not st.session_state.get("player_name")
):
    st.warning("Please create or join an auction room from the lobby.")
    if st.button("⬅️ Go to Lobby"):
        st.switch_page("app.py")
    st.stop()
room_code = st.session_state.room_code
player_name = st.session_state.player_name
# =========================================================
# GENERAL HELPERS
# =========================================================
def get_room():
    result = (
        supabase.table("auction_rooms")
        .select("*")
        .eq("room_code", room_code)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
def get_participants():
    result = (
        supabase.table("auction_participants")
        .select("*")
        .eq("room_code", room_code)
        .execute()
    )
    return result.data or []
def get_player_pool():
    result = (
        supabase.table("auction_player_pool")
        .select("*")
        .eq("room_code", room_code)
        .execute()
    )
    return result.data or []
def get_auction_state():
    result = (
        supabase.table("auction_state")
        .select("*")
        .eq("room_code", room_code)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
def get_my_participant():
    participants = get_participants()
    for participant in participants:
        if (
            participant["player_name"].strip().casefold()
            == player_name.strip().casefold()
        ):
            return participant
    return None
def get_my_team():
    participant = get_my_participant()
    if participant:
        return participant.get("team_id")
    return None
def money(value):
    return f"{Decimal(str(value or 0)):.2f} Cr"
def parse_time(value):
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)
def update_auction_state(**values):
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("auction_state").update(
        values
    ).eq("room_code", room_code).execute()
def get_team_row(team_id):
    result = (
        supabase.table("auction_teams")
        .select("*")
        .eq("room_code", room_code)
        .eq("team_id", team_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
# =========================================================
# INITIALIZE ROOM DATA
# =========================================================
def initialize_room_data():
    # Create team records if this room does not have them yet.
    existing_teams = (
        supabase.table("auction_teams")
        .select("team_id")
        .eq("room_code", room_code)
        .execute()
    ).data or []
    existing_team_ids = {
        row["team_id"] for row in existing_teams
    }
    for team_id, team_name in TEAMS.items():
        if team_id not in existing_team_ids:
            supabase.table("auction_teams").insert({
                "room_code": room_code,
                "team_id": team_id,
                "team_name": team_name,
                "purse": float(STARTING_PURSE),
                "squad_size": 0,
                "overseas_count": 0,
            }).execute()
    # Import the complete CSV pool once per room. Existing room pools are left
    # untouched so a running or completed auction is never reset.
    existing_players = get_player_pool()
    if existing_players:
        # Repair existing room rows previously imported with Unknown nationality.
        for existing_player in existing_players:
            if str(existing_player.get("nationality") or "").strip().casefold() == "unknown":
                corrected = resolve_nationality(existing_player.get("player_name"), "")
                if existing_player.get("id") is not None:
                    supabase.table("auction_player_pool").update(
                        {"nationality": corrected}
                    ).eq("id", existing_player["id"]).eq("room_code", room_code).execute()
    if not existing_players:
        player_rows = load_players_from_csv()
        # Insert in batches to avoid sending a large request to Supabase.
        for offset in range(0, len(player_rows), 100):
            batch = player_rows[offset:offset + 100]
            for row in batch:
                row["room_code"] = room_code
            supabase.table("auction_player_pool").insert(batch).execute()

    # Create the shared auction state if necessary.
    if not get_auction_state():
        supabase.table("auction_state").insert({
            "room_code": room_code,
            "current_player_id": None,
            "current_bid": 0,
            "highest_team": None,
            "status": "waiting",
            "auction_phase": "waiting",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
try:
    room = get_room()
    if not room:
        st.error("This room does not exist.")
        if st.button("Return to Lobby"):
            st.switch_page("app.py")
        st.stop()
    initialize_room_data()
except Exception as exc:
    st.error("Could not initialize the auction room.")
    st.code(str(exc))
    st.stop()
# =========================================================
# PAGE HEADER
# =========================================================
room = get_room()
is_host = (
    room
    and room.get("host_name", "").strip().casefold()
    == player_name.strip().casefold()
)
header_col, back_col = st.columns([5, 1])
with header_col:
    st.title("🏏 IPL MOCK AUCTION")
    st.caption(
        f"Room code: {room_code}  |  Player: {player_name}"
    )
with back_col:
    if st.button("🏠 Lobby"):
        st.switch_page("app.py")
# =========================================================
# TEAM SELECTION
# =========================================================
st.subheader("🏆 Choose Your IPL Team")
participants = get_participants()
my_participant = get_my_participant()
my_team = get_my_team()
if my_participant is None:
    st.error(
        "Your name is not registered in this room. "
        "Please return to the lobby and join again."
    )
    st.stop()
assigned_teams = {
    p.get("team_id")
    for p in participants
    if p.get("team_id")
}
available_teams = [
    team_id
    for team_id in TEAMS
    if team_id not in assigned_teams or team_id == my_team
]
if my_team:
    st.success(f"You selected **{TEAMS.get(my_team, my_team)}**.")
else:
    team_options = [""] + available_teams
    with st.form("choose_team_form"):
        chosen_team = st.selectbox(
            "Select your franchise",
            options=team_options,
            format_func=lambda x: (
                "Choose a team..." if x == ""
                else f"{x} — {TEAMS[x]}"
            ),
        )
        choose_clicked = st.form_submit_button(
            "Confirm Team",
            use_container_width=True,
        )
    if choose_clicked:
        if not chosen_team:
            st.error("Please select a team.")
        else:
            # Check again in case another participant selected it.
            latest_participants = get_participants()
            team_taken = any(
                p.get("team_id") == chosen_team
                and p.get("player_name", "").casefold()
                != player_name.casefold()
                for p in latest_participants
            )
            if team_taken:
                st.error("That team has already been selected.")
            else:
                try:
                    (
                        supabase.table("auction_participants")
                        .update({"team_id": chosen_team})
                        .eq("room_code", room_code)
                        .eq("player_name", player_name)
                        .execute()
                    )
                    st.rerun()
                except Exception as exc:
                    st.error("Could not save your team selection.")
                    st.code(str(exc))
# =========================================================
# PRE-AUCTION PLAYER LIST
# =========================================================
# Let everyone inspect the room's player pool before the host starts bidding.
pre_auction_state = get_auction_state()
if pre_auction_state and pre_auction_state.get("status") == "waiting":
    with st.expander("📋 View Player List — before bidding starts", expanded=False):
        pool_for_preview = get_player_pool()
        st.caption(f"{len(pool_for_preview)} players in this room's auction pool.")
        if not pool_for_preview:
            st.info("No players are loaded into this room yet.")
        else:
            search_player = st.text_input(
                "Search players",
                placeholder="Type a player name...",
                key="pre_auction_player_search",
            )
            roles = sorted({
                str(player.get("role") or "Player")
                for player in pool_for_preview
            })
            role_filter = st.selectbox(
                "Filter by role",
                options=["All roles"] + roles,
                key="pre_auction_role_filter",
            )
            preview_rows = []
            for player in pool_for_preview:
                name = str(player.get("player_name") or "")
                role = str(player.get("role") or "Player")
                if search_player.strip() and search_player.casefold() not in name.casefold():
                    continue
                if role_filter != "All roles" and role != role_filter:
                    continue
                preview_rows.append({
                    "Player": name,
                    "Role": role,
                    "Nationality": (player.get("nationality") if str(player.get("nationality") or "").strip().casefold() not in {"", "unknown"} else resolve_nationality(player.get("player_name"), "")),
                    "Base Price (Cr)": float(player.get("base_price") or 0),
                    "Status": str(player.get("status") or "available").title(),
                })
            st.caption(f"Showing {len(preview_rows)} player(s).")
            st.dataframe(
                preview_rows,
                use_container_width=True,
                hide_index=True,
            )

# =========================================================
# HOST CONTROLS
# =========================================================
st.divider()
st.subheader("🎮 Auction Controls")
if is_host:
    st.info("You are the host. You can start the auction.")
    current_state = get_auction_state()
    if current_state and current_state.get("status") == "waiting":
        if st.button(
            "🚀 Start Auction",
            type="primary",
            use_container_width=True,
        ):
            participants_now = get_participants()
            players_without_team = [
                p["player_name"]
                for p in participants_now
                if not p.get("team_id")
            ]
            if players_without_team:
                st.warning(
                    "Everyone must select a team before the auction starts. "
                    "Still waiting for: "
                    + ", ".join(players_without_team)
                )
            else:
                try:
                    available_players = [
                        p for p in get_player_pool()
                        if p.get("status") == "available"
                    ]
                    if not available_players:
                        st.error("There are no available players.")
                    else:
                        first_player = available_players[0]
                        now = datetime.now(timezone.utc)
                        update_auction_state(
                            current_player_id=first_player["id"],
                            current_bid=0,
                            highest_team=None,
                            status="active",
                            auction_phase="bidding",
                            last_bid_at=now.isoformat(),
                            countdown_ends_at=(
                                now + timedelta(seconds=BIDDING_SECONDS)
                            ).isoformat(),
                        )
                        (
                            supabase.table("auction_rooms")
                            .update({"status": "active"})
                            .eq("room_code", room_code)
                            .execute()
                        )
                        st.rerun()
                except Exception as exc:
                    st.error("Could not start the auction.")
                    st.code(str(exc))
else:
    st.caption("The host will start the auction once everyone is ready.")
# =========================================================
# LIVE AUCTION HELPERS
# =========================================================
def start_next_player():
    available_players = [
        p for p in get_player_pool()
        if p.get("status") == "available"
    ]
    if not available_players:
        update_auction_state(
            current_player_id=None,
            current_bid=0,
            highest_team=None,
            status="completed",
            auction_phase="completed",
            countdown_ends_at=None,
        )
        (
            supabase.table("auction_rooms")
            .update({"status": "completed"})
            .eq("room_code", room_code)
            .execute()
        )
        return
    next_player = available_players[0]
    now = datetime.now(timezone.utc)
    update_auction_state(
        current_player_id=next_player["id"],
        current_bid=0,
        highest_team=None,
        status="active",
        auction_phase="bidding",
        last_bid_at=now.isoformat(),
        countdown_ends_at=(
            now + timedelta(seconds=BIDDING_SECONDS)
        ).isoformat(),
    )
def process_auction_timer(state):
    phase = state.get("auction_phase", "waiting")
    status = state.get("status", "waiting")
    end_time = parse_time(state.get("countdown_ends_at"))
    now = datetime.now(timezone.utc)
    if status != "active" or phase in (
        "waiting", "completed", "paused"
    ):
        return
    if now < end_time:
        return
    player_id = state.get("current_player_id")
    # No bids were received before the timer expired.
    if phase == "bidding":
        if not state.get("highest_team"):
            player = next(
                (
                    p for p in get_player_pool()
                    if p.get("id") == player_id
                ),
                None,
            )
            if player and player.get("status") == "available":
                (
                    supabase.table("auction_player_pool")
                    .update({"status": "unsold"})
                    .eq("id", player_id)
                    .execute()
                )
            update_auction_state(
                auction_phase="unsold",
                countdown_ends_at=(
                    now + timedelta(seconds=RESULT_SECONDS)
                ).isoformat(),
            )
        else:
            update_auction_state(
                auction_phase="going_once",
                countdown_ends_at=(
                    now + timedelta(seconds=ANNOUNCEMENT_SECONDS)
                ).isoformat(),
            )
    elif phase == "going_once":
        update_auction_state(
            auction_phase="going_twice",
            countdown_ends_at=(
                now + timedelta(seconds=ANNOUNCEMENT_SECONDS)
            ).isoformat(),
        )
    elif phase == "going_twice":
        # Complete the sale only if the player is still available.
        player = next(
            (
                p for p in get_player_pool()
                if p.get("id") == player_id
            ),
            None,
        )
        if (
            player
            and player.get("status") == "available"
            and state.get("highest_team")
        ):
            team_id = state["highest_team"]
            final_price = Decimal(str(state["current_bid"]))
            (
                supabase.table("auction_player_pool")
                .update({
                    "status": "sold",
                    "sold_to": team_id,
                    "sold_price": float(final_price),
                })
                .eq("id", player_id)
                .execute()
            )
            team_row = get_team_row(team_id)
            if team_row:
                old_purse = Decimal(str(team_row.get("purse", 0)))
                new_purse = max(
                    Decimal("0"),
                    old_purse - final_price,
                )
                overseas_increment = (
                    1 if player.get("nationality") == "Overseas"
                    else 0
                )
                (
                    supabase.table("auction_teams")
                    .update({
                        "purse": float(new_purse),
                        "squad_size": int(
                            team_row.get("squad_size", 0)
                        ) + 1,
                        "overseas_count": int(
                            team_row.get("overseas_count", 0)
                        ) + overseas_increment,
                    })
                    .eq("room_code", room_code)
                    .eq("team_id", team_id)
                    .execute()
                )
        update_auction_state(
            auction_phase="sold",
            countdown_ends_at=(
                now + timedelta(seconds=RESULT_SECONDS)
            ).isoformat(),
        )
    elif phase in ("sold", "unsold"):
        start_next_player()
def submit_bid():
    state = get_auction_state()
    team_id = get_my_team()
    if not team_id:
        st.error("Select your team before bidding.")
        return
    if not state or state.get("auction_phase") != "bidding":
        st.warning("Bidding is not open right now.")
        return
    # A team cannot raise its own bid consecutively; another team must bid first.
    if state.get("highest_team") == team_id:
        st.warning("Your team is currently the highest bidder. Wait for another team to bid first.")
        return
    player_id = state.get("current_player_id")
    if not player_id:
        st.warning("There is no active player.")
        return
    players = get_player_pool()
    player = next(
        (p for p in players if p.get("id") == player_id),
        None,
    )
    if not player:
        st.error("Could not find the current player.")
        return
    current_bid = Decimal(str(state.get("current_bid") or 0))
    base_price = Decimal(str(player.get("base_price") or 0))
    new_bid = (
        base_price
        if current_bid == 0
        else current_bid + BID_INCREMENT
    )
    team_row = get_team_row(team_id)
    if not team_row:
        st.error("Your team record was not found.")
        return
    purse = Decimal(str(team_row.get("purse", 0)))
    squad_size = int(team_row.get("squad_size", 0))
    overseas_count = int(team_row.get("overseas_count", 0))
    if squad_size >= 25:
        st.error("Your squad has reached the limit of 25 players.")
        return
    if (
        player.get("nationality") == "Overseas"
        and overseas_count >= 8
    ):
        st.error("Your team has reached the limit of 8 overseas players.")
        return
    if new_bid > purse:
        st.error("Your remaining purse is too low for this bid.")
        return
    now = datetime.now(timezone.utc)
    try:
        supabase.table("auction_bids").insert({
            "room_code": room_code,
            "player_id": player_id,
            "team_id": team_id,
            "bid_amount": float(new_bid),
            "bidder_name": player_name,
        }).execute()
        update_auction_state(
            current_bid=float(new_bid),
            highest_team=team_id,
            auction_phase="bidding",
            last_bid_at=now.isoformat(),
            countdown_ends_at=(
                now + timedelta(seconds=BIDDING_SECONDS)
            ).isoformat(),
        )
    except Exception as exc:
        st.error("Your bid could not be submitted.")
        st.code(str(exc))
# =========================================================
# LIVE AUCTION DISPLAY
# =========================================================
st.divider()
st.subheader("🔴 Live Auction")
@st.fragment(run_every="1s")
def live_auction():
    try:
        state = get_auction_state()
        if not state:
            st.warning("Auction state is not available.")
            return
        # Only the host advances the auction phases.
        current_room = get_room()
        current_is_host = (
            current_room
            and current_room.get("host_name", "").strip().casefold()
            == player_name.strip().casefold()
        )
        if current_is_host:
            process_auction_timer(state)
            state = get_auction_state()
        status = state.get("status", "waiting")
        phase = state.get("auction_phase", "waiting")
        if status == "waiting":
            st.info("Waiting for the host to start the auction.")
            return
        if status == "completed" or phase == "completed":
            st.success("🏆 Auction completed! All players have been processed.")
            return
        player_id = state.get("current_player_id")
        players = get_player_pool()
        player = next(
            (p for p in players if p.get("id") == player_id),
            None,
        )
        if not player:
            st.info("Preparing the next player...")
            return
        end_time = parse_time(state.get("countdown_ends_at"))
        seconds_left = max(
            0,
            int((end_time - datetime.now(timezone.utc)).total_seconds())
            + 1,
        )
        team_id = state.get("highest_team")
        team_name = TEAMS.get(team_id, "No bids yet")
        current_bid = Decimal(str(state.get("current_bid") or 0))
        left, right = st.columns([3, 2])
        with left:
            st.markdown(
                f"""
                <div style="
                    padding:24px;
                    border-radius:18px;
                    background:linear-gradient(135deg,#172e50,#30204d);
                    border:1px solid #405576;
                ">
                    <div style="font-size:14px;color:#b7c9e5;">
                        CURRENT PLAYER
                    </div>
                    <div style="font-size:30px;font-weight:900;">
                        {player["player_name"]}
                    </div>
                    <div style="font-size:16px;margin-top:10px;">
                        {player.get("role", "Player")}
                        &nbsp; • &nbsp;
                        {player.get("nationality", "Indian")}
                    </div>
                    <hr style="border-color:#405576;">
                    <div>Base Price</div>
                    <div style="font-size:24px;font-weight:800;">
                        {money(player.get("base_price", 0))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            st.markdown("#### 💰 Current Highest Bid")
            st.markdown(
                f"<div style='font-size:34px;font-weight:900;'>"
                f"{money(current_bid)}</div>",
                unsafe_allow_html=True,
            )
            st.write(f"**Leading team:** {team_name}")
            if phase == "bidding":
                st.metric("Time Remaining", f"{seconds_left} sec")
            elif phase == "going_once":
                st.warning("🔔 GOING ONCE!")
            elif phase == "going_twice":
                st.warning("🔔 GOING TWICE!")
            elif phase == "sold":
                st.success(f"🔨 SOLD to {team_name}!")
            elif phase == "unsold":
                st.error("❌ UNSOLD")
        my_team_now = get_my_team()
        if phase == "bidding":
            if my_team_now:
                st.caption(
                    f"Your team: {TEAMS.get(my_team_now, my_team_now)}"
                    f" | Bid increment: {money(BID_INCREMENT)}"
                )
                if state.get("highest_team") == my_team_now:
                    st.info("⏳ Your team is currently leading. Wait for another team to bid.")
                elif st.button(
                    "🔨 Place Bid",
                    type="primary",
                    use_container_width=True,
                    key=f"bid_{player_id}_{state.get('current_bid', 0)}",
                ):
                    submit_bid()
                    st.rerun()
            else:
                st.info("Select an IPL team above before bidding.")
        # Show the latest bids for this room and player.
        bid_result = (
            supabase.table("auction_bids")
            .select("*")
            .eq("room_code", room_code)
            .eq("player_id", player_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        recent_bids = bid_result.data or []
        if recent_bids:
            st.markdown("#### Recent Bids")
            for bid in recent_bids:
                bid_team = TEAMS.get(
                    bid.get("team_id"),
                    bid.get("team_id", "Team"),
                )
                st.write(
                    f"**{bid.get('bidder_name', 'Player')}** "
                    f"({bid_team}) — {money(bid.get('bid_amount', 0))}"
                )
    except Exception as exc:
        st.error("Could not refresh the live auction.")
        st.caption(str(exc))
live_auction()
# =========================================================
# TEAM PURSE DASHBOARD
# =========================================================
st.divider()
st.subheader("📊 Team Purse Dashboard")
@st.fragment(run_every="3s")
def team_dashboard():
    try:
        result = (
            supabase.table("auction_teams")
            .select("*")
            .eq("room_code", room_code)
            .execute()
        )
        team_rows = result.data or []
        # Put teams in a consistent order.
        team_rows.sort(
            key=lambda row: list(TEAMS.keys()).index(row["team_id"])
            if row.get("team_id") in TEAMS
            else 999
        )
        columns = st.columns(2)
        for index, team in enumerate(team_rows):
            team_id = team["team_id"]
            team_name = team.get(
                "team_name",
                TEAMS.get(team_id, team_id),
            )
            color = TEAM_COLORS.get(team_id, "#405576")
            purse = Decimal(str(team.get("purse", 0)))
            squad_size = int(team.get("squad_size", 0))
            overseas_count = int(team.get("overseas_count", 0))
            spent = STARTING_PURSE - purse
            with columns[index % 2]:
                st.markdown(
                    f"""
                    <div style="
                        border-left:6px solid {color};
                        padding:14px;
                        margin-bottom:10px;
                        border-radius:10px;
                        background:rgba(255,255,255,0.05);
                    ">
                        <div style="font-size:18px;font-weight:900;">
                            {team_id} — {team_name}
                        </div>
                        <div style="margin-top:8px;">
                            Remaining purse:
                            <b>{money(purse)}</b>
                        </div>
                        <div>Spent: {money(spent)}</div>
                        <div>Squad: {squad_size}/25</div>
                        <div>Overseas players: {overseas_count}/8</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                roster_result = (
                    supabase.table("auction_player_pool")
                    .select("player_name,sold_price,nationality")
                    .eq("room_code", room_code)
                    .eq("status", "sold")
                    .eq("sold_to", team_id)
                    .execute()
                )
                roster = roster_result.data or []
                if roster:
                    with st.expander(
                        f"View {team_id} squad ({len(roster)} players)"
                    ):
                        for player in roster:
                            st.write(
                                f"• {player['player_name']} — "
                                f"{money(player.get('sold_price', 0))}"
                            )
    except Exception as exc:
        st.error("Could not load the team dashboard.")
        st.caption(str(exc))
team_dashboard()
# =========================================================
# ROOM PARTICIPANTS
# =========================================================
st.divider()
st.subheader("👥 Room Participants")
try:
    current_participants = get_participants()
    for participant in current_participants:
        participant_name = participant["player_name"]
        participant_team = participant.get("team_id")
        team_label = (
            TEAMS.get(participant_team, participant_team)
            if participant_team
            else "Choosing a team..."
        )
        host_label = (
            " 👑 Host"
            if participant_name.strip().casefold()
            == room.get("host_name", "").strip().casefold()
            else ""
        )
        st.write(
            f"• **{participant_name}** — {team_label}{host_label}"
        )
except Exception as exc:
    st.caption(f"Could not load participants: {exc}")
