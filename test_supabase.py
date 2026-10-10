import streamlit as st
from supabase import create_client

st.title("IPL Auction - Database Connection Test")

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

    result = (
        supabase
        .table("auction_rooms")
        .select("id")
        .limit(1)
        .execute()
    )

    st.success("Supabase connection successful!")
    st.write("Your auction_rooms table is accessible.")

except Exception as e:
    st.error("Connection failed. Check your settings and database.")
    st.code(str(e))