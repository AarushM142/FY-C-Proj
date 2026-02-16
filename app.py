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
        print("DEBUG: No user in session_state, cannot sync")
        return False
    
    try:
        user_id = st.session_state.user.id
        balance = int(st.session_state.balance)
        
        print(f"DEBUG: Syncing balance - User: {user_id}, Balance: {balance}")
        
        # Use upsert to create or update the profile
        response = supabase.table("profiles").upsert({
            "id": user_id,
            "balance": balance
        }).execute()
        
        print(f"DEBUG: Upsert response data: {response.data}")
        
        if response.data:
            print(f"DEBUG: Successfully synced balance ${balance} to Supabase")
            
            # Clear the balance-loaded flag so next page load fetches fresh from DB
            balance_flag = f"balance_loaded_{user_id}"
            if balance_flag in st.session_state:
                del st.session_state[balance_flag]
                print(f"DEBUG: Cleared balance-loaded flag for fresh DB fetch on next load")
            
            return True
        else:
            print(f"DEBUG: Upsert returned no data")
            return False
            
    except Exception as e:
        print(f"DEBUG: Error syncing balance to Supabase: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- 3. THE MAIN APP GUARD ---
if __name__ == "__main__":
    st.set_page_config(page_title="C-Engine Arcade", layout="wide")

    # Global CSS for the Casino Theme
    st.markdown("""
        <style>
        .stApp {
            background: radial-gradient(circle, #1a4d1a 0%, #0d260d 100%);
            color: white;
        }
        [data-testid="stSidebar"] {
            background-color: #050505 !important;
            border-right: 2px solid #FFD700;
        }
        .stMetric {
            background-color: rgba(0,0,0,0.4);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #FFD700;
        }
        </style>
    """, unsafe_allow_html=True)

    from auth import render_auth_page
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        print("DEBUG: No user in session_state, showing login page")
        render_auth_page(supabase)
        st.stop()
    else:
        print(f"DEBUG: User in session_state: {st.session_state.user.id}")

    # Init Balance - only fetch once per user session using a unique flag
    user_id = st.session_state.user.id
    balance_flag = f"balance_loaded_{user_id}"
    
    if balance_flag not in st.session_state:
        print(f"DEBUG: Balance not loaded for user {user_id}, fetching from DB")
        try:
            res = supabase.table("profiles").select("balance").eq("id", user_id).single().execute()
            print(f"DEBUG: Database response: {res}")
            if res.data and 'balance' in res.data:
                st.session_state.balance = res.data['balance']
                print(f"DEBUG: Fetched balance from DB: {st.session_state.balance}")
            else:
                print("DEBUG: No profile found in DB, defaulting to 1000")
                st.session_state.balance = 1000
        except Exception as e:
            print(f"DEBUG: Error fetching balance from DB: {e}")
            print("DEBUG: No profile exists yet, using default balance of 1000")
            st.session_state.balance = 1000
        
        # Mark this user's balance as loaded
        st.session_state[balance_flag] = True
    else:
        print(f"DEBUG: Balance already loaded for user {user_id}: {st.session_state.balance}")

    # Load Engines
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    game_lib = ctypes.CDLL(os.path.join(curr_dir, "game.dll"), winmode=0)
    game_lib.calculate_score.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
    game_lib.calculate_score.restype = ctypes.c_int
    ttt_lib = ctypes.CDLL(os.path.join(curr_dir, "tictactoe.dll"), winmode=0)
    ttt_lib.get_cell.argtypes = [ctypes.c_int, ctypes.c_int]
    ttt_lib.get_cell.restype = ctypes.c_char
    ttt_lib.place_move.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char]
    ttt_lib.place_move.restype = ctypes.c_int

    # Sidebar
    st.sidebar.title("🎰 ARCADE MENU")
    st.sidebar.metric("VAULT BALANCE", f"${st.session_state.balance}")
    
    # Add Logout Button
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    page = st.sidebar.radio("CHOOSE A TABLE", ["🏠 HOME", "🃏 BLACKJACK", "⭕ TIC-TAC-TOE"], key="nav_menu")

    if page == "🏠 HOME":
        st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 60px;'>THE GRAND ARCADE</h1>", unsafe_allow_html=True)
        st.info("Select a game in the sidebar. Your progress is synced to the cloud.")

    elif page == "🃏 BLACKJACK":
        if "phase" not in st.session_state: st.session_state.phase = "betting"
        if "payout_done" not in st.session_state: st.session_state.payout_done = False
        from blackjack import run_blackjack
        run_blackjack(game_lib)

    elif page == "⭕ TIC-TAC-TOE":
        from tictactoe_ui import run_tictactoe
        run_tictactoe(ttt_lib)