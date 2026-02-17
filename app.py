import streamlit as st
import ctypes
import os
import platform
from supabase import create_client

# --- 1. SUPABASE SETUP ---
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
except Exception:
    st.error("Missing Secrets! Add SUPABASE_URL and SUPABASE_KEY to Streamlit Secrets.")
    st.stop()

# --- 2. DATA SYNC HELPER ---
def sync_balance_to_db():
    if 'user' not in st.session_state or not st.session_state.user:
        return False
    try:
        user_id = st.session_state.user.id
        balance = int(st.session_state.balance)
        supabase.table("profiles").upsert({
            "id": user_id,
            "balance": balance
        }).execute()
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
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
                    st.info("🕒 Submitted! The Pit Boss will review it shortly.")
                except Exception:
                    st.error("This ID has already been used.")
            else:
                st.error("UTR must be at least 10 digits.")

# --- 4. MAIN APP ---
if __name__ == "__main__":
    st.set_page_config(page_title="C-Engine Arcade", layout="wide")

    # Casino Theme CSS
    st.markdown("""
        <style>
        .stApp { background: radial-gradient(circle, #1a4d1a 0%, #0d260d 100%); color: white; }
        [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #FFD700; }
        .stMetric { background-color: rgba(0,0,0,0.4); padding: 15px; border-radius: 10px; border: 1px solid #FFD700; }
        </style>
    """, unsafe_allow_html=True)

    from auth import render_auth_page
    if 'user' not in st.session_state:
        render_auth_page(supabase)
        st.stop()

    # Load Balance & Notifications
    user_id = st.session_state.user.id
    balance_flag = f"balance_loaded_{user_id}"
    
    if balance_flag not in st.session_state:
        try:
            res = supabase.table("profiles").select("balance").eq("id", user_id).single().execute()
            st.session_state.balance = res.data['balance'] if res.data else 1000
            st.session_state[balance_flag] = True
            
            # Notification logic for approved payments
            check = supabase.table("payment_claims").select("*").eq("user_id", user_id).eq("status", "approved").execute()
            if check.data:
                st.toast("💰 Payment Approved! Welcome to the High Roller Club.", icon="💎")
        except:
            st.session_state.balance = 1000

    # --- CROSS-PLATFORM ENGINE LOADER ---
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    is_windows = platform.system() == "Windows"
    game_ext = "game.dll" if is_windows else "game.so"
    ttt_ext = "tictactoe.dll" if is_windows else "tictactoe.so"

    try:
        # Game Lib
        game_path = os.path.join(curr_dir, game_ext)
        game_lib = ctypes.CDLL(game_path if is_windows else os.path.abspath(game_path))
        game_lib.calculate_score.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        game_lib.calculate_score.restype = ctypes.c_int

        # TTT Lib
        ttt_path = os.path.join(curr_dir, ttt_ext)
        ttt_lib = ctypes.CDLL(ttt_path if is_windows else os.path.abspath(ttt_path))
        ttt_lib.get_cell.argtypes = [ctypes.c_int, ctypes.c_int]
        ttt_lib.get_cell.restype = ctypes.c_int # Using int for ASCII safety
        ttt_lib.place_move.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char]
        ttt_lib.place_move.restype = ctypes.c_int
    except Exception as e:
        st.error(f"Critical Error: Could not load C-Engines. Details: {e}")
        st.stop()

    # Sidebar UI
    st.sidebar.title("🎰 ARCADE MENU")
    st.sidebar.metric("VAULT BALANCE", f"${st.session_state.balance:,}")
    
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    # Navigation
    page = st.sidebar.radio("CHOOSE A TABLE", ["🏠 HOME", "🃏 BLACKJACK", "⭕ TIC-TAC-TOE"])

    # Admin Panel Logic
    ADMIN_EMAIL = "freshlettucev5@gmail.com"
    if st.session_state.user.email == ADMIN_EMAIL:
        st.sidebar.markdown("---")
        if st.sidebar.button("🛠️ ADMIN VAULT", type="primary", use_container_width=True):
            st.session_state.show_admin = not st.session_state.get("show_admin", False)

    render_high_roller_menu()

    # Admin Panel Display
    if st.session_state.get("show_admin"):
        st.divider()
        st.header("🕵️ Pit Boss Panel")
        claims = supabase.table("payment_claims").select("*").eq("status", "pending").execute()
        if not claims.data:
            st.write("No pending transactions.")
        else:
            for claim in claims.data:
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{claim['user_email']}** | UTR: `{claim['transaction_id']}`")
                if c2.button("✅ Approve", key=f"a_{claim['id']}"):
                    u_prof = supabase.table("profiles").select("balance").eq("id", claim['user_id']).single().execute()
                    new_bal = (u_prof.data['balance'] or 0) + 1000000
                    supabase.table("profiles").update({"balance": new_bal}).eq("id", claim['user_id']).execute()
                    supabase.table("payment_claims").update({"status": "approved"}).eq("id", claim['id']).execute()
                    st.success("Approved!")
                    st.rerun()
                if c3.button("❌ Reject", key=f"r_{claim['id']}"):
                    supabase.table("payment_claims").update({"status": "rejected"}).eq("id", claim['id']).execute()
                    st.rerun()

    # Page Routing
    if page == "🏠 HOME":
        st.title("THE GRAND ARCADE")
        st.markdown("### Welcome to the C-Engine Powered Arcade.")
        st.info("Select a game from the sidebar to start playing. High Roller top-ups require manual admin approval.")
    
    elif page == "🃏 BLACKJACK":
        if "phase" not in st.session_state:
            st.session_state.phase = "betting"
        from blackjack import run_blackjack
        run_blackjack(game_lib)
        
    elif page == "⭕ TIC-TAC-TOE":
        from tictactoe_ui import run_tictactoe
        run_tictactoe(ttt_lib)