import streamlit as st
import ctypes

def display_cards(hand, hide_second=False):
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    st.markdown("""
        <style>
        @keyframes slideIn { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        .card {
            animation: slideIn 0.4s ease-out;
            width: 80px; height: 120px; background: white; border-radius: 8px;
            margin: 10px; display: inline-block; position: relative;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.5); border: 1px solid #999;
            text-align: center; line-height: 120px; font-size: 30px; font-weight: bold;
        }
        .card-back { background: repeating-linear-gradient(45deg, #800, #800 10px, #600 10px, #600 20px); border: 2px solid #FFD700; }
        </style>
    """, unsafe_allow_html=True)

    html = '<div style="display: flex; flex-wrap: wrap; justify-content: center;">'
    for i, card in enumerate(hand):
        if hide_second and i == 1:
            html += '<div class="card card-back"></div>'
        else:
            r, s = ranks[card % 13], suits[card // 13]
            color = "#d32f2f" if s in ["♥", "♦"] else "#1a1a1a"
            html += f'<div class="card" style="color: {color};">{r}{s}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def run_blackjack(game_lib):
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>BLACKJACK 21</h1>", unsafe_allow_html=True)

    if st.session_state.phase == "betting":
        st.markdown("<h3 style='text-align: center;'>PLACE YOUR WAGER</h3>", unsafe_allow_html=True)
        cols = st.columns(4)
        amounts = [100, 500, 1000, "ALL IN"]
        for i, amt in enumerate(amounts):
            val = st.session_state.balance if amt == "ALL IN" else amt
            if cols[i].button(f"💰 ${amt}", use_container_width=True):
                if st.session_state.balance >= val:
                    st.session_state.balance -= val
                    st.session_state.bet = val
                    game_lib.init_engine()
                    st.session_state.player_hand = [game_lib.draw_card(), game_lib.draw_card()]
                    st.session_state.dealer_hand = [game_lib.draw_card(), game_lib.draw_card()]
                    st.session_state.phase = "playing"
                    st.session_state.payout_done = False
                    st.rerun()

    else:
        # Dealer Area
        st.markdown("<p style='text-align: center; letter-spacing: 3px; opacity: 0.7;'>DEALER</p>", unsafe_allow_html=True)
        display_cards(st.session_state.dealer_hand, hide_second=(st.session_state.phase == "playing"))
        
        # Player Area
        p_score = game_lib.calculate_score((ctypes.c_int * len(st.session_state.player_hand))(*st.session_state.player_hand), len(st.session_state.player_hand))
        st.markdown(f"<p style='text-align: center; letter-spacing: 3px;'>PLAYER: {p_score}</p>", unsafe_allow_html=True)
        display_cards(st.session_state.player_hand)

        if st.session_state.phase == "playing":
            c1, c2 = st.columns(2)
            if c1.button("HIT 🎴", use_container_width=True):
                st.session_state.player_hand.append(game_lib.draw_card())
                if game_lib.calculate_score((ctypes.c_int * len(st.session_state.player_hand))(*st.session_state.player_hand), len(st.session_state.player_hand)) > 21:
                    st.session_state.phase = "result"
                st.rerun()
            if c2.button("STAND ✋", use_container_width=True):
                d_arr = (ctypes.c_int * 10)(*st.session_state.dealer_hand)
                new_count = game_lib.dealer_logic(d_arr, len(st.session_state.dealer_hand))
                st.session_state.dealer_hand = list(d_arr)[:new_count]
                st.session_state.phase = "result"
                st.rerun()

        elif st.session_state.phase == "result":
            d_score = game_lib.calculate_score((ctypes.c_int * len(st.session_state.dealer_hand))(*st.session_state.dealer_hand), len(st.session_state.dealer_hand))
            
            if not st.session_state.payout_done:
                old_balance = st.session_state.balance
                
                if p_score <= 21 and (d_score > 21 or p_score > d_score):
                    st.session_state.balance += (st.session_state.bet * 2)
                    st.balloons()
                    print(f"DEBUG: Player won! Balance: {old_balance} -> {st.session_state.balance}")
                elif p_score <= 21 and p_score == d_score:
                    st.session_state.balance += st.session_state.bet
                    print(f"DEBUG: Push (tie)! Balance: {old_balance} -> {st.session_state.balance}")
                else:
                    print(f"DEBUG: Player lost. Balance remains: {st.session_state.balance}")
                
                print(f"DEBUG: About to call sync_balance_to_db() with balance={st.session_state.balance}")
                from app import sync_balance_to_db
                result = sync_balance_to_db()
                print(f"DEBUG: sync_balance_to_db() returned: {result}")
                st.session_state.payout_done = True

            # Final Result Banner
            if p_score > 21: st.error("❌ BUST! HOUSE WINS")
            elif d_score > 21: st.success("🎉 DEALER BUSTS! YOU WIN!")
            elif p_score > d_score: st.success(f"🏆 YOU WIN ${st.session_state.bet}!")
            elif p_score < d_score: st.error(f"💸 DEALER WINS ({d_score})")
            else: st.warning("🤝 PUSH - MONEY RETURNED")

            if st.button("COLLECT & NEXT HAND 🔄", use_container_width=True):
                st.session_state.phase = "betting"
                st.rerun()