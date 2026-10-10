import streamlit as st
import json
import os

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="IPL Mock Auction",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# FILE PATHS
# ============================================================

TEAMS_FILE = "data/teams.json"
PLAYERS_FILE = "data/players.json"
STATE_FILE = "data/auction_state.json"

TEAM_IMAGE_FOLDER = "images/teams"
PLAYER_IMAGE_FOLDER = "images/players"

# Auction rules
MAX_SQUAD_SIZE = 25
MAX_OVERSEAS_PLAYERS = 8
MIN_SQUAD_SIZE = 18

# ============================================================
# LOAD JSON
# ============================================================

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# SAVE STATE
# ============================================================

def save_auction_state():
    state = {
        "purses": st.session_state.purses,
        "squads": st.session_state.squads
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)


# ============================================================
# IMAGE FUNCTIONS
# ============================================================

def get_player_image(player_id):

    for extension in [".jpg", ".jpeg", ".png", ".webp"]:

        path = os.path.join(
            PLAYER_IMAGE_FOLDER,
            player_id + extension
        )

        if os.path.exists(path):
            return path

    return None


def get_team_image(team_id):

    for extension in [".png", ".jpg", ".jpeg", ".webp"]:

        path = os.path.join(
            TEAM_IMAGE_FOLDER,
            team_id + extension
        )

        if os.path.exists(path):
            return path

    return None


# ============================================================
# LOAD DATA
# ============================================================

teams = load_json(TEAMS_FILE)
players = load_json(PLAYERS_FILE)


# ============================================================
# SESSION STATE
# ============================================================

if "state_loaded" not in st.session_state:

    if os.path.exists(STATE_FILE):

        saved_state = load_json(STATE_FILE)

        st.session_state.purses = saved_state.get(
            "purses",
            {
                team["id"]: float(team["purse"])
                for team in teams
            }
        )

        st.session_state.squads = saved_state.get(
            "squads",
            {
                team["id"]: []
                for team in teams
            }
        )

    else:

        st.session_state.purses = {
            team["id"]: float(team["purse"])
            for team in teams
        }

        st.session_state.squads = {
            team["id"]: []
            for team in teams
        }

    st.session_state.state_loaded = True


if "current_player" not in st.session_state:
    st.session_state.current_player = None

if "current_bid" not in st.session_state:
    st.session_state.current_bid = 0.0

if "highest_team" not in st.session_state:
    st.session_state.highest_team = None

if "auction_started" not in st.session_state:
    st.session_state.auction_started = False

