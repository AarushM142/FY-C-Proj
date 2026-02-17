import streamlit as st
import ctypes

def display_cards(hand, hide_second=False):
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    st.markdown("""
        <style>
        @keyframes slideIn { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 10px #FFD700, 0 0 20px #FFD700; } 50% { box-shadow: 0 0 20px #FFD700, 0 0 30px #FFD700; } }
        .card {
            animation: slideIn 0.4s ease-out;
            width: 80px; height: 120px; background: white; border-radius: 8px;
            margin: 10px; display: inline-block; position: relative;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.5); border: 1px solid #999;
            text-align: center; line-height: 120px; font-size: 30px; font-weight: bold;
        }
        .card-back { background: repeating-linear-gradient(45deg, #800, #800 10px, #600 10px, #600 20px); border: 2px solid #FFD700; }
        .glow-button { animation: glow 1.5s ease-in-out infinite; }
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
    # --- 🛡️ BUG FIX: INITIALIZE SESSION STATE ---
    if "phase" not in st.session_state:
        st.session_state.phase = "betting"
    if "balance" not in st.session_state:
        st.session_state.balance = 1000
    if "player_hand" not in st.session_state:
        st.session_state.player_hand = []
    if "dealer_hand" not in st.session_state:
        st.session_state.dealer_hand = []
    if "hands" not in st.session_state:
        st.session_state.hands = []
    if "current_hand" not in st.session_state:
        st.session_state.current_hand = 0
    if "split_active" not in st.session_state:
        st.session_state.split_active = False
    if "ace_choice_locked" not in st.session_state:
        st.session_state.ace_choice_locked = False
    if "payout_done" not in st.session_state:
        st.session_state.payout_done = False
    # --------------------------------------------

    st.markdown("<h1 style='text-align: center; color: #FFD700;'>BLACKJACK 21</h1>", unsafe_allow_html=True)
    # ... rest of your code ...
    
    

    if st.session_state.phase == "betting":
        st.markdown("<h3 style='text-align: center;'>PLACE YOUR WAGER</h3>", unsafe_allow_html=True)
        cols = st.columns(4)
        amounts = [100, 500, 1000, "ALL IN"]
        insufficient_funds_shown = False
        
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
                    st.session_state.split_active = False
                    st.session_state.current_hand = 0
                    st.session_state.hands = [st.session_state.player_hand]
                    st.session_state.ace_choice = None  # None means not yet chosen
                    st.session_state.ace_choice_locked = False  # Lock choice after selection
                    st.rerun()
                else:
                    insufficient_funds_shown = True
        
        if insufficient_funds_shown:
            st.error(f"❌ Insufficient funds! You need ${val} but only have ${st.session_state.balance}")
        
        # Reset Balance Button
        st.markdown("<p style='text-align: center; opacity: 0.5; margin-top: 20px;'>—</p>", unsafe_allow_html=True)
        if st.button("🔄 RESET BALANCE TO $1000", use_container_width=True):
            st.session_state.balance = 1000
            from app import sync_balance_to_db
            sync_balance_to_db()
            st.rerun()
        
        # Leaderboard Section
        st.markdown("<hr style='margin-top: 40px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #FFD700;'>🏆 LEADERBOARD 🏆</h3>", unsafe_allow_html=True)
        
        try:
            from app import supabase
            
            # Fetch top 10 users by balance
            response = supabase.table("profiles").select("email, balance").order("balance", desc=True).limit(10).execute()
            
            if response.data and len(response.data) > 0:
                leaderboard_data = []
                for idx, user in enumerate(response.data, 1):
                    email = user.get('email', 'Unknown')
                    balance = user.get('balance', 0)
                    leaderboard_data.append({"Rank": idx, "Player": email, "Balance": f"${balance:,}"})
                
                st.dataframe(
                    leaderboard_data,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn(width=80),
                        "Player": st.column_config.TextColumn(width=200),
                        "Balance": st.column_config.TextColumn(width=150),
                    }
                )
            else:
                st.info("No players on leaderboard yet.")
        except Exception as e:
            st.warning(f"⚠️ Could not load leaderboard: {str(e)}")

    else:
        # Dealer Area
        st.markdown("<p style='text-align: center; letter-spacing: 3px; opacity: 0.7;'>DEALER</p>", unsafe_allow_html=True)
        display_cards(st.session_state.dealer_hand, hide_second=(st.session_state.phase == "playing"))
        
        # Player Area
        if st.session_state.split_active:
            # Show both split hands
            cols = st.columns(2)
            for hand_idx in range(len(st.session_state.hands)):
                with cols[hand_idx]:
                    current_hand = st.session_state.hands[hand_idx]
                    p_score = game_lib.calculate_score((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand))
                    hand_label = "PLAYER (HAND 1)" if hand_idx == 0 else "PLAYER (HAND 2)"
                    if hand_idx == st.session_state.current_hand:
                        st.markdown(f"<p style='text-align: center; letter-spacing: 3px; color: #FFD700;'>{hand_label}: {p_score} 👈</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='text-align: center; letter-spacing: 3px;'>{hand_label}: {p_score}</p>", unsafe_allow_html=True)
                    display_cards(current_hand)
        else:
            # Single hand
            current_hand = st.session_state.hands[st.session_state.current_hand]
            
            # Calculate score with locked ace choice if available
            if game_lib.has_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand)):
                if st.session_state.ace_choice_locked:
                    p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), st.session_state.ace_choice)
                else:
                    # Show both options if not locked
                    p_score_as_1 = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 1)
                    p_score_as_11 = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 11)
                    p_score = p_score_as_11  # Display best option
            else:
                p_score = game_lib.calculate_score((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand))
            
            st.markdown(f"<p style='text-align: center; letter-spacing: 3px;'>PLAYER: {p_score}</p>", unsafe_allow_html=True)
            display_cards(current_hand)

        if st.session_state.phase == "playing":
            # Get current playing hand
            current_hand = st.session_state.hands[st.session_state.current_hand]
            
            # Check if hand has an Ace and choice hasn't been locked
            has_ace_in_hand = game_lib.has_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand))
            
            if has_ace_in_hand and not st.session_state.ace_choice_locked:
                st.warning("⚠️ You have an Ace! Choose whether it counts as 1 or 11 to continue")
                
                p_score_as_1 = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 1)
                p_score_as_11 = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 11)
                
                ace_cols = st.columns(2)
                
                if ace_cols[0].button(f"🌟 Ace = 1 ({p_score_as_1})", use_container_width=True, key="ace_as_1"):
                    st.session_state.ace_choice = 1
                    st.session_state.ace_choice_locked = True
                    st.rerun()
                
                if ace_cols[1].button(f"🌟 Ace = 11 ({p_score_as_11})", use_container_width=True, key="ace_as_11"):
                    st.session_state.ace_choice = 11
                    st.session_state.ace_choice_locked = True
                    st.rerun()
                
                st.stop()  # Stop execution until Ace choice is made
            
            # Calculate score with locked ace choice
            if has_ace_in_hand and st.session_state.ace_choice_locked:
                p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), st.session_state.ace_choice)
                
                # Show locked choice with glow
                p_score_as_1 = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 1)
                p_score_as_11 = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 11)
                
                st.markdown("<p style='text-align: center; opacity: 0.7;'>Your Ace choice (locked):</p>", unsafe_allow_html=True)
                ace_cols = st.columns(2)
                
                if st.session_state.ace_choice == 1:
                    ace_cols[0].markdown(f"<div class='glow-button' style='padding: 10px; border-radius: 5px; background: #1a4d1a; border: 2px solid #FFD700; text-align: center;'>✨ Ace = 1 ({p_score_as_1})</div>", unsafe_allow_html=True)
                    ace_cols[1].markdown(f"<div style='padding: 10px; border-radius: 5px; text-align: center; opacity: 0.5;'>Ace = 11 ({p_score_as_11})</div>", unsafe_allow_html=True)
                else:
                    ace_cols[0].markdown(f"<div style='padding: 10px; border-radius: 5px; text-align: center; opacity: 0.5;'>Ace = 1 ({p_score_as_1})</div>", unsafe_allow_html=True)
                    ace_cols[1].markdown(f"<div class='glow-button' style='padding: 10px; border-radius: 5px; background: #1a4d1a; border: 2px solid #FFD700; text-align: center;'>✨ Ace = 11 ({p_score_as_11})</div>", unsafe_allow_html=True)
            else:
                p_score = game_lib.calculate_score((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand))
            
            # Check for natural blackjack on first two cards
            if len(current_hand) == 2 and p_score == 21:
                st.success("🎉 BLACKJACK! 21 with two cards!")
            
            c1, c2, c3, c4 = st.columns(4)
            
            # HIT button
            if c1.button("HIT 🎴", use_container_width=True):
                current_hand.append(game_lib.draw_card())
                
                # Check for bust with current ace choice
                if game_lib.has_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand)):
                    if st.session_state.ace_choice_locked:
                        p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), st.session_state.ace_choice)
                    else:
                        # Try with 11 first
                        p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 11)
                else:
                    p_score = game_lib.calculate_score((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand))
                
                if p_score > 21:
                    # Move to next hand or result
                    if st.session_state.split_active and st.session_state.current_hand == 0:
                        st.session_state.current_hand = 1
                        st.session_state.ace_choice_locked = False  # Reset for next hand
                        st.session_state.ace_choice = None
                    else:
                        st.session_state.phase = "result"
                st.rerun()
            
            # STAND button
            if c2.button("STAND ✋", use_container_width=True):
                if st.session_state.split_active and st.session_state.current_hand == 0:
                    st.session_state.current_hand = 1
                    st.session_state.ace_choice_locked = False  # Reset for next hand
                    st.session_state.ace_choice = None
                else:
                    d_arr = (ctypes.c_int * 10)(*st.session_state.dealer_hand)
                    new_count = game_lib.dealer_logic(d_arr, len(st.session_state.dealer_hand))
                    st.session_state.dealer_hand = list(d_arr)[:new_count]
                    st.session_state.phase = "result"
                st.rerun()
            
            # SPLIT button (only on first two cards with same rank)
            can_split_flag = False
            if len(current_hand) == 2:
                can_split_flag = game_lib.can_split(current_hand[0], current_hand[1]) and not st.session_state.split_active
            
            if can_split_flag:
                if c3.button("SPLIT 💔", use_container_width=True):
                    if st.session_state.balance >= st.session_state.bet:
                        st.session_state.balance -= st.session_state.bet
                        # Create second hand with the second card
                        card1 = current_hand[0]
                        card2 = current_hand[1]
                        hand1 = [card1, game_lib.draw_card()]
                        hand2 = [card2, game_lib.draw_card()]
                        st.session_state.hands = [hand1, hand2]
                        st.session_state.split_active = True
                        st.session_state.current_hand = 0
                        st.session_state.ace_choice_locked = False  # Reset for first split hand
                        st.session_state.ace_choice = None
                        st.rerun()
                    else:
                        st.error("❌ Insufficient funds to split!")
            else:
                if c3.button("SPLIT 💔", use_container_width=True, disabled=True):
                    pass
            
            # DOUBLE DOWN button (only on first two cards)
            if len(current_hand) == 2 and c4.button("DOUBLE DOWN 💰", use_container_width=True):
                if st.session_state.balance >= st.session_state.bet:
                    st.session_state.balance -= st.session_state.bet
                    st.session_state.bet *= 2
                    current_hand.append(game_lib.draw_card())
                    
                    if game_lib.has_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand)):
                        if st.session_state.ace_choice_locked:
                            p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), st.session_state.ace_choice)
                        else:
                            p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand), 11)
                    else:
                        p_score = game_lib.calculate_score((ctypes.c_int * len(current_hand))(*current_hand), len(current_hand))
                    
                    if p_score > 21:
                        if st.session_state.split_active and st.session_state.current_hand == 0:
                            st.session_state.current_hand = 1
                            st.session_state.ace_choice_locked = False  # Reset for next hand
                            st.session_state.ace_choice = None
                        else:
                            st.session_state.phase = "result"
                    else:
                        if st.session_state.split_active and st.session_state.current_hand == 0:
                            st.session_state.current_hand = 1
                            st.session_state.ace_choice_locked = False  # Reset for next hand
                            st.session_state.ace_choice = None
                        else:
                            d_arr = (ctypes.c_int * 10)(*st.session_state.dealer_hand)
                            new_count = game_lib.dealer_logic(d_arr, len(st.session_state.dealer_hand))
                            st.session_state.dealer_hand = list(d_arr)[:new_count]
                            st.session_state.phase = "result"
                    st.rerun()

        elif st.session_state.phase == "result":
            d_score = game_lib.calculate_score((ctypes.c_int * len(st.session_state.dealer_hand))(*st.session_state.dealer_hand), len(st.session_state.dealer_hand))
            
            if not st.session_state.payout_done:
                old_balance = st.session_state.balance
                
                # Process each hand for split cases
                total_winnings = 0
                for hand_idx, hand in enumerate(st.session_state.hands):
                    # Calculate score with ace choice if available
                    if game_lib.has_ace((ctypes.c_int * len(hand))(*hand), len(hand)):
                        if st.session_state.ace_choice_locked:
                            p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(hand))(*hand), len(hand), st.session_state.ace_choice)
                        else:
                            # Use 11 as default for hands checked without explicit choice
                            p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(hand))(*hand), len(hand), 11)
                    else:
                        p_score = game_lib.calculate_score((ctypes.c_int * len(hand))(*hand), len(hand))
                    
                    # Determine outcome for this hand
                    if p_score > 21:
                        # Player busted - lose the bet (no winnings)
                        pass
                    elif d_score > 21:
                        # Dealer busted - player wins
                        if len(hand) == 2 and p_score == 21:
                            # Blackjack pays 3:2 (1.5x profit) = total return is 2.5x bet
                            total_winnings += int(st.session_state.bet * 2.5)
                        else:
                            # Normal win pays 1:1 (1x profit) = total return is 2x bet
                            total_winnings += int(st.session_state.bet * 2)
                    elif p_score > d_score:
                        # Player closer to 21
                        if len(hand) == 2 and p_score == 21:
                            # Blackjack pays 3:2 (1.5x profit) = total return is 2.5x bet
                            total_winnings += int(st.session_state.bet * 2.5)
                        else:
                            # Normal win pays 1:1 (1x profit) = total return is 2x bet
                            total_winnings += int(st.session_state.bet * 2)
                    elif p_score == d_score:
                        # Push - return the original bet (1x bet)
                        total_winnings += st.session_state.bet
                    # else: p_score < d_score - player loses, no winnings
                
                st.session_state.balance += total_winnings
                
                if total_winnings > st.session_state.bet * len(st.session_state.hands):
                    st.balloons()
                
                from app import sync_balance_to_db
                sync_balance_to_db()
                st.session_state.payout_done = True

            # Display results
            if st.session_state.split_active:
                cols = st.columns(2)
                for hand_idx, hand in enumerate(st.session_state.hands):
                    with cols[hand_idx]:
                        if game_lib.has_ace((ctypes.c_int * len(hand))(*hand), len(hand)):
                            if st.session_state.ace_choice_locked:
                                p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(hand))(*hand), len(hand), st.session_state.ace_choice)
                            else:
                                p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(hand))(*hand), len(hand), 11)
                        else:
                            p_score = game_lib.calculate_score((ctypes.c_int * len(hand))(*hand), len(hand))
                        
                        if p_score > 21:
                            st.error(f"❌ BUST! Hand {hand_idx + 1}")
                        elif d_score > 21:
                            st.success(f"🎉 DEALER BUSTS! Hand {hand_idx + 1} WINS!")
                        elif p_score > d_score:
                            st.success(f"🏆 HAND {hand_idx + 1} WINS!")
                        elif p_score < d_score:
                            st.error(f"💸 HAND {hand_idx + 1} LOSES")
                        else:
                            st.warning(f"🤝 HAND {hand_idx + 1}: PUSH")
            else:
                if game_lib.has_ace((ctypes.c_int * len(st.session_state.player_hand))(*st.session_state.player_hand), len(st.session_state.player_hand)):
                    if st.session_state.ace_choice_locked:
                        p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(st.session_state.player_hand))(*st.session_state.player_hand), len(st.session_state.player_hand), st.session_state.ace_choice)
                    else:
                        p_score = game_lib.calculate_score_with_ace((ctypes.c_int * len(st.session_state.player_hand))(*st.session_state.player_hand), len(st.session_state.player_hand), 11)
                else:
                    p_score = game_lib.calculate_score((ctypes.c_int * len(st.session_state.player_hand))(*st.session_state.player_hand), len(st.session_state.player_hand))
                
                if p_score > 21:
                    st.error("❌ BUST! HOUSE WINS")
                elif d_score > 21:
                    st.success("🎉 DEALER BUSTS! YOU WIN!")
                elif p_score > d_score:
                    st.success(f"🏆 YOU WIN ${st.session_state.bet}!")
                elif p_score < d_score:
                    st.error(f"💸 DEALER WINS ({d_score})")
                else:
                    st.warning("🤝 PUSH - MONEY RETURNED")

            if st.button("COLLECT & NEXT HAND 🔄", use_container_width=True):
                st.session_state.phase = "betting"
                st.rerun()
