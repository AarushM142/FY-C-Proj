import streamlit as st
import ctypes
import os
from supabase import create_client

# --- 1. SUPABASE SETUP ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception:
    st.error("Check your .streamlit/secrets.toml!")
    st.stop()

# --- 2. DATA SYNC HELPER ---
def sync_balance_to_db():
    if 'user' not in st.session_state or not st.session_state.user:
        return False
    try:
        user_id = st.session_state.user.id
        balance = int(st.session_state.balance)
        supabase.table("profiles").update({"balance": balance}).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Sync Error: {e}")
        return False

# --- 3. HIGH ROLLER MENU ---
def render_high_roller_menu():
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='color: #FFD700; text-align: center;'>💎 HIGH ROLLER VAULT</h3>", unsafe_allow_html=True)
    
    upi_id = "am2007144-1@okicici" 
    upi_url = f"upi://pay?pa={upi_id}&pn=ArcadeGate&am=1&cu=INR&tn=ArcadeMillionaire"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={upi_url}"

    tab_mobile, tab_desktop = st.sidebar.tabs(["📱 MOBILE", "💻 DESKTOP"])
    with tab_mobile:
        st.markdown(f'<a href="{upi_url}"><div style="background: linear-gradient(45deg, #FFD700, #FFA500); color: black; text-align: center; padding: 12px; border-radius: 8px; font-weight: bold;">📲 OPEN UPI APP (₹1)</div></a>', unsafe_allow_html=True)
    with tab_desktop:
        st.image(qr_url, caption="Scan to Pay", use_container_width=True)

    with st.sidebar.expander("✅ I have paid! Claim credits"):
        txn_id = st.text_input("Enter Transaction ID (UTR)")
        if st.button("SUBMIT FOR REVIEW", use_container_width=True):
            if len(txn_id) >= 10:
                try:
                    supabase.table("payment_claims").insert({
                        "user_id": st.session_state.user.id,
                        "user_email": st.session_state.user.email,
                        "transaction_id": txn_id,
                        "status": "pending"
                    }).execute()
                    st.info("🕒 Submitted! Reviewing now.")
                except Exception:
                    st.error("This ID has already been used.")

# --- 4. MAIN APP ---
if __name__ == "__main__":
    st.set_page_config(page_title="C-Engine Arcade", layout="wide")

    # Theme
    st.markdown("<style>.stApp { background: radial-gradient(circle, #1a4d1a 0%, #0d260d 100%); color: white; } [data-testid='stSidebar'] { background-color: #050505 !important; border-right: 2px solid #FFD700; }</style>", unsafe_allow_html=True)

    from auth import render_auth_page
    if 'user' not in st.session_state:
        render_auth_page(supabase)
        st.stop()

    # Load Balance & Notifications
    user_id = st.session_state.user.id
    if f"balance_loaded_{user_id}" not in st.session_state:
        try:
            res = supabase.table("profiles").select("balance").eq("id", user_id).single().execute()
            st.session_state.balance = res.data['balance'] if res.data else 1000
            st.session_state[f"balance_loaded_{user_id}"] = True
            
            # Notification logic: check if any claim was approved since last login
            check = supabase.table("payment_claims").select("*").eq("user_id", user_id).eq("status", "approved").execute()
            if check.data:
                st.toast("💰 Payment Approved! Welcome to the High Roller Club.", icon="💎")
        except:
            st.session_state.balance = 1000

    # DLL Loading
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        game_lib = ctypes.CDLL(os.path.join(curr_dir, "game.dll"), winmode=0)
        ttt_lib = ctypes.CDLL(os.path.join(curr_dir, "tictactoe.dll"), winmode=0)
        ttt_lib.get_cell.restype = ctypes.c_int # Fix ASCII return
    except Exception as e:
        st.error(f"Engine Error: {e}"); st.stop()

    # Sidebar
    st.sidebar.title("🎰 ARCADE")
    st.sidebar.metric("VAULT BALANCE", f"${st.session_state.balance:,}")
    if st.sidebar.button("🚪 LOGOUT"):
        st.session_state.clear(); st.rerun()

    # Admin Panel
    ADMIN_EMAIL = "freshlettucev5@gmail.com"
    if st.session_state.user.email == ADMIN_EMAIL:
        st.sidebar.markdown("---")
        if st.sidebar.button("🛠️ ADMIN VAULT", type="primary"):
            st.session_state.show_admin = True

    render_high_roller_menu()

    if st.session_state.get("show_admin"):
        st.header("🕵️ Pit Boss Panel")
        claims = supabase.table("payment_claims").select("*").eq("status", "pending").execute()
        for claim in claims.data:
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{claim['user_email']}** | UTR: `{claim['transaction_id']}`")
            if c2.button("✅ Approve", key=f"a_{claim['id']}"):
                u_prof = supabase.table("profiles").select("balance").eq("id", claim['user_id']).single().execute()
                new_bal = (u_prof.data['balance'] or 0) + 1000000
                supabase.table("profiles").update({"balance": new_bal}).eq("id", claim['user_id']).execute()
                supabase.table("payment_claims").update({"status": "approved"}).eq("id", claim['id']).execute()
                st.rerun()
            if c3.button("❌ Reject", key=f"r_{claim['id']}"):
                supabase.table("payment_claims").update({"status": "rejected"}).eq("id", claim['id']).execute()
                st.rerun()
        if st.button("Close Admin"):
            st.session_state.show_admin = False; st.rerun()

    page = st.sidebar.radio("GAMES", ["🏠 HOME", "🃏 BLACKJACK", "⭕ TIC-TAC-TOE"])
    
    if page == "🏠 HOME":
        st.title("THE GRAND ARCADE")
    elif page == "🃏 BLACKJACK":
        # Initialize blackjack session state
        if "phase" not in st.session_state:
            st.session_state.phase = "betting"
        if "payout_done" not in st.session_state:
            st.session_state.payout_done = False
        if "split_active" not in st.session_state:
            st.session_state.split_active = False
        if "current_hand" not in st.session_state:
            st.session_state.current_hand = 0
        if "hands" not in st.session_state:
            st.session_state.hands = []
        if "player_hand" not in st.session_state:
            st.session_state.player_hand = []
        if "dealer_hand" not in st.session_state:
            st.session_state.dealer_hand = []
        if "bet" not in st.session_state:
            st.session_state.bet = 0
        if "ace_choice" not in st.session_state:
            st.session_state.ace_choice = None
        if "ace_choice_locked" not in st.session_state:
            st.session_state.ace_choice_locked = False
        
        from blackjack import run_blackjack
        run_blackjack(game_lib)
    elif page == "⭕ TIC-TAC-TOE":
        from tictactoe_ui import run_tictactoe
        run_tictactoe(ttt_lib)