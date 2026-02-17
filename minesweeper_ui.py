import streamlit as st

def run_minesweeper(lib):
    # --- 🛡️ INITIALIZATION ---
    if 'ms_ptr' not in st.session_state:
        st.session_state.ms_ptr = lib.create_game()
        st.session_state.ms_status = "playing"
        st.session_state.prev_revealed = 0
        st.session_state.flood_msg = None

    st.markdown("<h1 style='text-align: center; color: #FFD700;'>💣 MINESWEEPER</h1>", unsafe_allow_html=True)

    # Tabs for Gameplay and Leaderboards
    tab1, tab2, tab3 = st.tabs(["🎮 Play", "🌟 Hall of Fame", "💀 Wall of Shame"])

    with tab1:
        if st.session_state.flood_msg:
            st.toast(st.session_state.flood_msg)
            st.session_state.flood_msg = None 

        is_locked = st.session_state.ms_status != "playing"

        # Render 6x6 Grid
        for r in range(6):
            cols = st.columns(6)
            for c in range(6):
                with cols[c]:
                    revealed = lib.is_cell_revealed(st.session_state.ms_ptr, r, c)
                    is_mine = lib.is_cell_mine(st.session_state.ms_ptr, r, c)
                    
                    # Show content if revealed or if game is lost (to show where mines were)
                    show_content = revealed or (st.session_state.ms_status == "lost" and is_mine)
                    
                    if show_content:
                        label = "💣" if is_mine else str(lib.get_adjacent_count(st.session_state.ms_ptr, r, c))
                        st.button(label, key=f"cell_{r}_{c}", disabled=True, use_container_width=True)
                    else:
                        if st.button("❓", key=f"btn_{r}_{c}", use_container_width=True, disabled=is_locked):
                            res = lib.process_move(st.session_state.ms_ptr, r, c)
                            
                            # Update Statistics Logic
                            current_revealed = 0
                            for i in range(6):
                                for j in range(6):
                                    if lib.is_cell_revealed(st.session_state.ms_ptr, i, j):
                                        current_revealed += 1
                            
                            cleared_this_turn = current_revealed - st.session_state.prev_revealed
                            st.session_state.prev_revealed = current_revealed

                            if res == 0: # Safe Move
                                if cleared_this_turn > 1:
                                    st.session_state.flood_msg = f"🌊 Flood Fill! +{cleared_this_turn} cells"
                                sync_minesweeper_stats(cells_delta=cleared_this_turn)
                            
                            elif res == -1: # Hit Mine
                                st.session_state.ms_status = "lost"
                                sync_minesweeper_stats(mines_delta=1)
                            
                            elif res == 2: # Win
                                st.session_state.ms_status = "won"
                            
                            st.rerun()

        if st.session_state.ms_status == "lost":
            st.error("💀 BOOM! You've been added to the Wall of Shame.")
            if st.button("Re-deploy 🚁", use_container_width=True):
                reset_minesweeper()
        elif st.session_state.ms_status == "won":
            st.balloons()
            st.success("🏆 Clear! You survived the field.")
            if st.button("Next Mission 🚩", use_container_width=True):
                reset_minesweeper()

    with tab2:
        st.subheader("🌟 Hall of Fame (Cells Cleared)")
        display_ms_leaderboard("cells_cleared", "Total Cells")

    with tab3:
        st.subheader("💀 Wall of Shame (Mines Hit)")
        display_ms_leaderboard("mines_hit", "Mines Hit")

# --- DATABASE & UTILITY HELPERS ---

def reset_minesweeper():
    if 'ms_ptr' in st.session_state:
        del st.session_state.ms_ptr
    st.session_state.ms_status = "playing"
    st.session_state.prev_revealed = 0
    st.rerun()

def sync_minesweeper_stats(cells_delta=0, mines_delta=0):
    from app import supabase
    try:
        user_id = st.session_state.user.id
        # Fetch existing stats
        res = supabase.table("profiles").select("cells_cleared, mines_hit").eq("id", user_id).single().execute()
        cur_cells = res.data.get('cells_cleared', 0) or 0
        cur_mines = res.data.get('mines_hit', 0) or 0
        
        # Update with new deltas
        supabase.table("profiles").update({
            "cells_cleared": cur_cells + cells_delta,
            "mines_hit": cur_mines + mines_delta
        }).eq("id", user_id).execute()
    except Exception as e:
        print(f"Stat Sync Error: {e}")

def display_ms_leaderboard(column, label):
    from app import supabase
    try:
        # Fetch top 5
        res = supabase.table("profiles").select("email, " + column).order(column, desc=True).limit(5).execute()
        if res.data:
            for idx, row in enumerate(res.data, 1):
                val = row.get(column, 0)
                st.write(f"**{idx}.** {row['email']} — `{val}` {label}")
    except:
        st.write("Leaderboard currently unavailable.")