import streamlit as st
import ctypes

def run_tictactoe(ttt_lib):
    st.markdown("<h1 style='text-align: center; color: #00fbff;'>TIC-TAC-TOE</h1>", unsafe_allow_html=True)

    # Pop-out styling (no layout/style changes, only enhancement)
    st.markdown("""
    <style>
    div.stButton > button {
        font-size: 40px;
        height: 100px;
        transition: all 0.15s ease-in-out;
        border-radius: 12px;
    }

    div.stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px #00fbff;
    }

    div.stButton > button:active {
        transform: scale(1.12);
        box-shadow: 0 0 25px #00fbff;
    }

    /* KEEP TEXT COLOR WHEN DISABLED */
    div.stButton > button:disabled {
        font-size: 45px;
        font-weight: bold;
        box-shadow: 0 0 20px #00fbff;
        color: #00fbff !important;
        -webkit-text-fill-color: #00fbff !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize game state
    if 'ttt_active' not in st.session_state:
        ttt_lib.init_ttt()
        st.session_state.ttt_active = True
        st.session_state.ttt_turn = 'X'
        st.session_state.ttt_winner = None

    # Reset Button - Always Visible
    col1, col2, col3 = st.columns([1, 2, 1])
    

    # Display current turn
    if st.session_state.ttt_active and not st.session_state.ttt_winner:
        st.markdown(
            f"<h3 style='text-align: center;'>Current Turn: {st.session_state.ttt_turn}</h3>",
            unsafe_allow_html=True
        )

    # Game Grid
    for r in range(3):
        cols = st.columns(3, gap="large")
        for c in range(3):
            with cols[c]:
                # Get cell value
                cell_raw = ttt_lib.get_cell(r, c)

                # Convert to string safely
                if isinstance(cell_raw, int):
                    cell_value = chr(cell_raw)
                elif isinstance(cell_raw, bytes):
                    cell_value = cell_raw.decode('utf-8', errors='replace').strip()
                else:
                    cell_value = str(cell_raw).strip()

                # Empty cells show as blank dot
                display_label = cell_value if cell_value.strip() and cell_value != ' ' else "·"

                # Disable logic
                is_empty = cell_value == ' ' or cell_value.strip() == ''
                is_disabled = (
                    not is_empty
                    or not st.session_state.ttt_active
                    or st.session_state.ttt_winner is not None
                )

                if st.button(
                    display_label,
                    key=f"ttt_{r}_{c}",
                    use_container_width=True,
                    disabled=is_disabled
                ):
                    # Place move
                    move_char = ord(st.session_state.ttt_turn)
                    ttt_lib.place_move(r, c, move_char)

                    # Check win
                    if ttt_lib.check_win():
                        st.session_state.ttt_winner = st.session_state.ttt_turn
                        st.session_state.ttt_active = False

                    # Check draw
                    elif ttt_lib.check_draw():
                        st.session_state.ttt_winner = "Draw"
                        st.session_state.ttt_active = False

                    # Switch turn
                    else:
                        st.session_state.ttt_turn = (
                            'O' if st.session_state.ttt_turn == 'X' else 'X'
                        )

                    st.rerun()
    with col2:
        if st.button("🔄 RESET BOARD", use_container_width=True):
            ttt_lib.init_ttt()
            st.session_state.ttt_active = True
            st.session_state.ttt_winner = None
            st.session_state.ttt_turn = 'X'
            st.rerun()

    # Result Section
    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.ttt_winner:
        if st.session_state.ttt_winner == "Draw":
            st.info("🤝 IT'S A DRAW!")
        else:
            st.success(f"🎉 PLAYER {st.session_state.ttt_winner} WINS!")

        # Play Again button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("▶️ PLAY AGAIN", use_container_width=True):
                ttt_lib.init_ttt()
                st.session_state.ttt_active = True
                st.session_state.ttt_winner = None
                st.session_state.ttt_turn = 'X'
                st.rerun()