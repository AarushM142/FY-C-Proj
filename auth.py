import streamlit as st
from supabase import create_client

def render_auth_page(supabase):
    # Styling for the Login Box
    st.markdown("""
        <style>
        .auth-container {
            max-width: 400px;
            margin: auto;
            padding: 30px;
            background: rgba(0, 0, 0, 0.6);
            border: 2px solid #FFD700;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
        }
        .stTextInput > div > div > input {
            background-color: #1a1a1a !important;
            color: white !important;
            border: 1px solid #444 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🎰 ARCADE GATEWAY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #aaa;'>Enter the high-stakes C-Engine Arcade</p>", unsafe_allow_html=True)

    # Tabs for Login vs Sign Up
    tab1, tab2 = st.tabs(["EXISTING PLAYER", "NEW ACCOUNT"])

    with tab1:
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Security Code", type="password", key="login_pw")
        
        if st.button("LOG IN TO VAULT", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                print(f"DEBUG: User logged in: {res.user.id}")
                
                # Fetch balance immediately
                try:
                    profile = supabase.table("profiles").select("balance").eq("id", res.user.id).single().execute()
                    if profile.data and 'balance' in profile.data:
                        st.session_state.balance = profile.data['balance']
                        print(f"DEBUG: Fetched balance: {st.session_state.balance}")
                    else:
                        st.session_state.balance = 1000
                        print("DEBUG: No balance found, setting to 1000")
                except Exception as e:
                    print(f"DEBUG: Error fetching profile: {e}")
                    print("DEBUG: Profile doesn't exist yet, using default balance")
                    st.session_state.balance = 1000
                
                st.success("Access Granted. Redirecting...")
                st.rerun()
            except Exception as e:
                print(f"DEBUG: Login error: {e}")
                st.error("Authentication Failed: Invalid credentials.")

    with tab2:
        new_email = st.text_input("Email Address", key="reg_email")
        new_pw = st.text_input("New Security Code", type="password", key="reg_pw")
        confirm_pw = st.text_input("Confirm Code", type="password", key="reg_pw_conf")
        
        if st.button("CREATE PROFILE", use_container_width=True):
            if new_pw != confirm_pw:
                st.error("Codes do not match.")
            elif len(new_pw) < 6:
                st.error("Security Code must be at least 6 characters.")
            else:
                try:
                    res = supabase.auth.sign_up({"email": new_email, "password": new_pw})
                    if res.user:
                        # Create a profile entry with initial balance
                        supabase.table("profiles").insert({
                            "id": res.user.id,
                            "balance": 1000
                        }).execute()
                        st.info("📩 Registration initiated! Check your email to verify your account.")
                    else:
                        st.error("Registration failed. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")