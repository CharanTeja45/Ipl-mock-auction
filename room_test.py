
import random
import string
import html
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import streamlit as st
from supabase import create_client


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="IPL Mock Auction",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TEAMS = {
    "CSK": "Chennai Super Kings",
    "DC": "Delhi Capitals",
    "GT": "Gujarat Titans",
    "KKR": "Kolkata Knight Riders",
    "LSG": "Lucknow Super Giants",
    "MI": "Mumbai Indians",
    "PBKS": "Punjab Kings",
    "RR": "Rajasthan Royals",
    "RCB": "Royal Challengers Bengaluru",
    "SRH": "Sunrisers Hyderabad",
}

TEAM_COLORS = {
    "CSK": "#F9CD05",
    "DC": "#78BCE8",
    "GT": "#00B4D8",
    "KKR": "#A970FF",
    "LSG": "#F36C9B",
    "MI": "#1688F8",
    "PBKS": "#ED1B24",
    "RR": "#EA1A85",
    "RCB": "#E31E35",
    "SRH": "#FF7518",
}

STARTING_PURSE = Decimal("120.00")
BID_INCREMENT = Decimal("0.05")
BIDDING_SECONDS = 10
ANNOUNCEMENT_SECONDS = 3
RESULT_SECONDS = 2

SAMPLE_PLAYERS = [
    ("Virat Kohli", "Batter", "Indian", 2.00),
    ("Rohit Sharma", "Batter", "Indian", 2.00),
    ("Jasprit Bumrah", "Bowler", "Indian", 2.00),
    ("MS Dhoni", "Wicketkeeper", "Indian", 0.50),
    ("Hardik Pandya", "All-rounder", "Indian", 1.50),
    ("Suryakumar Yadav", "Batter", "Indian", 1.50),
    ("Shubman Gill", "Batter", "Indian", 2.00),
    ("Ravindra Jadeja", "All-rounder", "Indian", 1.50),
    ("Rashid Khan", "Bowler", "Overseas", 2.00),
    ("Jos Buttler", "Wicketkeeper", "Overseas", 2.00),
    ("Trent Boult", "Bowler", "Overseas", 1.50),
    ("Sunil Narine", "All-rounder", "Overseas", 1.50),
    ("Andre Russell", "All-rounder", "Overseas", 1.50),
    ("Rishabh Pant", "Wicketkeeper", "Indian", 2.00),
    ("Sanju Samson", "Wicketkeeper", "Indian", 1.50),
    ("Yashasvi Jaiswal", "Batter", "Indian", 1.50),
    ("Rinku Singh", "Batter", "Indian", 1.00),
    ("Kuldeep Yadav", "Bowler", "Indian", 1.00),
    ("Pat Cummins", "Bowler", "Overseas", 2.00),
    ("Nicholas Pooran", "Wicketkeeper", "Overseas", 1.50),
]


# =========================================================
# STYLING
# =========================================================

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at 5% 0%, rgba(22,136,248,.13), transparent 38%),
        radial-gradient(ellipse at 100% 15%, rgba(169,112,255,.10), transparent 35%),
        #0b1020;
    color: #f4f7ff;
}
.block-container {
    max-width: 1500px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}
