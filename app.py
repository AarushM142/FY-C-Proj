import streamlit as st
import ctypes
import os
import platform
from supabase import create_client

# --- 1. SUPABASE SETUP ---
# Ensure these are set in your .streamlit/secrets.toml
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
        st.markdown(f'''
            <a href="{upi_url}">
                <div style="background: linear-gradient(45deg, #FFD700, #FFA500); 
                color: black; text-align: center; padding: 12px; border-radius: 8px; font-weight: bold;">
                    📲 OPEN UPI APP (₹1) Win 1 Million! 
                </div>
            </a>''', unsafe_allow_html=True)
    with tab_desktop:
        st.image(qr_url, caption="Scan to Pay ₹1", use_container_width=True)

    with st.sidebar.expander("✅ I have paid! Claim 1 Million Balance!"):
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

# --- 4. MAIN APP LOGIC ---
if __name__ == "__main__":
    st.set_page_config(page_title="C-Engine Arcade", layout="wide", page_icon="🎰")

    # Casino Theme CSS
    st.markdown("""
        <style>
        .stApp { background: radial-gradient(circle, #1a4d1a 0%, #0d260d 100%); color: white; }
        [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #FFD700; }
        .stMetric { background-color: rgba(0,0,0,0.4); padding: 15px; border-radius: 10px; border: 1px solid #FFD700; }
        </style>
    """, unsafe_allow_html=True)

    # Authentication Check
    from auth import render_auth_page
    if 'user' not in st.session_state:
        render_auth_page(supabase)
        st.stop()

    # Initial Balance Fetch
    user_id = st.session_state.user.id
    if "balance" not in st.session_state:
        try:
            res = supabase.table("profiles").select("balance").eq("id", user_id).single().execute()
            st.session_state.balance = res.data['balance'] if res.data else 1000
        except:
            st.session_state.balance = 1000

    # --- C-ENGINE LOADER ---
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    is_windows = platform.system() == "Windows"
    
    # Filenames
    bj_ext = "game.dll" if is_windows else "game.so"
    ttt_ext = "tictactoe.dll" if is_windows else "tictactoe.so"
    ms_ext = "minesweeper.dll" if is_windows else "minesweeper.so"

    try:
        # 1. Blackjack Engine
        bj_path = os.path.join(curr_dir, bj_ext)
        bj_lib = ctypes.CDLL(bj_path)
        
        # 2. Tic-Tac-Toe Engine
        ttt_path = os.path.join(curr_dir, ttt_ext)
        ttt_lib = ctypes.CDLL(ttt_path)

        # 3. Minesweeper Engine (Configured for 64-bit Pointers)
        ms_path = os.path.join(curr_dir, ms_ext)
        ms_lib = ctypes.CDLL(ms_path)
        
        # Explicitly define Minesweeper types to prevent OverflowError
        ms_lib.create_game.restype = ctypes.c_void_p
        ms_lib.is_cell_revealed.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        ms_lib.is_cell_mine.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        ms_lib.get_adjacent_count.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        ms_lib.process_move.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

    except Exception as e:
        st.error(f"Engine Failure: Ensure C files are compiled and names match. Error: {e}")
        st.stop()

    # Sidebar Navigation
    st.sidebar.title("🎰 ARCADE MENU")
    st.sidebar.metric("VAULT BALANCE", f"${st.session_state.balance:,}")
    
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    page = st.sidebar.radio("CHOOSE A TABLE", ["🏠 HOME", "🃏 BLACKJACK", "⭕ TIC-TAC-TOE", "💣 MINESWEEPER"])

    # Admin Panel (Secret Pit Boss Access)
    ADMIN_EMAIL = "freshlettucev5@gmail.com"
    if st.session_state.user.email == ADMIN_EMAIL:
        st.sidebar.markdown("---")
        if st.sidebar.button("🛠️ PIT BOSS PANEL", type="primary", use_container_width=True):
            st.session_state.show_admin = not st.session_state.get("show_admin", False)

    render_high_roller_menu()

    # Admin View logic
    if st.session_state.get("show_admin"):
        st.divider()
        st.header("🕵️ Pit Boss: Payment Verification")
        claims = supabase.table("payment_claims").select("*").eq("status", "pending").execute()
        
        if not claims.data:
            st.info("No pending claims.")
        
        for claim in claims.data:
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**User:** {claim['user_email']} <br> **UTR:** `{claim['transaction_id']}`", unsafe_allow_html=True)
            if c2.button("✅ Approve", key=f"a_{claim['id']}"):
                u_prof = supabase.table("profiles").select("balance").eq("id", claim['user_id']).single().execute()
                new_bal = (u_prof.data['balance'] or 0) + 1000000
                supabase.table("profiles").update({"balance": new_bal}).eq("id", claim['user_id']).execute()
                supabase.table("payment_claims").update({"status": "approved"}).eq("id", claim['id']).execute()
                st.success("Balance Updated!")
                st.rerun()
            if c3.button("❌ Reject", key=f"r_{claim['id']}"):
                supabase.table("payment_claims").update({"status": "rejected"}).eq("id", claim['id']).execute()
                st.rerun()

    # Page Routing
    if page == "🏠 HOME":
        st.title("THE GRAND C-ENGINE ARCADE")
        st.markdown("Welcome to the most efficient arcade on the web, powered by high-performance C engines.")
        st.image("https://images.unsplash.com/photo-1596838132731-3301c3fd4317?q=80&w=2070", caption="Step up to the table.")

    elif page == "🃏 BLACKJACK":
        from blackjack import run_blackjack
        run_blackjack(bj_lib)
        sync_balance_to_db()
        
    elif page == "⭕ TIC-TAC-TOE":
        from tictactoe_ui import run_tictactoe
        run_tictactoe(ttt_lib)

    elif page == "💣 MINESWEEPER":
        from minesweeper_ui import run_minesweeper
        run_minesweeper(ms_lib)