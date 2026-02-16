import streamlit as st
import ctypes

def run_tictactoe(ttt_lib):
    st.markdown("<h1 style='text-align: center; color: #00fbff; text-shadow: 0 0 10px #00fbff; margin-bottom: 5px;'>NEON TIC-TAC-TOE</h1>", unsafe_allow_html=True)
    
    # CSS to force the Streamlit columns to be tiny and centered
    st.markdown("""
        <style>
        /* 1. Squeeze the horizontal block to the center */
        [data-testid="stHorizontalBlock"] {
            justify-content: center !important;
            gap: 2px !important; /* Spacing between columns */
        }

        /* 2. Force columns to be only as wide as the button (100px) */
        [data-testid="column"] {
            flex: 0 1 100px !important;
            min-width: 100px !important;
        }

        /* 3. Button Styling */
        div.stButton > button {
            width: 100px !important;
            height: 100px !important;
            font-size: 45px !important;
            background-color: #1a1a1a !important;
            border: 2px solid #00fbff !important;
            color: white !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        div.stButton > button:hover {
            box-shadow: 0 0 15px #00fbff !important;
            background-color: #003333 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if 'ttt_turn' not in st.session_state:
        st.session_state.ttt_turn = 'X'
        st.session_state.ttt_active = True
        st.session_state.ttt_winner = None
        ttt_lib.init_ttt()

    # --- THE TIGHT GRID ---
    # Loop through rows
    for r in range(3):
        # Create 3 columns for each row to force horizontal alignment
        cols = st.columns(3)
        for c in range(3):
            cell_raw = ttt_lib.get_cell(r, c)
            cell_value = cell_raw.decode('utf-8', errors='ignore')
            label = cell_value if cell_value != ' ' else " "
            
            # Place button in the respective column
            if cols[c].button(label, key=f"ttt_{r}_{c}", disabled=not st.session_state.ttt_active or cell_value != ' '):
                ttt_lib.place_move(r, c, st.session_state.ttt_turn.encode('utf-8')[0])
                
                if ttt_lib.check_win():
                    st.session_state.ttt_winner = st.session_state.ttt_turn
                    st.session_state.ttt_active = False
                elif ttt_lib.check_draw():
                    st.session_state.ttt_winner = "Draw"
                    st.session_state.ttt_active = False
                else:
                    st.session_state.ttt_turn = 'O' if st.session_state.ttt_turn == 'X' else 'X'
                st.rerun()

    # --- STATUS AREA ---
    st.markdown("<br>", unsafe_allow_html=True)
    # Centering the status messages
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if st.session_state.ttt_winner:
            if st.session_state.ttt_winner == "Draw":
                st.warning("🤝 DRAW!")
            else:
                st.success(f"🎉 PLAYER {st.session_state.ttt_winner} WINS!")
            if st.button("PLAY AGAIN", use_container_width=True):
                st.session_state.ttt_active = True
                st.session_state.ttt_winner = None
                st.session_state.ttt_turn = 'X'
                ttt_lib.init_ttt()
                st.rerun()
        else:
            st.info(f"TURN: PLAYER {st.session_state.ttt_turn}")