h1, h2, h3 { font-weight: 850 !important; }
p, label { color: #e0e8f5; }
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #1a2942, #101827);
    border: 1px solid #31425f;
    padding: 15px;
    border-radius: 15px;
}
[data-testid="stMetricLabel"] { color: #afc0d9; }
[data-testid="stMetricValue"] { color: white; font-weight: 850; }
.stButton > button {
    min-height: 43px;
    border-radius: 12px;
    font-weight: 800;
    border: 1px solid #3b506f;
}
.stButton > button:hover {
    border-color: #ffd447;
    color: #ffd447;
}
hr { border-color: #2c3b54; }
.auction-banner {
    padding: 21px 14px;
    margin: 12px 0 18px;
    border-radius: 17px;
    text-align: center;
    font-size: 1.55rem;
    font-weight: 950;
    letter-spacing: 1px;
    border: 1px solid rgba(255,255,255,.16);
    animation: pulse .6s ease-out;
}
.auction-bidding { background: linear-gradient(110deg,#142b4c,#17608a); }
.auction-once { background: linear-gradient(110deg,#62400d,#c88719); }
.auction-twice { background: linear-gradient(110deg,#873719,#e16b21); }
.auction-sold { background: linear-gradient(110deg,#07583f,#13a875); }
.auction-unsold { background: linear-gradient(110deg,#641f31,#a52e49); }
.auction-completed { background: linear-gradient(110deg,#3c2b78,#7954d8); }
.player-card {
    padding: 25px;
    border-radius: 21px;
    background: linear-gradient(135deg,#1b2b45,#101827);
    border: 1px solid #344765;
    border-left: 7px solid var(--accent,#1688f8);
    margin: 12px 0 18px;
    animation: rise .4s ease-out;
}
.player-name {
    font-size: clamp(1.7rem,4vw,2.7rem);
    font-weight: 950;
    color: white;
}
.player-meta { color: #c0cee2; margin-top: 8px; }
.player-price {
    color: var(--accent,#ffd447);
    font-size: 1.6rem;
    font-weight: 950;
    margin-top: 15px;
}
.team-card {
    padding: 15px;
    border-radius: 15px;
    background: linear-gradient(145deg,#19243a,#101827);
    border: 1px solid #2e405d;
    border-top: 4px solid var(--accent,#1688f8);
    margin-bottom: 10px;
    min-height: 115px;
}
.team-code {
    font-size: 1.2rem;
    font-weight: 950;
    color: var(--accent,#fff);
}
.team-name { color: #bdcbe0; font-size: .88rem; margin-top: 4px; }
.team-balance {
    font-size: 1.5rem;
    font-weight: 950;
    color: white;
    margin-top: 12px;
}
@keyframes pulse {
    0% { transform: scale(.985); opacity: .7; }
    100% { transform: scale(1); opacity: 1; }
}
@keyframes rise {
    from { opacity: .55; transform: translateY(7px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="padding:23px;border-radius:20px;margin-bottom:18px;
background:linear-gradient(110deg,#152743,#1a1835);
border:1px solid #344765;">
    <div style="font-size:2.2rem;font-weight:950;color:white;">
        🏏 IPL MOCK AUCTION
    </div>
    <div style="color:#b9c9df;margin-top:7px;">
        MULTIPLAYER • LIVE BIDDING • TEAM PURSE TRACKING • AUTO SOLD/UNSOLD
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


try:
    supabase = get_supabase()
except Exception as exc:
    st.error("Could not connect to Supabase. Check your local secrets configuration.")
    st.caption(str(exc))
    st.stop()


# =========================================================
# SESSION STATE AND UTILITIES
# =========================================================

if "room_code" not in st.session_state:
    st.session_state.room_code = None

if "player_name" not in st.session_state:
    st.session_state.player_name = None


def norm(value):
    return str(value or "").strip().casefold()


def money(value):
    return Decimal(str(value if value is not None else 0))


def money_text(value):
    return f"₹{money(value):.2f} Cr"


def safe(value):
    return html.escape(str(value if value is not None else ""))


def utc_now():
    return datetime.now(timezone.utc)


def iso_time(value):
    return value.isoformat()


def parse_time(value):
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result
    except (ValueError, TypeError, AttributeError):
        return None


def seconds_left(value):
    deadline = parse_time(value)
    if deadline is None:
        return 0
    return max(0, int((deadline - utc_now()).total_seconds() + 0.999))


def show_banner(message, css_class):
    st.markdown(
        f'<div class="auction-banner {css_class}">{safe(message)}</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# ROOM AND PARTICIPANT HELPERS
# =========================================================

def generate_room_code():
    for _ in range(20):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        result = (
            supabase.table("auction_rooms")
            .select("room_code")
            .eq("room_code", code)
            .execute()
        )
        if not result.data:
            return code
    raise RuntimeError("Could not generate a room code.")


def get_room(code):
    result = (
        supabase.table("auction_rooms")
        .select("room_code,host_name,status,started_at")
        .eq("room_code", code)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_participants(code):
    result = (
        supabase.table("auction_participants")
        .select("id,room_code,player_name,team_id")
        .eq("room_code", code)
        .execute()
    )

    unique = {}
    for participant in result.data or []:
        key = norm(participant["player_name"])
        if key not in unique:
            unique[key] = participant
        elif not unique[key].get("team_id") and participant.get("team_id"):
            unique[key] = participant
    return list(unique.values())


def register_participant(code, name):
    name = name.strip()
    if not name:
        raise ValueError("Enter your name.")

    for participant in get_participants(code):
        if norm(participant["player_name"]) == norm(name):
            return participant

    result = (
        supabase.table("auction_participants")
        .insert({
            "room_code": code,
            "player_name": name,
            "team_id": None,
        })
        .execute()
    )
    if not result.data:
        raise RuntimeError("Could not register participant.")
    return result.data[0]


def save_team(code, player_name, team_id):
    participants = get_participants(code)
    matches = [
        p for p in participants
        if norm(p["player_name"]) == norm(player_name)
    ]
    if not matches:
        raise RuntimeError("Participant not found.")

    # Check that no other participant has already selected this team.
    for participant in participants:
        if (
            norm(participant["player_name"]) != norm(player_name)
            and participant.get("team_id") == team_id
        ):
            raise ValueError("That team is already selected by another participant.")

    for participant in matches:
        (
            supabase.table("auction_participants")
            .update({"team_id": team_id})
            .eq("id", participant["id"])
            .execute()
        )


def enter_room(code, name):
    code = code.strip().upper()
    name = name.strip()

    if not code or not name:
        st.error("Enter your name and room code.")
        return

    try:
        room = get_room(code)
        if not room:
            st.error("Room not found. Check the room code.")
            return
        if room["status"] != "waiting":
            st.error("This auction has already started.")
            return

        participant = register_participant(code, name)
        st.session_state.room_code = code
        st.session_state.player_name = participant["player_name"]
        st.rerun()

    except Exception as exc:
        st.error("Could not join the room.")
        st.caption(str(exc))


# =========================================================
# PLAYER POOL AND AUCTION STATE
# =========================================================

def get_player_pool(code):
    result = (
        supabase.table("auction_player_pool")
        .select("*")
        .eq("room_code", code)
        .order("id")
        .execute()
    )
    return result.data or []


def get_auction_state(code):
    result = (
        supabase.table("auction_state")
        .select("*")
        .eq("room_code", code)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def update_state(code, changes, expected_phase=None):
    payload = dict(changes)
    payload["updated_at"] = iso_time(utc_now())

    query = (
        supabase.table("auction_state")
        .update(payload)
        .eq("room_code", code)
    )
    if expected_phase is not None:
        query = query.eq("auction_phase", expected_phase)

    result = query.select("*").execute()
    return result.data or []


def initialize_auction(code):
    pool = get_player_pool(code)

    if not pool:
        rows = [
            {
                "room_code": code,
                "player_name": name,
                "role": role,
                "nationality": nationality,
                "base_price": price,
                "status": "available",
            }
            for name, role, nationality, price in SAMPLE_PLAYERS
        ]
        supabase.table("auction_player_pool").insert(rows).execute()

    state = get_auction_state(code)
    if not state:
        supabase.table("auction_state").insert({
            "room_code": code,
            "current_player_id": None,
            "current_bid": 0,
            "highest_team": None,
            "status": "waiting",
            "auction_phase": "waiting",
            "countdown_ends_at": None,
            "last_bid_at": None,
        }).execute()


def get_current_player(code):
    state = get_auction_state(code)
    if not state or not state.get("current_player_id"):
        return None

    result = (
        supabase.table("auction_player_pool")
        .select("*")
        .eq("room_code", code)
        .eq("id", state["current_player_id"])
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# =========================================================
# TEAM PURSE AND SQUAD HELPERS
# =========================================================

def get_team_records(code):
    result = (
        supabase.table("auction_teams")
        .select("*")
        .eq("room_code", code)
        .execute()
    )
    return result.data or []


def get_team_record(code, team_id):
    result = (
        supabase.table("auction_teams")
        .select("*")
        .eq("room_code", code)
        .eq("team_id", team_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def ensure_team_records(code):
    """
    Create one purse record for every IPL franchise in this room.
    This allows the dashboard to show all ten teams.
    """
    existing_records = get_team_records(code)
    existing_ids = {record["team_id"] for record in existing_records}

    for team_id, team_name in TEAMS.items():
        if team_id in existing_ids:
            continue

        supabase.table("auction_teams").insert({
            "room_code": code,
            "team_id": team_id,
            "team_name": team_name,
            "purse": float(STARTING_PURSE),
            "squad_size": 0,
            "overseas_count": 0,
        }).execute()


def refresh_team_stats(code):
    """
    Rebuild each team's balance and squad statistics from recorded sales.
    Recalculating avoids deducting the same player twice.
    """
    ensure_team_records(code)
    pool = get_player_pool(code)
    records = get_team_records(code)

    for team in records:
        team_id = team["team_id"]

        bought_players = [
            player for player in pool
            if player.get("status") == "sold"
            and player.get("sold_to") == team_id
        ]

        spent = sum(
            (money(player.get("sold_price")) for player in bought_players),
            Decimal("0"),
        )

        overseas_count = sum(
            1 for player in bought_players
            if norm(player.get("nationality")) == "overseas"
        )

        remaining = STARTING_PURSE - spent

        supabase.table("auction_teams").update({
            "purse": float(remaining),
            "squad_size": len(bought_players),
            "overseas_count": overseas_count,
        }).eq("id", team["id"]).execute()


def get_team_statistics(code):
    """
    Calculate display values from sold-player records so the dashboard
    remains consistent with the recorded auction results.
    """
    records = get_team_records(code)
    pool = get_player_pool(code)
    statistics = {}

    for team in records:
        team_id = team["team_id"]
        bought_players = [
            player for player in pool
            if player.get("status") == "sold"
            and player.get("sold_to") == team_id
        ]

        spent = sum(
            (money(player.get("sold_price")) for player in bought_players),
            Decimal("0"),
        )

        overseas = sum(
            1 for player in bought_players
            if norm(player.get("nationality")) == "overseas"
        )

        statistics[team_id] = {
            "team_name": team.get("team_name", TEAMS.get(team_id, team_id)),
            "spent": spent,
            "purse": STARTING_PURSE - spent,
            "squad_size": len(bought_players),
            "overseas_count": overseas,
            "players": bought_players,
        }

    return statistics


# =========================================================
# AUTOMATIC PLAYER SELECTION
# =========================================================

def next_player(code):
    pool = get_player_pool(code)
    available = [
        player for player in pool
        if player["status"] == "available"
    ]

    if not available:
        update_state(code, {
            "current_player_id": None,
            "current_bid": 0,
            "highest_team": None,
            "status": "completed",
            "auction_phase": "completed",
            "countdown_ends_at": None,
        })
        return False, "All players have been auctioned."

    player = available[0]
    deadline = utc_now() + timedelta(seconds=BIDDING_SECONDS)

    update_state(code, {
        "current_player_id": player["id"],
        "current_bid": float(money(player["base_price"])),
        "highest_team": None,
        "status": "bidding",
        "auction_phase": "bidding",
        "countdown_ends_at": iso_time(deadline),
        "last_bid_at": None,
    })

    return True, player["player_name"]


# =========================================================
# START AUCTION
# =========================================================

def start_auction(code, host_name):
    room = get_room(code)

    if not room:
        return False, "Room not found."
    if norm(room["host_name"]) != norm(host_name):
        return False, "Only the host can start the auction."
    if room["status"] != "waiting":
        return False, "The auction has already started."

    participants = get_participants(code)

    if len(participants) < 2:
        return False, "At least two participants are required."
    if any(not participant.get("team_id") for participant in participants):
        return False, "Every participant must select a team."

    selected_teams = [participant["team_id"] for participant in participants]
    if len(selected_teams) != len(set(selected_teams)):
        return False, "Each participant must select a different team."

    ensure_team_records(code)
    initialize_auction(code)

    (
        supabase.table("auction_rooms")
        .update({
            "status": "live",
            "started_at": iso_time(utc_now()),
        })
        .eq("room_code", code)
        .eq("status", "waiting")
        .execute()
    )

    room = get_room(code)
    if not room or room["status"] != "live":
        return False, "Could not start the auction."

    next_player(code)
    return True, "Auction started! Everyone can bid."


# =========================================================
# BIDDING
# =========================================================

def place_bid(code, bidder_name):
    room = get_room(code)
    if not room or room["status"] != "live":
        return False, "The auction is not live."

    participants = get_participants(code)
    bidder = next(
        (
            participant for participant in participants
            if norm(participant["player_name"]) == norm(bidder_name)
        ),
        None,
    )

    if not bidder or not bidder.get("team_id"):
        return False, "Select your team before bidding."

    state = get_auction_state(code)
    player = get_current_player(code)

    if not state or not player:
        return False, "No player is currently being auctioned."
    if state.get("status") != "bidding":
        return False, "Bidding is not open."
    if state.get("auction_phase") not in ("bidding", "going_once", "going_twice"):
        return False, "Bidding is closed for this player."

    deadline = parse_time(state.get("countdown_ends_at"))
    if deadline and utc_now() >= deadline:
        return False, "The timer has expired. Please wait for the result."

    if player["status"] != "available":
        return False, "This player is no longer available."
    if state.get("highest_team") == bidder["team_id"]:
        return False, "Your team already has the highest bid."

    team = get_team_record(code, bidder["team_id"])
    if not team:
        ensure_team_records(code)
        team = get_team_record(code, bidder["team_id"])

    if not team:
        return False, "Could not load your team's purse."

    new_bid = money(state["current_bid"]) + BID_INCREMENT

    if new_bid > money(team.get("purse")):
        return False, (
            f"Insufficient purse. Your team's remaining purse is "
            f"{money_text(team.get('purse'))}."
        )

    # Insert the bid before updating the shared auction state.
    supabase.table("auction_bids").insert({
        "room_code": code,
        "player_id": player["id"],
        "team_id": bidder["team_id"],
        "bid_amount": float(new_bid),
        "bidder_name": bidder["player_name"],
    }).execute()

    new_deadline = utc_now() + timedelta(seconds=BIDDING_SECONDS)

    update_state(code, {
        "current_bid": float(new_bid),
        "highest_team": bidder["team_id"],
        "status": "bidding",
        "auction_phase": "bidding",
        "countdown_ends_at": iso_time(new_deadline),
        "last_bid_at": iso_time(utc_now()),
    })

    return True, f"Bid placed: {money_text(new_bid)}"


def get_player_bids(code, player_id):
    result = (
        supabase.table("auction_bids")
        .select("*")
        .eq("room_code", code)
        .eq("player_id", player_id)
        .order("id", desc=True)
        .limit(10)
        .execute()
    )
    return result.data or []


# =========================================================
# AUTOMATIC SOLD / UNSOLD TIMER
# =========================================================

def settle_player(code, sold):
    state = get_auction_state(code)
    player = get_current_player(code)

    if not state or not player:
        return False
    if player["status"] != "available":
        return False

    phase = state.get("auction_phase")
    new_phase = "sold" if sold else "unsold"

    claimed = update_state(
        code,
        {
            "auction_phase": new_phase,
            "countdown_ends_at": iso_time(
                utc_now() + timedelta(seconds=RESULT_SECONDS)
            ),
        },
        expected_phase=phase,
    )

    if not claimed:
        return False

    if sold:
        result = (
            supabase.table("auction_player_pool")
            .update({
                "status": "sold",
                "sold_to": state["highest_team"],
                "sold_price": float(money(state["current_bid"])),
            })
            .eq("room_code", code)
            .eq("id", player["id"])
            .eq("status", "available")
            .execute()
        )

        if result.data:
            refresh_team_stats(code)

    else:
        (
            supabase.table("auction_player_pool")
            .update({
                "status": "unsold",
                "sold_to": None,
                "sold_price": None,
            })
            .eq("room_code", code)
            .eq("id", player["id"])
            .eq("status", "available")
            .execute()
        )

    return True


def process_automatic_timer(code):
    state = get_auction_state(code)
    if not state:
        return

    phase = state.get("auction_phase")
    deadline = parse_time(state.get("countdown_ends_at"))

    if not deadline or utc_now() < deadline:
        return

    player = get_current_player(code)

    if phase == "bidding":
        if not player:
            return

        if state.get("highest_team"):
            update_state(
                code,
                {
                    "auction_phase": "going_once",
                    "countdown_ends_at": iso_time(
                        utc_now() + timedelta(seconds=ANNOUNCEMENT_SECONDS)
                    ),
                },
                expected_phase="bidding",
            )
        else:
            settle_player(code, sold=False)

    elif phase == "going_once":
        update_state(
            code,
            {
                "auction_phase": "going_twice",
                "countdown_ends_at": iso_time(
                    utc_now() + timedelta(seconds=ANNOUNCEMENT_SECONDS)
                ),
            },
            expected_phase="going_once",
        )

    elif phase == "going_twice":
        settle_player(code, sold=True)

    elif phase in ("sold", "unsold"):
        claimed = update_state(
            code,
            {
                "auction_phase": "loading_next",
                "countdown_ends_at": None,
            },
            expected_phase=phase,
        )

        if claimed:
            next_player(code)


# =========================================================
# CREATE / JOIN ROOM
# =========================================================

if not st.session_state.room_code:
    create_tab, join_tab = st.tabs(["➕ Create Room", "🚪 Join Room"])

    with create_tab:
        st.subheader("Create a new auction")

        with st.form("create_room_form"):
            host_name = st.text_input("Host name")
            create_clicked = st.form_submit_button(
                "🏏 Create Auction Room",
                use_container_width=True,
            )

        if create_clicked:
            host_name = host_name.strip()

            if not host_name:
                st.error("Enter your name.")
            else:
                try:
                    code = generate_room_code()

                    created = (
                        supabase.table("auction_rooms")
                        .insert({
                            "room_code": code,
                            "host_name": host_name,
                            "status": "waiting",
                        })
                        .execute()
                    )

                    if created.data:
                        participant = register_participant(code, host_name)
                        st.session_state.room_code = code
                        st.session_state.player_name = participant["player_name"]
                        st.rerun()
                    else:
                        st.error("Room creation failed.")

                except Exception as exc:
                    st.error("Could not create the room.")
                    st.caption(str(exc))

    with join_tab:
        st.subheader("Join a friend's auction")

        with st.form("join_room_form"):
            join_code = st.text_input("Room code")
            join_name = st.text_input("Your name")
            join_clicked = st.form_submit_button(
                "🚪 Join Auction",
                use_container_width=True,
            )

        if join_clicked:
            enter_room(join_code, join_name)

    st.stop()


# =========================================================
# LOAD ROOM
# =========================================================

room_code = st.session_state.room_code
player_name = st.session_state.player_name

try:
    room = get_room(room_code)

    if not room:
        st.error("Room not found.")
        st.session_state.room_code = None
        st.session_state.player_name = None
        st.stop()

    participants = get_participants(room_code)

except Exception as exc:
    st.error("Could not load room.")
    st.caption(str(exc))
    st.stop()

is_host = norm(player_name) == norm(room["host_name"])

my_participant = next(
    (
        participant for participant in participants
        if norm(participant["player_name"]) == norm(player_name)
    ),
    None,
)


# =========================================================
# ROOM HEADER
# =========================================================

left, right = st.columns([3, 1])

with left:
    st.markdown(f"### 🏟️ Room `{room_code}`")
    st.caption(f"Welcome, **{player_name}**")

with right:
    if room["status"] == "live":
        st.success("🔴 AUCTION LIVE")
    elif room["status"] == "waiting":
        st.info("⏳ Waiting for host")
    else:
        st.success("🏁 Auction finished")

st.code(room_code, language=None)

if is_host:
    st.caption("⭐ You are the host and can bid like every other participant.")


# =========================================================
# FRANCHISE SELECTION
# =========================================================

st.divider()
st.subheader("🏆 Franchise Selection")

if my_participant:
    current_team = my_participant.get("team_id")

    if room["status"] == "waiting":
        taken_teams = {
            participant["team_id"]
            for participant in participants
            if participant.get("team_id")
            and norm(participant["player_name"]) != norm(player_name)
        }

        available_options = {
            team_id: name
            for team_id, name in TEAMS.items()
            if team_id not in taken_teams or team_id == current_team
        }

        team_ids = [""] + list(available_options.keys())

        selected_team = st.selectbox(
            "Choose your IPL franchise",
            team_ids,
            index=team_ids.index(current_team) if current_team in team_ids else 0,
            format_func=lambda team: (
                "Select a team" if not team
                else f"{team} — {TEAMS[team]}"
            ),
            key=f"team_{room_code}_{norm(player_name)}",
        )

        if st.button("💾 Save My Team", use_container_width=True):
            if not selected_team:
                st.warning("Please select a team.")
            else:
                try:
                    save_team(room_code, player_name, selected_team)
                    ensure_team_records(room_code)
                    st.success("Your team has been saved!")
                    st.rerun()
                except Exception as exc:
                    st.error("Could not save your team.")
                    st.caption(str(exc))

    elif current_team:
        color = TEAM_COLORS.get(current_team, "#1688f8")
        st.markdown(
            f"""
            <div class="team-card" style="--accent:{color}">
                <div class="team-code">{safe(current_team)}</div>
                <div class="team-name">{safe(TEAMS.get(current_team, current_team))}</div>
                <div class="team-name">Your selected franchise</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("You have not selected a team.")


# =========================================================
# PARTICIPANTS
# =========================================================

st.divider()
st.subheader("🛡️ Competing Franchises")

team_participants = [
    participant for participant in participants
    if participant.get("team_id")
]

if team_participants:
    columns = st.columns(3)

    for index, participant in enumerate(team_participants):
        team_id = participant["team_id"]
        color = TEAM_COLORS.get(team_id, "#1688f8")
        is_me = norm(participant["player_name"]) == norm(player_name)

        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="team-card" style="--accent:{color}">
                    <div class="team-code">{safe(team_id)}</div>
                    <div class="team-name">{safe(TEAMS.get(team_id, team_id))}</div>
                    <div class="team-name">
                        {"⭐ " if is_me else "🏏 "}
                        {safe(participant["player_name"])}
                        {" (You)" if is_me else ""}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.caption(
    f"{len(participants)} participant(s) in this room. "
    "Each participant must select a different franchise."
)


# =========================================================
# TEAM PURSE AND SQUAD DASHBOARD
# =========================================================

st.divider()
st.header("💰 Team Purse & Squad Dashboard")
st.caption(
    "Each franchise starts with ₹120 Cr. "
    "The winning team's purse and squad update after a player is sold."
)

try:
    ensure_team_records(room_code)
    refresh_team_stats(room_code)
except Exception as exc:
    st.error("Could not initialize team purse records.")
    st.caption(str(exc))

@st.fragment(run_every="3s")
def team_purse_dashboard():
    try:
        # Ensure newly selected teams also have records.
        ensure_team_records(room_code)
        statistics = get_team_statistics(room_code)

        if not statistics:
            st.info("Team details will appear here.")
            return

        columns = st.columns(3)

        for index, team_id in enumerate(TEAMS):
            info = statistics.get(team_id)

            if info is None:
                continue

            color = TEAM_COLORS.get(team_id, "#1688f8")
            purse = info["purse"]
            spent = info["spent"]

            with columns[index % 3]:
                st.markdown(
                    f"""
                    <div class="team-card" style="--accent:{color};min-height:205px;">
                        <div class="team-code">{safe(team_id)}</div>
                        <div class="team-name">{safe(TEAMS[team_id])}</div>
                        <div class="team-balance">{money_text(purse)}</div>
                        <div class="team-name">Remaining purse</div>
                        <div class="team-name" style="margin-top:9px;">
                            Spent: {money_text(spent)}
                        </div>
                        <div class="team-name">
                            Squad: {info["squad_size"]} players
                        </div>
                        <div class="team-name">
                            Overseas: {info["overseas_count"]} players
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                ratio = float(purse / STARTING_PURSE)
                st.progress(
                    min(1.0, max(0.0, ratio)),
                    text="Purse remaining",
                )

                with st.expander(f"📋 {team_id} squad"):
                    if info["players"]:
                        for bought in info["players"]:
                            st.write(
                                f"🏏 {bought['player_name']} — "
                                f"{money_text(bought.get('sold_price'))}"
                            )
                    else:
                        st.caption("No players purchased yet.")

    except Exception as exc:
        st.error("Could not refresh team purse details.")
        st.caption(str(exc))


team_purse_dashboard()


# =========================================================
# AUCTION CONTROLS
# =========================================================

st.divider()
st.subheader("🎮 Auction Controls")

if is_host and room["status"] == "waiting":
    ready = (
        len(participants) >= 2
        and all(participant.get("team_id") for participant in participants)
        and len({
            participant["team_id"]
            for participant in participants
            if participant.get("team_id")
        }) == len([
            participant for participant in participants
            if participant.get("team_id")
        ])
    )

    if not ready:
        st.warning(
            "At least two participants must join and select different teams."
        )

    if st.button(
        "🚀 START LIVE AUCTION",
        type="primary",
        use_container_width=True,
        disabled=not ready,
    ):
        try:
            success, message = start_auction(room_code, player_name)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        except Exception as exc:
            st.error("Could not start the auction.")
            st.caption(str(exc))

elif room["status"] == "live":
    st.info("The auction runs automatically. All participants can bid.")


# =========================================================
# LIVE AUCTION ARENA
# =========================================================

st.divider()
st.header("🔴 Live Auction Arena")


@st.fragment(run_every="1s")
def live_auction():
    try:
        current_room = get_room(room_code)

        if not current_room or current_room["status"] != "live":
            st.info("The live auction will appear after the host starts it.")
            return

        process_automatic_timer(room_code)
        state = get_auction_state(room_code)

        if not state:
            st.warning("Auction state is not initialized.")
            return

        phase = state.get("auction_phase", "waiting")

        if phase == "completed":
            show_banner("🏆 AUCTION COMPLETED", "auction-completed")
            st.success("All available players have been processed.")
            return

        player = get_current_player(room_code)

        if not player:
            st.info("Preparing the next player...")
            return

        state = get_auction_state(room_code)
        phase = state.get("auction_phase", "bidding")
        remaining = seconds_left(state.get("countdown_ends_at"))

        team_id = state.get("highest_team")
        accent = TEAM_COLORS.get(team_id, "#ffd447")

        if phase == "bidding":
            show_banner("🔨 LIVE BIDDING", "auction-bidding")
        elif phase == "going_once":
            show_banner("📣 GOING ONCE!", "auction-once")
        elif phase == "going_twice":
            show_banner("🔥 GOING TWICE!", "auction-twice")
        elif phase == "sold":
            show_banner("🏆 SOLD!", "auction-sold")
        elif phase == "unsold":
            show_banner("❌ UNSOLD", "auction-unsold")
        elif phase == "loading_next":
            show_banner("⏭️ NEXT PLAYER LOADING", "auction-bidding")

        st.markdown(
            f"""
            <div class="player-card" style="--accent:{accent}">
                <div style="text-transform:uppercase;letter-spacing:2px;
                            color:#9eb5d3;font-size:.8rem;font-weight:800;">
                    PLAYER ON THE BLOCK
                </div>
                <div class="player-name">{safe(player["player_name"])}</div>
                <div class="player-meta">
                    🏏 {safe(player.get("role"))}
                    &nbsp; • &nbsp;
                    🌍 {safe(player.get("nationality"))}
                </div>
                <div class="player-price">
                    Base Price: {money_text(player["base_price"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        bid_col, team_col, timer_col = st.columns(3)

        with bid_col:
            st.metric("💰 CURRENT BID", money_text(state["current_bid"]))

        with team_col:
            st.metric("🏆 HIGHEST TEAM", team_id or "No bids yet")
            if team_id:
                st.caption(TEAMS.get(team_id, team_id))

        with timer_col:
            st.metric("⏱️ TIME LEFT", f"{remaining}s")

        if phase == "bidding":
            st.progress(
                min(1.0, max(0.0, remaining / BIDDING_SECONDS)),
                text="Bidding countdown",
            )
        elif phase in ("going_once", "going_twice"):
            st.progress(
                min(1.0, max(0.0, remaining / ANNOUNCEMENT_SECONDS)),
                text="Auction announcement",
            )

        if phase in ("bidding", "going_once", "going_twice"):
            my_team = my_participant.get("team_id") if my_participant else None

            if not my_team:
                st.warning("Select your IPL team before bidding.")
            elif team_id == my_team:
                st.info("⭐ Your team currently has the highest bid.")
            else:
                next_bid = money(state["current_bid"]) + BID_INCREMENT

                st.markdown("#### ⚡ Place your bid")
                st.markdown(
                    f"""
                    <div style="text-align:center;padding:14px;border-radius:14px;
                                margin:8px 0 12px;background:#14243a;
                                border:1px solid #314867;">
                        <div style="color:#aebfd7;font-size:.9rem;">
                            NEXT AVAILABLE BID
                        </div>
                        <div style="font-size:2rem;font-weight:950;color:#ffd447;">
                            {money_text(next_bid)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"🔨 BID {money_text(next_bid)}",
                    type="primary",
                    use_container_width=True,
                    key=f"bid_{room_code}_{player['id']}",
                ):
                    success, message = place_bid(room_code, player_name)

                    if success:
                        st.toast(message, icon="🏏")
                    else:
                        st.warning(message)
                    st.rerun()

        elif phase == "sold":
            st.success(
                f"🏆 {player['player_name']} sold to {state.get('highest_team')} "
                f"for {money_text(state['current_bid'])}!"
            )
        elif phase == "unsold":
            st.warning("No bids were placed for this player.")

        st.divider()
        st.subheader("📈 Recent Bids")

        bids = get_player_bids(room_code, player["id"])

        if bids:
            for bid in bids:
                bid_team = bid["team_id"]
                color = TEAM_COLORS.get(bid_team, "#1688f8")

                st.markdown(
                    f"""
                    <div style="padding:12px 15px;margin:6px 0;border-radius:12px;
                                background:#141f32;border-left:4px solid {color};
                                display:flex;justify-content:space-between;
                                gap:10px;flex-wrap:wrap;">
                        <div>
                            <strong style="color:{color};">{safe(bid_team)}</strong>
                            <span style="color:#d5dfed;">
                                — {safe(bid["bidder_name"])}
                            </span>
                        </div>
                        <strong style="color:white;">
                            {money_text(bid["bid_amount"])}
                        </strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No bids yet. Be the first to place a bid!")

    except Exception as exc:
        st.error("Could not load the live auction.")
        st.caption(str(exc))


live_auction()


# =========================================================
# AUCTION SUMMARY
# =========================================================

st.divider()
st.header("📋 Auction Summary")

try:
    pool = get_player_pool(room_code)

    sold_players = [p for p in pool if p["status"] == "sold"]
    unsold_players = [p for p in pool if p["status"] == "unsold"]
    available_players = [p for p in pool if p["status"] == "available"]

    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Players Sold", len(sold_players))
    m2.metric("❌ Players Unsold", len(unsold_players))
    m3.metric("⏳ Remaining", len(available_players))

    with st.expander("🏆 View sold players"):
        if sold_players:
            for player in sold_players:
                color = TEAM_COLORS.get(player.get("sold_to"), "#24d18b")
                st.markdown(
                    f"""
                    <div style="padding:12px;margin:6px 0;background:#14243a;
                                border-left:4px solid {color};border-radius:10px;">
                        <strong>{safe(player["player_name"])}</strong>
                        <span style="color:{color};">
                            — {safe(player.get("sold_to"))}
                        </span>
                        <span style="float:right;font-weight:800;">
                            {money_text(player.get("sold_price"))}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No players sold yet.")

    with st.expander("❌ View unsold players"):
        if unsold_players:
            for player in unsold_players:
                st.write(f"❌ {player['player_name']} — Unsold")
        else:
            st.caption("No unsold players yet.")

    with st.expander("⏳ View remaining players"):
        if available_players:
            for player in available_players:
                st.write(
                    f"🏏 {player['player_name']} — "
                    f"{money_text(player['base_price'])}"
                )
        else:
            st.caption("No remaining players.")

except Exception as exc:
    st.warning("Could not load auction results.")
    st.caption(str(exc))


# =========================================================
# FOOTER CONTROLS
# =========================================================

st.divider()

refresh_col, leave_col = st.columns(2)

with refresh_col:
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()

with leave_col:
    if st.button("🚪 Leave Room", use_container_width=True):
        st.session_state.room_code = None
        st.session_state.player_name = None
        st.rerun()

st.caption(
    "IPL Mock Auction • Multiplayer prototype • Shared Supabase state "
    "• Automatic SOLD/UNSOLD timer"
)