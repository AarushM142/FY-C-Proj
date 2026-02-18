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
        st.markdown(f'''
            <a href="{upi_url}">
                <div style="background: linear-gradient(45deg, #FFD700, #FFA500); 
                color: black; text-align: center; padding: 12px; border-radius: 8px; font-weight: bold;">
                    📲 OPEN UPI APP (₹1) Win 1 Million! 
                </div>
            </a>''', unsafe_allow_html=True)
    with tab_desktop:
        st.image(qr_url, caption="Scan to Pay ₹1", use_container_width=True)

    with st.sidebar.expander("✅ I have paid!"):
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
                    st.info("🕒 Submitted for review.")
                except Exception:
                    st.error("This ID has already been used.")

# --- 4. MAIN APP LOGIC ---
if __name__ == "__main__":
    st.set_page_config(page_title="C-Engine Arcade", layout="wide", page_icon="🎰")

    # Casino Theme CSS
    st.markdown("""
        <style>
        .stApp { background: radial-gradient(circle, #1a4d1a 0%, #0d260d 100%); color: white; }
        [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #FFD700; }
        .stMetric { background-color: rgba(0,0,0,0.6); padding: 20px; border-radius: 15px; border: 2px solid #FFD700; text-align: center; }
        .admin-box { background-color: rgba(255, 215, 0, 0.1); border: 1px solid #FFD700; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # Auth
    from auth import render_auth_page
    if 'user' not in st.session_state:
        render_auth_page(supabase)
        st.stop()

    # Admin State Initialization
    if "show_admin" not in st.session_state:
        st.session_state.show_admin = False

    # Balance Sync
    user_id = st.session_state.user.id
    if "balance" not in st.session_state:
        try:
            res = supabase.table("profiles").select("balance").eq("id", user_id).single().execute()
            st.session_state.balance = res.data['balance'] if res.data else 1000
        except:
            st.session_state.balance = 1000

    # Engine Loaders
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    is_windows = platform.system() == "Windows"
    ext = ".dll" if is_windows else ".so"

    try:
        bj_lib = ctypes.CDLL(os.path.join(curr_dir, f"game{ext}"))
        ttt_lib = ctypes.CDLL(os.path.join(curr_dir, f"tictactoe{ext}"))
        ms_lib = ctypes.CDLL(os.path.join(curr_dir, f"minesweeper{ext}"))
        
        # MS 64-bit Pointer Setup
        ms_lib.create_game.restype = ctypes.c_void_p
        ms_lib.process_move.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        ms_lib.force_reveal.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    except Exception as e:
        st.error(f"Engine Failure: {e}")
        st.stop()

    # Sidebar Navigation
    st.sidebar.title("🎰 ARCADE")
    st.sidebar.metric("VAULT BALANCE", f"${st.session_state.balance:,}")
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    page = st.sidebar.radio("CHOOSE A TABLE", ["🏠 HOME", "🃏 BLACKJACK", "⭕ TIC-TAC-TOE", "💣 MINESWEEPER"])
    render_high_roller_menu()

    # --- PIT BOSS PANEL LOGIC ---
    ADMIN_EMAIL = "freshlettucev5@gmail.com"
    if st.session_state.user.email == ADMIN_EMAIL:
        st.sidebar.markdown("---")
        if st.sidebar.button("🛠️ PIT BOSS PANEL", type="primary", use_container_width=True):
            st.session_state.show_admin = not st.session_state.show_admin
            st.rerun()

    # Display Admin Panel if toggled ON
    if st.session_state.show_admin:
        st.markdown("### 🕵️ Pit Boss Panel")
        if st.button("❌ Close Admin Panel"):
            st.session_state.show_admin = False
            st.rerun()

        try:
            claims_res = supabase.table("payment_claims").select("*").eq("status", "pending").execute()
            claims = claims_res.data
            
            if not claims:
                st.info("No pending payment claims found.")
            else:
                for claim in claims:
                    with st.container():
                        st.markdown(f"""<div class="admin-box">
                            <strong>User:</strong> {claim['user_email']}<br>
                            <strong>UTR:</strong> <code>{claim['transaction_id']}</code>
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"Approve {claim['transaction_id'][-4:]}", key=f"claim_{claim['id']}"):
                            # Fetch user's current balance
                            u_prof = supabase.table("profiles").select("balance").eq("id", claim['user_id']).single().execute()
                            current_bal = u_prof.data['balance'] if u_prof.data else 0
                            
                            # Update balance and claim status
                            supabase.table("profiles").update({"balance": current_bal + 1000000}).eq("id", claim['user_id']).execute()
                            supabase.table("payment_claims").update({"status": "approved"}).eq("id", claim['id']).execute()
                            
                            st.success(f"Verified! $1M credited to {claim['user_email']}")
                            st.rerun()
        except Exception as e:
            st.error(f"Database Error: {e}")
        st.markdown("---")

    # --- ROUTING PAGES ---
    if page == "🏠 HOME":
        from minesweeper_ui import display_ms_leaderboard
        
        st.markdown("<h1 style='text-align: center; color: #FFD700;'>🏦 THE GLOBAL VAULT</h1>", unsafe_allow_html=True)
        
        # Big Balance Display
        st.markdown(f"""
            <div class="stMetric">
                <h2 style="margin:0; color:#FFD700;">YOUR CURRENT BALANCE</h2>
                <h1 style="margin:0; font-size: 50px;">${st.session_state.balance:,}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        # Leaderboards in a grid
        st.subheader("📊 Global Rankings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🃏 Blackjack Whales")
            st.caption("Top earners by balance")
            display_ms_leaderboard("balance", "Credits")

        with col2:
            st.markdown("### 💣 Minesweeper Pro")
            st.caption("Top cells cleared")
            display_ms_leaderboard("cells_cleared", "Cells")

        with col3:
            st.markdown("### 💀 Wall of Shame")
            st.caption("Most mines triggered")
            display_ms_leaderboard("mines_hit", "Mines")

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
