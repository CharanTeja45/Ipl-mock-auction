import random
import string

import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="IPL Mock Auction - Lobby",
    page_icon="🏏",
    layout="centered",
)

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at top left, #172e50, transparent 55%),
        #0b1020;
    color: white;
}
.block-container {
    max-width: 850px;
    padding-top: 3rem;
}
h1, h2, h3 {
    color: white !important;
}
.stButton > button {
    min-height: 45px;
    border-radius: 12px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

try:
    supabase = get_supabase()
except Exception:
    st.error("Could not connect to Supabase. Check your secrets.toml file.")
    st.stop()

if "room_code" not in st.session_state:
    st.session_state.room_code = None

if "player_name" not in st.session_state:
    st.session_state.player_name = None

st.markdown("""
<div style="
    text-align:center;
    padding:30px 15px;
    border-radius:20px;
    background:linear-gradient(120deg,#172e50,#28204b);
    border:1px solid #405576;
">
    <div style="font-size:3rem;">🏏</div>
    <div style="font-size:2.2rem;font-weight:900;">
        IPL MOCK AUCTION
    </div>
    <p style="color:#c1cde0;">
        Create a room, invite your friends and build your dream team.
    </p>
</div>
""", unsafe_allow_html=True)

st.write("")
create_tab, join_tab = st.tabs(["➕ Create Room", "🚪 Join Room"])

def generate_room_code():
    for _ in range(20):
        code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        result = (
            supabase.table("auction_rooms")
            .select("room_code")
            .eq("room_code", code)
            .execute()
        )
        if not result.data:
            return code

    raise RuntimeError("Could not generate a room code.")

with create_tab:
    st.subheader("Create a new auction")

    with st.form("create_room_form"):
        host_name = st.text_input("Your name")
        create_clicked = st.form_submit_button(
            "🏏 Create Auction Room",
            use_container_width=True,
        )

    if create_clicked:
        host_name = host_name.strip()

        if not host_name:
            st.error("Please enter your name.")
        else:
            try:
                code = generate_room_code()

                result = (
                    supabase.table("auction_rooms")
                    .insert({
                        "room_code": code,
                        "host_name": host_name,
                        "status": "waiting",
                    })
                    .execute()
                )

                if result.data:
                    supabase.table("auction_participants").insert({
                        "room_code": code,
                        "player_name": host_name,
                        "team_id": None,
                    }).execute()

                    st.session_state.room_code = code
                    st.session_state.player_name = host_name
                    st.switch_page("pages/2_Auction_Room.py")

            except Exception as exc:
                st.error("Could not create the room.")
                st.caption(str(exc))

with join_tab:
    st.subheader("Join a friend's auction")
    st.caption(
        "You can join before the auction starts or while it is in progress. "
        "Late joiners can choose any IPL team that is still available."
    )

    with st.form("join_room_form"):
        join_name = st.text_input("Your name", key="join_name")
        join_code = st.text_input(
            "Room code",
            key="join_code",
            max_chars=6,
        )
        join_clicked = st.form_submit_button(
            "🚪 Enter Room",
            use_container_width=True,
        )

    if join_clicked:
        name = join_name.strip()
        code = join_code.strip().upper()

        if not name or not code:
            st.error("Enter both your name and room code.")
        else:
            try:
                result = (
                    supabase.table("auction_rooms")
                    .select("room_code,host_name,status")
                    .eq("room_code", code)
                    .limit(1)
                    .execute()
                )

                room = result.data[0] if result.data else None

                if not room:
                    st.error("Room not found. Check the room code.")
                elif str(room.get("status") or "").strip().casefold() in {
                    "completed", "finished", "closed", "cancelled", "canceled"
                }:
                    st.error("This auction room is already closed.")
                else:
                    existing = (
                        supabase.table("auction_participants")
                        .select("player_name")
                        .eq("room_code", code)
                        .execute()
                    )

                    names = existing.data or []
                    duplicate = any(
                        str(p.get("player_name") or "").strip().casefold()
                        == name.casefold()
                        for p in names
                    )

                    if duplicate:
                        st.error("That name is already in this room. Use a different name.")
                    else:
                        supabase.table("auction_participants").insert({
                            "room_code": code,
                            "player_name": name,
                            "team_id": None,
                        }).execute()

                        st.session_state.room_code = code
                        st.session_state.player_name = name
                        st.switch_page("pages/2_Auction_Room.py")

            except Exception as exc:
                st.error("Could not join the room.")
                st.caption(str(exc))

st.caption(
    "Create a room or join with a friend's six-character room code. "
    "Joining remains open while the auction is running."
)
