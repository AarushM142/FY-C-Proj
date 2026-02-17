import streamlit as st
import random
import ctypes

# --- ⚙️ CTYPES CONFIG ---
def setup_lib_types(lib):
    lib.create_game.restype = ctypes.c_void_p
    lib.is_cell_revealed.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.is_cell_mine.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.get_adjacent_count.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.process_move.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.force_reveal.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

# --- 🧠 EXPANDED LIFELINE CHALLENGE ---
def show_logic_challenge(lib):
    st.warning("💥 MINE HIT! Lifeline activated.")
    st.subheader("Solve this technical riddle to stay alive:")
    
    # Expanded Question Bank
    questions = [
        {"q": "In C, what is the output of printf('%d', 5 / 2)?", "a": "2", "options": ["2", "2.5", "3"]},
        {"q": "In Python, what is the result of True + True?", "a": "2", "options": ["1", "2", "True"]},
        {"q": "In C, which operator is used for 'address of'?", "a": "&", "options": ["**", "&", "->"]},
        {"q": "In Python, which is a mutable data type?", "a": "list", "options": ["tuple", "string", "list"]},
        {"q": "In C, what is the index of the last element in 'int arr[5]'?", "a": "4", "options": ["5", "4", "0"]},
        {"q": "What is the result of 10 % 3 in both C and Python?", "a": "1", "options": ["3", "1", "0"]},
        {"q": "In Python, how do you start a comment?", "a": "#", "options": ["//", "/*", "#"]}
    ]
    
    if 'current_q' not in st.session_state or st.session_state.current_q is None:
        st.session_state.current_q = random.choice(questions)
    
    q = st.session_state.current_q
    choice = st.radio(q["q"], q["options"])
    
    if st.button("SUBMIT ANSWER"):
        if choice == q["a"]:
            st.success("🎉 Correct! Second life granted.")
            r, c = st.session_state.last_clicked
            lib.force_reveal(st.session_state.ms_ptr, r, c)
            st.session_state.ms_status = "playing"
            st.session_state.current_q = None
            st.rerun()
        else:
            st.session_state.ms_status = "lost"
            sync_minesweeper_stats(mines_delta=1)
            st.session_state.current_q = None
            st.rerun()

# --- 🎮 GAME ENGINE ---
def run_minesweeper(lib):
    setup_lib_types(lib)
    if 'ms_ptr' not in st.session_state:
        st.session_state.ms_ptr = lib.create_game()
        st.session_state.ms_status = "playing"
        st.session_state.prev_revealed = 0
        st.session_state.flood_msg = None

    st.markdown("<h1 style='text-align: center; color: #FFD700;'>💣 MINESWEEPER</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🎮 Play", "🌟 Hall of Fame", "💀 Wall of Shame"])

    with tab1:
        if st.session_state.ms_status == "lost":
            st.error("💥 KABOOM! You hit the second mine. Wall of Shame for you.")
            if st.button("Re-deploy 🚁", use_container_width=True): reset_minesweeper()
        elif st.session_state.ms_status == "won":
            st.balloons()
            st.success("🏆 Mission Accomplished! You survived.")
            if st.button("Next Mission 🚩", use_container_width=True): reset_minesweeper()
        elif st.session_state.flood_msg:
            st.toast(st.session_state.flood_msg)
            st.session_state.flood_msg = None 

        if st.session_state.ms_status == "question":
            show_logic_challenge(lib)
            return

        is_locked = st.session_state.ms_status != "playing"

        for r in range(6):
            cols = st.columns(6)
            for c in range(6):
                with cols[c]:
                    revealed = lib.is_cell_revealed(st.session_state.ms_ptr, r, c)
                    is_mine = lib.is_cell_mine(st.session_state.ms_ptr, r, c)
                    show_content = revealed or (st.session_state.ms_status == "lost" and is_mine)
                    
                    if show_content:
                        label = "💣" if is_mine else str(lib.get_adjacent_count(st.session_state.ms_ptr, r, c))
                        st.button(label, key=f"cell_{r}_{c}", disabled=True, use_container_width=True)
                    else:
                        if st.button("❓", key=f"btn_{r}_{c}", use_container_width=True, disabled=is_locked):
                            st.session_state.last_clicked = (r, c)
                            before = get_revealed_count(lib)
                            res = lib.process_move(st.session_state.ms_ptr, r, c)
                            after = get_revealed_count(lib)
                            
                            cleared_this_turn = after - before
                            
                            if res == 1: # First mine
                                st.session_state.ms_status = "question"
                            elif res == -1: # Second mine
                                st.session_state.ms_status = "lost"
                                sync_minesweeper_stats(mines_delta=1)
                            elif res == 2: # Win
                                st.session_state.ms_status = "won"
                            else: # Safe Move
                                if cleared_this_turn > 1:
                                    st.session_state.flood_msg = f"🌊 Flood Fill! +{cleared_this_turn} cells"
                                sync_minesweeper_stats(cells_delta=cleared_this_turn)
                            
                            st.session_state.prev_revealed = after
                            st.rerun()

    with tab2:
        st.subheader("🌟 Hall of Fame")
        display_ms_leaderboard("cells_cleared", "Total Cells")

    with tab3:
        st.subheader("💀 Wall of Shame")
        display_ms_leaderboard("mines_hit", "Mines Hit")

# --- 🛠️ DATABASE & UTILS ---
def reset_minesweeper():
    if 'ms_ptr' in st.session_state: del st.session_state.ms_ptr
    st.session_state.ms_status = "playing"
    st.session_state.prev_revealed = 0
    st.rerun()

def get_revealed_count(lib):
    return sum(1 for r in range(6) for c in range(6) if lib.is_cell_revealed(st.session_state.ms_ptr, r, c))

def sync_minesweeper_stats(cells_delta=0, mines_delta=0):
    from app import supabase
    try:
        user_id = st.session_state.user.id
        res = supabase.table("profiles").select("cells_cleared, mines_hit").eq("id", user_id).single().execute()
        cur_cells = res.data.get('cells_cleared', 0) or 0
        cur_mines = res.data.get('mines_hit', 0) or 0
        supabase.table("profiles").update({
            "cells_cleared": cur_cells + cells_delta, 
            "mines_hit": cur_mines + mines_delta
        }).eq("id", user_id).execute()
    except Exception as e: print(f"Sync Error: {e}")

def display_ms_leaderboard(column, label):
    from app import supabase
    try:
        res = supabase.table("profiles").select(f"email, {column}").order(column, desc=True).limit(5).execute()
        if res.data:
            for idx, row in enumerate(res.data, 1):
                val = row.get(column, 0)
                st.write(f"**{idx}.** {row['email']} — `{val}` {label}")
        else: st.info("No data found.")
    except Exception as e: st.error(f"Leaderboard error: {e}")