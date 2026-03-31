import streamlit as st
from database import (login_user, create_user_by_admin, get_all_users,
                      toggle_user_active, change_password, complete_profile)
from datetime import date, timedelta

NAVY  = "#1B2A4A"
BLUE  = "#185FA5"
GRAY  = "#4A5568"
WHITE = "#FFFFFF"
BORDER= "#E2E8F0"
GREEN = "#2D6A4F"

def hide_ui():
    st.markdown("""<style>
    header[data-testid="stHeader"]{display:none!important}
    #MainMenu{display:none!important}
    footer{display:none!important}
    [data-testid="stToolbar"]{display:none!important}
    [data-testid="stDecoration"]{display:none!important}
    </style>""", unsafe_allow_html=True)

def render_welcome():
    """Brochure shown to first-time visitors before login."""
    hide_ui()
    st.markdown(f"""
    <style>
    .block-container{{max-width:800px;margin:0 auto;padding:2rem 1rem}}
    </style>
    <div style="text-align:center;padding:40px 0 20px">
        <div style="font-size:48px;margin-bottom:12px">📋</div>
        <div style="font-size:28px;font-weight:700;color:{NAVY}">Internship Tracker</div>
        <div style="font-size:15px;color:{GRAY};margin-top:6px">
            Your personal command center for a high-impact internship
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1, "✅", "Track every task", "Log work, update status, extend deadlines — all in one place. Dashboard shows what needs attention today."),
        (c2, "💬", "Never miss a follow-up", "Log every stakeholder conversation. Set follow-up reminders. Build your professional network systematically."),
        (c3, "📅", "See your full picture", "Calendar view shows deadlines, scheduled calls, work logged and communications — all on one screen."),
    ]:
        col.markdown(f"""
        <div style="background:{WHITE};border:1px solid {BORDER};border-radius:12px;
            padding:20px 16px;text-align:center;height:160px">
            <div style="font-size:28px;margin-bottom:8px">{icon}</div>
            <div style="font-size:13px;font-weight:600;color:{NAVY};margin-bottom:6px">{title}</div>
            <div style="font-size:11px;color:{GRAY};line-height:1.5">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Sign In →", use_container_width=True, type="primary"):
            st.session_state["show_login"] = True
            st.rerun()

    st.markdown(f"""
    <div style="text-align:center;margin-top:16px;font-size:11px;color:{GRAY}">
        Access by invitation only · Contact your admin to get an account
    </div>
    """, unsafe_allow_html=True)

def render_login():
    hide_ui()
    st.markdown(f"""
    <style>
    .block-container{{max-width:420px;margin:60px auto;padding:0 1rem}}
    </style>
    <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:32px;margin-bottom:8px">📋</div>
        <div style="font-size:22px;font-weight:700;color:{NAVY}">Internship Tracker</div>
        <div style="font-size:13px;color:{GRAY};margin-top:4px">Sign in to your account</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Sign In", "Change Password"])

    with tab1:
        with st.form("login_form"):
            email    = st.text_input("Email address", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="Your password")
            submit   = st.form_submit_button("Sign In", use_container_width=True)
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    user, error = login_user(email.strip().lower(), password)
                    if user:
                        st.session_state["user"]    = user
                        st.session_state["user_id"] = str(user["user_id"])
                        st.session_state["name"]    = user.get("name") or "New User"
                        st.session_state["role"]    = user["role"]
                        st.session_state["profile_complete"] = user.get("profile_complete", False)
                        st.rerun()
                    else:
                        st.error(error)

        if st.button("← Back to home", use_container_width=True):
            st.session_state["show_login"] = False
            st.rerun()

    with tab2:
        with st.form("change_pw_form"):
            cp_email   = st.text_input("Email address", key="cp_email")
            cp_old     = st.text_input("Current password", type="password", key="cp_old")
            cp_new     = st.text_input("New password (min 8 chars)", type="password", key="cp_new")
            cp_confirm = st.text_input("Confirm new password", type="password", key="cp_confirm")
            if st.form_submit_button("Change Password", use_container_width=True):
                if not all([cp_email, cp_old, cp_new, cp_confirm]):
                    st.error("All fields required.")
                elif len(cp_new) < 8:
                    st.error("Password must be at least 8 characters.")
                elif cp_new != cp_confirm:
                    st.error("New passwords do not match.")
                else:
                    user, error = login_user(cp_email.strip().lower(), cp_old)
                    if user:
                        change_password(str(user["user_id"]), cp_new)
                        st.success("Password changed. Please sign in.")
                    else:
                        st.error("Current email or password is incorrect.")

def render_onboarding():
    """Shown to users who have logged in but not completed their profile."""
    hide_ui()
    uid = st.session_state["user_id"]
    st.markdown(f"""
    <style>
    .block-container{{max-width:520px;margin:40px auto;padding:0 1rem}}
    </style>
    <div style="text-align:center;margin-bottom:28px">
        <div style="font-size:32px;margin-bottom:8px">👋</div>
        <div style="font-size:22px;font-weight:700;color:{NAVY}">Welcome! Let's set up your profile</div>
        <div style="font-size:13px;color:{GRAY};margin-top:6px">
            Takes 60 seconds · You only do this once
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("onboarding_form"):
        st.markdown("#### Your details")
        name  = st.text_input("Full name *", placeholder="Gaurav Patil")
        firm  = st.text_input("Firm / Company *", placeholder="Accenture Strategy")
        phone = st.text_input("Phone number", placeholder="+91 98765 43210")

        st.markdown("#### Internship dates")
        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start date *", value=date.today())
        with col2:
            end   = st.date_input("End date *", value=date.today() + timedelta(days=60))

        st.markdown("#### Set your password")
        pw1 = st.text_input("New password (min 8 chars) *", type="password")
        pw2 = st.text_input("Confirm password *", type="password")

        st.caption("You'll use this password to log in from now on.")

        if st.form_submit_button("Complete Setup →", use_container_width=True):
            if not name or not firm:
                st.error("Name and firm are required.")
            elif len(pw1) < 8:
                st.error("Password must be at least 8 characters.")
            elif pw1 != pw2:
                st.error("Passwords do not match.")
            else:
                complete_profile(uid, name, firm, phone, start, end, pw1)
                st.session_state["name"] = name
                st.session_state["profile_complete"] = True
                st.session_state["user"]["name"] = name
                st.session_state["user"]["firm"] = firm
                st.success("Profile complete! Loading your dashboard...")
                st.rerun()

def is_logged_in():
    return "user_id" in st.session_state and st.session_state["user_id"]

def profile_is_complete():
    return st.session_state.get("profile_complete", False)

def logout():
    for key in ["user","user_id","name","role","profile_complete","show_login"]:
        st.session_state.pop(key, None)
    st.rerun()

def render_admin_users():
    st.markdown("### User Management")
    users_df = get_all_users()

    with st.expander("➕  Add New User"):
        with st.form("add_user_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            with ac1:
                nu_email = st.text_input("Email address *", placeholder="intern@college.edu")
            with ac2:
                nu_role  = st.selectbox("Role", ["intern", "admin"])
            nu_submit = st.form_submit_button("Create Account", use_container_width=True)

            if nu_submit:
                if not nu_email:
                    st.error("Email is required.")
                else:
                    uid, temp_pw, err = create_user_by_admin(nu_email.lower(), nu_role)
                    if uid:
                        st.success(f"Account created!")
                        st.info(f"""Share these login details with the user:

**Email:** {nu_email}
**Temporary password:** `{temp_pw}`

They will be asked to set their own password and fill in their profile on first login.""")
                    else:
                        st.error(err)

    st.markdown(f"**{len(users_df)} registered users**")
    st.caption("Users marked incomplete have not yet set up their profile.")

    for _, u in users_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            status_dot  = "🟢" if u["is_active"] else "🔴"
            profile_tag = "" if u.get("profile_complete") else ' <span style="background:#FEF3C7;color:#92400E;font-size:9px;padding:1px 6px;border-radius:8px;font-weight:600">Profile incomplete</span>'
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid {BORDER}">
                {status_dot} <b>{u['name'] or u['email']}</b>{profile_tag}<br>
                <span style="font-size:11px;color:{GRAY}">
                    {u['email']} · {u['firm'] or '—'} · {u['role']}
                </span><br>
                <span style="font-size:10px;color:#94A3B8">
                    Joined: {u['created_at']} · Last login: {u['last_login'] or 'Never'}
                </span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if u["is_active"]:
                if st.button("Deactivate", key=f"deact_{u['user_id']}"):
                    toggle_user_active(str(u["user_id"]), False)
                    st.rerun()
            else:
                if st.button("Activate", key=f"act_{u['user_id']}"):
                    toggle_user_active(str(u["user_id"]), True)
                    st.rerun()