if "last_result" not in st.session_state:
    st.session_state.last_result = None


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fb;
    }

    .hero {
        padding: 28px;
        border-radius: 20px;
        text-align: center;
        background: linear-gradient(
            135deg,
            #111827,
            #1f2937
        );
        color: white;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 45px;
        font-weight: 800;
    }

    .hero-subtitle {
        font-size: 18px;
        opacity: 0.85;
    }

    .player-card {
        background: white;
        padding: 25px;
        border-radius: 22px;
        text-align: center;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 20px rgba(0,0,0,0.07);
    }

    .player-name {
        font-size: 34px;
        font-weight: 800;
    }

    .player-role {
        font-size: 17px;
        color: #6b7280;
        margin: 8px;
    }

    .bid-box {
        background: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #e5e7eb;
        box-shadow: 0 5px 20px rgba(0,0,0,0.06);
    }

    .bid-label {
        font-size: 15px;
        color: #6b7280;
    }

    .bid-price {
        font-size: 46px;
        font-weight: 900;
    }

    .section-title {
        font-size: 28px;
        font-weight: 800;
        margin-top: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-title">
            🏏 IPL MOCK AUCTION
        </div>

        <div class="hero-subtitle">
            Build Your Dream Squad • Bid Smart • Win the Auction
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FIND SOLD PLAYERS
# ============================================================

sold_player_ids = set()

for squad in st.session_state.squads.values():

    for squad_player in squad:

        if isinstance(squad_player, dict):
            sold_player_ids.add(squad_player["id"])


available_players = [
    player
    for player in players
    if player["id"] not in sold_player_ids
]


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎮 Auction Control")

st.sidebar.markdown("---")


# ============================================================
# PLAYER FILTERS
# ============================================================

selected_player = None

if available_players:

    st.sidebar.subheader("🔎 Player Filters")

    role_filter = st.sidebar.selectbox(
        "Player Role",
        [
            "All Roles",
            "Batter",
            "Bowler",
            "All-rounder",
            "Wicketkeeper"
        ]
    )

    nationality_filter = st.sidebar.selectbox(
        "Nationality",
        [
            "All",
            "Indian",
            "Overseas"
        ]
    )

    filtered_players = available_players.copy()

    if role_filter != "All Roles":

        filtered_players = [
            player
            for player in filtered_players
            if player.get("role") == role_filter
        ]

    if nationality_filter != "All":

        filtered_players = [
            player
            for player in filtered_players
            if player.get("nationality") == nationality_filter
        ]


    # ========================================================
    # SELECT PLAYER
    # ========================================================

    if filtered_players:

        selected_name = st.sidebar.selectbox(
            "👤 Select Player",
            [
                player["name"]
                for player in filtered_players
            ]
        )

        selected_player = next(
            player
            for player in filtered_players
            if player["name"] == selected_name
        )

    else:

        st.sidebar.warning(
            "No players match the selected filters."
        )


# ============================================================
# PLAYER PREVIEW
# ============================================================

if selected_player:

    st.sidebar.markdown("---")

    st.sidebar.subheader("👤 Player Preview")

    preview_image = get_player_image(
        selected_player["id"]
    )

    if preview_image:

        st.sidebar.image(
            preview_image,
            use_container_width=True
        )

    else:

        st.sidebar.markdown(
            """
            <div style="
                text-align:center;
                font-size:70px;
                padding:20px;
            ">
                🏏
            </div>
            """,
            unsafe_allow_html=True
        )


    st.sidebar.write(
        f"**Role:** {selected_player['role']}"
    )

    st.sidebar.write(
        f"**Country:** {selected_player['nationality']}"
    )

    st.sidebar.write(
        f"**Previous IPL Team:** {selected_player['team']}"
    )

    st.sidebar.write(
        f"**Base Price:** "
        f"₹{float(selected_player['base_price']):.2f} Cr"
    )


    # ========================================================
    # START AUCTION
    # ========================================================

    if st.sidebar.button(
        "🔨 START AUCTION",
        use_container_width=True
    ):

        st.session_state.current_player = selected_player

        st.session_state.current_bid = float(
            selected_player["base_price"]
        )

        st.session_state.highest_team = None

        st.session_state.auction_started = True

        st.session_state.last_result = None

        st.rerun()


# ============================================================
# LIVE AUCTION
# ============================================================

if st.session_state.auction_started:

    player = st.session_state.current_player

    st.markdown(
        '<div class="section-title">🔴 LIVE AUCTION</div>',
        unsafe_allow_html=True
    )


    # ========================================================
    # PLAYER INFORMATION
    # ========================================================

    photo_col, details_col = st.columns(
        [1, 2]
    )


    with photo_col:

        player_image = get_player_image(
            player["id"]
        )

        if player_image:

            st.image(
                player_image,
                use_container_width=True
            )

        else:

            st.markdown(
                """
                <div class="player-card">

                    <div style="
                        font-size:100px;
                        padding:50px;
                    ">
                        🏏
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


    with details_col:

        st.markdown(
            f"""
            <div class="player-card">

                <div class="player-name">
                    {player["name"]}
                </div>

                <div class="player-role">
                    {player["role"]}
                    •
                    {player["nationality"]}
                    •
                    {player["team"]}
                </div>

                <hr>

                <div>
                    <b>BASE PRICE</b>
                </div>

                <div class="bid-price">
                    ₹{float(player["base_price"]):.2f} Cr
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # PLAYER STATISTICS
    # ========================================================

    st.markdown("### 📊 Player Statistics")

    s1, s2, s3, s4, s5, s6 = st.columns(6)

    with s1:
        st.metric("Matches", player.get("matches", "—"))

    with s2:
        st.metric("Runs", player.get("runs", "—"))

    with s3:
        st.metric("Average", player.get("average", "—"))

    with s4:
        st.metric(
            "Strike Rate",
            player.get("strike_rate", "—")
        )

    with s5:
        st.metric(
            "Wickets",
            player.get("wickets", "—")
        )

    with s6:
        st.metric(
            "Economy",
            player.get("economy", "—")
        )


    st.markdown("---")


    # ========================================================
    # CURRENT BID
    # ========================================================

    b1, b2, b3 = st.columns(3)


    with b1:

        st.markdown(
            f"""
            <div class="bid-box">

                <div class="bid-label">
                    CURRENT BID
                </div>

                <div class="bid-price">
                    ₹{st.session_state.current_bid:.2f} Cr
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    with b2:

        if st.session_state.highest_team:

            highest_team = next(
                team
                for team in teams
                if team["id"]
                == st.session_state.highest_team
            )

            logo = get_team_image(
                highest_team["id"]
            )

            if logo:
                st.image(logo, width=65)

            st.metric(
                "🏆 LEADING TEAM",
                highest_team["short_name"]
            )

        else:

            st.metric(
                "🏆 LEADING TEAM",
                "No bids"
            )


    with b3:

        st.metric(
            "💵 BASE PRICE",
            f"₹{float(player['base_price']):.2f} Cr"
        )


    st.markdown("---")


    # ========================================================
    # TEAM BIDDING
    # ========================================================

    st.markdown(
        '<div class="section-title">💰 PLACE YOUR BIDS</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Every bid increases the price by **₹0.20 Cr**."
    )


    bid_columns = st.columns(5)


    for i, team in enumerate(teams):

        team_id = team["id"]

        with bid_columns[i % 5]:

            team_logo = get_team_image(team_id)

            if team_logo:
                st.image(team_logo, width=65)

            st.markdown(
                f"### {team['short_name']}"
            )


            # ------------------------------------------------
            # TEAM INFORMATION
            # ------------------------------------------------

            purse = float(
                st.session_state.purses[team_id]
            )

            squad = st.session_state.squads[team_id]

            squad_size = len(squad)

            overseas_count = sum(
                1
                for squad_player in squad
                if squad_player.get("nationality")
                == "Overseas"
            )


            st.write(
                f"💰 ₹{purse:.2f} Cr"
            )

            st.write(
                f"👥 {squad_size}/{MAX_SQUAD_SIZE}"
            )

            st.write(
                f"🌍 {overseas_count}/{MAX_OVERSEAS_PLAYERS}"
            )


            # ------------------------------------------------
            # NEXT BID
            # ------------------------------------------------

            next_bid = round(
                st.session_state.current_bid + 0.20,
                2
            )


            # ------------------------------------------------
            # TEAM RESTRICTIONS
            # ------------------------------------------------

            can_bid = True

            restriction_message = ""


            # Maximum squad size

            if squad_size >= MAX_SQUAD_SIZE:

                can_bid = False

                restriction_message = (
                    "Squad full"
                )


            # Maximum overseas players

            elif (
                player.get("nationality") == "Overseas"
                and overseas_count >= MAX_OVERSEAS_PLAYERS
            ):

                can_bid = False

                restriction_message = (
                    "8 overseas players reached"
                )


            # Purse check

            elif purse < next_bid:

                can_bid = False

                restriction_message = (
                    "Insufficient purse"
                )


            # ------------------------------------------------
            # LEADING TEAM
            # ------------------------------------------------

            if team_id == st.session_state.highest_team:

                st.success("🏆 LEADING")


            elif can_bid:

                if st.button(
                    f"BID ₹{next_bid:.2f} Cr",
                    key=f"bid_{team_id}",
                    use_container_width=True
                ):

                    st.session_state.current_bid = next_bid

                    st.session_state.highest_team = team_id

                    st.rerun()


            else:

                st.warning(
                    restriction_message
                )


    st.markdown("---")


    # ========================================================
    # AUCTION RESULT
    # ========================================================

    st.markdown(
        '<div class="section-title">📢 AUCTION RESULT</div>',
        unsafe_allow_html=True
    )

    sold_col, unsold_col = st.columns(2)


    # ========================================================
    # SOLD BUTTON
    # ========================================================

    with sold_col:

        if st.button(
            "🔨 SOLD",
            use_container_width=True
        ):

            if st.session_state.highest_team is None:

                st.warning(
                    "⚠️ At least one team must bid first."
                )

            else:

                team_id = st.session_state.highest_team

                price = float(
                    st.session_state.current_bid
                )


                squad = st.session_state.squads[team_id]


                # Re-check squad limit

                if len(squad) >= MAX_SQUAD_SIZE:

                    st.error(
                        "This team already has 25 players."
                    )

                else:

                    # Re-check overseas limit

                    overseas_count = sum(
                        1
                        for squad_player in squad
                        if squad_player.get("nationality")
                        == "Overseas"
                    )


                    if (
                        player.get("nationality")
                        == "Overseas"
                        and overseas_count
                        >= MAX_OVERSEAS_PLAYERS
                    ):

                        st.error(
                            "This team already has "
                            "8 overseas players."
                        )

                    elif (
                        st.session_state.purses[team_id]
                        < price
                    ):

                        st.error(
                            "This team does not have "
                            "enough purse."
                        )

                    else:

                        # Deduct purse

                        st.session_state.purses[team_id] = round(
                            st.session_state.purses[team_id]
                            - price,
                            2
                        )


                        # Save player

                        purchased_player = {
                            "id": player["id"],
                            "name": player["name"],
                            "role": player["role"],
                            "nationality": player["nationality"],
                            "team": player["team"],
                            "base_price": player["base_price"],
                            "sold_price": price,
                            "matches": player.get("matches", 0),
                            "runs": player.get("runs", 0),
                            "average": player.get("average", 0),
                            "strike_rate": player.get(
                                "strike_rate",
                                0
                            ),
                            "wickets": player.get(
                                "wickets",
                                0
                            ),
                            "economy": player.get(
                                "economy",
                                0
                            )
                        }


                        st.session_state.squads[
                            team_id
                        ].append(
                            purchased_player
                        )


                        save_auction_state()


                        team_name = next(
                            team["name"]
                            for team in teams
                            if team["id"] == team_id
                        )


                        st.session_state.last_result = (
                            f"🎉 {player['name']} SOLD to "
                            f"{team_name} for "
                            f"₹{price:.2f} Cr!"
                        )


                        st.session_state.current_player = None

                        st.session_state.current_bid = 0.0

                        st.session_state.highest_team = None

                        st.session_state.auction_started = False

                        st.rerun()


    # ========================================================
    # UNSOLD BUTTON
    # ========================================================

    with unsold_col:

        if st.button(
            "❌ UNSOLD",
            use_container_width=True
        ):

            st.session_state.last_result = (
                f"❌ {player['name']} was UNSOLD."
            )

            st.session_state.current_player = None

            st.session_state.current_bid = 0.0

            st.session_state.highest_team = None

            st.session_state.auction_started = False

            st.rerun()


else:

    st.info(
        "👈 Select a player from the sidebar "
        "and click **START AUCTION**."
    )


# ============================================================
# LAST RESULT
# ============================================================

if st.session_state.last_result:

    st.success(
        st.session_state.last_result
    )


st.markdown("---")


# ============================================================
# TEAM PURSES
# ============================================================

st.markdown(
    '<div class="section-title">💰 TEAM PURSES</div>',
    unsafe_allow_html=True
)

purse_columns = st.columns(5)


for i, team in enumerate(teams):

    with purse_columns[i % 5]:

        logo = get_team_image(team["id"])

        if logo:
            st.image(logo, width=55)

        purse_value = float(
            st.session_state.purses[team["id"]]
        )

        st.metric(
            team["short_name"],
            f"₹{purse_value:.2f} Cr"
        )


st.markdown("---")


# ============================================================
# CURRENT SQUADS
# ============================================================

st.markdown(
    '<div class="section-title">🏆 CURRENT SQUADS</div>',
    unsafe_allow_html=True
)


for team in teams:

    team_id = team["id"]

    squad = st.session_state.squads[team_id]


    with st.expander(
        f"{team['short_name']} — "
        f"{len(squad)}/{MAX_SQUAD_SIZE} Players"
    ):

        if squad:

            total_spent = sum(
                float(
                    squad_player.get(
                        "sold_price",
                        0
                    )
                )
                for squad_player in squad
            )


            overseas_count = sum(
                1
                for squad_player in squad
                if squad_player.get("nationality")
                == "Overseas"
            )


            st.write(
                f"💰 **Total Spent:** "
                f"₹{total_spent:.2f} Cr"
            )

            st.write(
                f"👥 **Squad:** "
                f"{len(squad)}/{MAX_SQUAD_SIZE}"
            )

            st.write(
                f"🌍 **Overseas:** "
                f"{overseas_count}/{MAX_OVERSEAS_PLAYERS}"
            )


            st.markdown("---")


            for squad_player in squad:

                player_image = get_player_image(
                    squad_player["id"]
                )


                c1, c2, c3 = st.columns(
                    [1, 4, 2]
                )


                with c1:

                    if player_image:

                        st.image(
                            player_image,
                            width=60
                        )

                    else:

                        st.write("🏏")


                with c2:

                    st.write(
                        f"**{squad_player['name']}**"
                    )

                    st.caption(
                        f"{squad_player['role']} • "
                        f"{squad_player['nationality']}"
                    )


                with c3:

                    sold_price = float(
                        squad_player.get(
                            "sold_price",
                            0
                        )
                    )

                    st.write(
                        f"💰 ₹{sold_price:.2f} Cr"
                    )

        else:

            st.write(
                "No players purchased yet."
            )


st.markdown("---")


# ============================================================
# AUCTION SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">📊 AUCTION SUMMARY</div>',
    unsafe_allow_html=True
)


total_players = len(players)

sold_players = sum(
    len(squad)
    for squad in st.session_state.squads.values()
)

remaining_players = (
    total_players - sold_players
)


total_spent = sum(
    sum(
        float(
            squad_player.get(
                "sold_price",
                0
            )
        )
        for squad_player in squad
    )
    for squad in st.session_state.squads.values()
)


a1, a2, a3, a4 = st.columns(4)


with a1:

    st.metric(
        "👥 Total Players",
        total_players
    )


with a2:

    st.metric(
        "✅ Sold",
        sold_players
    )


with a3:

    st.metric(
        "⏳ Remaining",
        remaining_players
    )


with a4:

    st.metric(
        "💰 Total Spent",
        f"₹{total_spent:.2f} Cr"
    )


st.markdown("---")


# ============================================================
# AUCTION RULES
# ============================================================

st.markdown(
    '<div class="section-title">📜 AUCTION RULES</div>',
    unsafe_allow_html=True
)

rule1, rule2, rule3 = st.columns(3)


with rule1:

    st.info(
        f"👥 Maximum squad size: "
        f"**{MAX_SQUAD_SIZE} players**"
    )


with rule2:

    st.info(
        f"🌍 Maximum overseas players: "
        f"**{MAX_OVERSEAS_PLAYERS}**"
    )


with rule3:

    st.info(
        f"💵 Minimum squad size target: "
        f"**{MIN_SQUAD_SIZE} players**"
    )


st.markdown("---")


# ============================================================
# RESET AUCTION
# ============================================================

st.markdown(
    '<div class="section-title">⚙️ AUCTION SETTINGS</div>',
    unsafe_allow_html=True
)

st.warning(
    "Resetting the auction removes all player purchases "
    "and restores every team's purse."
)


if st.button(
    "🔄 RESET ENTIRE AUCTION",
    use_container_width=True
):

    st.session_state.purses = {
        team["id"]: float(team["purse"])
        for team in teams
    }

    st.session_state.squads = {
        team["id"]: []
        for team in teams
    }

    st.session_state.current_player = None

    st.session_state.current_bid = 0.0

    st.session_state.highest_team = None

    st.session_state.auction_started = False

    st.session_state.last_result = (
        "🔄 Auction reset successfully."
    )


    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center;">

        🏏 <b>IPL Mock Auction</b>

        <br><br>

        Build Your Dream Squad • Bid Smart • Win the Auction

    </div>
    """,
    unsafe_allow_html=True
)