import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar as cal_lib
from database import (
    init_db, add_task, get_all_tasks, get_task, update_task, delete_task,
    add_log, get_logs_for_task, get_recent_activity,
    add_event, get_events, get_events_for_month, update_event_status,
    add_manager_item, get_manager_queue, resolve_manager_item,
    add_contact, get_all_contacts, get_contact, delete_contact,
    add_networking_log, get_all_networking, get_pending_followups, mark_followup_done,
    get_kpis, get_calendar_data
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Internship Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# ── Design system ──────────────────────────────────────────────────────────────
NAVY    = "#1B2A4A"
BLUE    = "#185FA5"
GREEN   = "#2D6A4F"
AMBER   = "#B7791F"
RED     = "#C0392B"
PURPLE  = "#553C9A"
GRAY    = "#4A5568"
BG      = "#F7F8FA"
WHITE   = "#FFFFFF"
BORDER  = "#E2E8F0"

st.markdown(f"""
<style>
  /* ── Reset & base ── */
  .block-container {{ padding: 1.5rem 2rem 2rem; max-width: 1200px; }}
  body {{ background: {BG}; }}
  h1 {{ font-size: 22px !important; font-weight: 600 !important; color: {NAVY} !important; margin-bottom: 0 !important; }}
  h2 {{ font-size: 16px !important; font-weight: 600 !important; color: {NAVY} !important; }}
  h3 {{ font-size: 14px !important; font-weight: 600 !important; color: {NAVY} !important; }}
  p, span, div {{ font-family: 'Inter', -apple-system, sans-serif; }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{ background: {NAVY} !important; border-right: none; }}
  [data-testid="stSidebar"] * {{ color: #CBD5E0 !important; }}
  [data-testid="stSidebar"] .stRadio label {{ color: #CBD5E0 !important; font-size: 14px; padding: 6px 0; }}
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] {{ gap: 10px; }}

  /* ── Metrics ── */
  div[data-testid="metric-container"] {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
  }}
  div[data-testid="metric-container"] label {{
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: {GRAY} !important;
  }}
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 28px !important;
    font-weight: 700 !important;
    color: {NAVY} !important;
  }}

  /* ── Cards ── */
  .card {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 16px 18px;
    margin: 6px 0;
  }}
  .card-section {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
  }}

  /* ── Task cards ── */
  .task-row {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-left: 4px solid {BORDER};
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    transition: border-color .15s;
  }}
  .task-row.overdue  {{ border-left-color: {RED}; }}
  .task-row.soon     {{ border-left-color: {AMBER}; }}
  .task-row.ok       {{ border-left-color: {GREEN}; }}
  .task-row.done     {{ border-left-color: #A0AEC0; opacity: .7; }}
  .task-title  {{ font-size: 14px; font-weight: 600; color: {NAVY}; }}
  .task-sub    {{ font-size: 12px; color: {GRAY}; margin-top: 2px; }}
  .task-next   {{ font-size: 12px; color: #2B6CB0; margin-top: 4px; }}

  /* ── Log entries ── */
  .log-item {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    margin: 5px 0;
    font-size: 13px;
  }}

  /* ── Event cards ── */
  .event-item {{
    background: #F5F3FF;
    border: 1px solid #C4B5FD;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 5px 0;
    font-size: 13px;
  }}

  /* ── Queue cards ── */
  .queue-item {{
    background: #FFFBEB;
    border: 1px solid #FCD34D;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 5px 0;
    font-size: 13px;
  }}

  /* ── Contact cards ── */
  .contact-card {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px 16px;
    margin: 6px 0;
  }}
  .contact-avatar {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 38px; height: 38px;
    border-radius: 50%;
    font-weight: 700;
    font-size: 14px;
    color: {WHITE};
    background: {BLUE};
    margin-right: 10px;
    vertical-align: middle;
  }}

  /* ── Badges ── */
  .badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    letter-spacing: .02em;
    margin: 1px 2px;
  }}
  .b-red    {{ background: #FEE2E2; color: #991B1B; }}
  .b-amber  {{ background: #FEF3C7; color: #92400E; }}
  .b-green  {{ background: #D1FAE5; color: #065F46; }}
  .b-blue   {{ background: #DBEAFE; color: #1E40AF; }}
  .b-gray   {{ background: #F1F5F9; color: #475569; }}
  .b-purple {{ background: #EDE9FE; color: #5B21B6; }}
  .b-navy   {{ background: #E8EDF5; color: {NAVY}; }}

  /* ── Section headers ── */
  .section-header {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: {GRAY};
    padding: 12px 0 6px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 10px;
  }}

  /* ── Dividers ── */
  .divider {{ border: none; border-top: 1px solid {BORDER}; margin: 16px 0; }}

  /* ── Progress bar ── */
  .prog-bg {{
    background: #E2E8F0;
    border-radius: 6px;
    height: 8px;
    overflow: hidden;
    margin: 6px 0;
  }}
  .prog-fill {{
    height: 100%;
    background: {BLUE};
    border-radius: 6px;
    transition: width .5s;
  }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background: {BG};
    border-radius: 8px;
    padding: 3px;
  }}
  .stTabs [data-baseweb="tab"] {{
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
  }}
  .stTabs [aria-selected="true"] {{
    background: {WHITE} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
  }}

  /* ── Buttons ── */
  .stButton > button {{
    border-radius: 8px;
    font-weight: 500;
    font-size: 13px;
    padding: 6px 16px;
    border: 1px solid {BORDER};
    transition: all .15s;
  }}
  .stButton > button:hover {{ background: {BG}; border-color: {BLUE}; color: {BLUE}; }}

  /* ── Forms ── */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stSelectbox > div > div {{
    border-radius: 8px !important;
    border: 1px solid {BORDER} !important;
    font-size: 13px !important;
  }}
  .stNumberInput > div > div > input {{ border-radius: 8px !important; }}

  /* ── Mobile ── */
  @media (max-width: 768px) {{
    .block-container {{ padding: .75rem 1rem; }}
    h1 {{ font-size: 18px !important; }}
  }}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
STATUS_OPTS   = ["Not Started","In Progress","Complete","Blocked","On Hold"]
PRIORITY_OPTS = ["High","Medium","Low"]
MEDIUM_OPTS   = ["Call","Meeting","Email","Teams/Slack","In-Person","Written Brief"]
EVENT_TYPES   = ["Manager Call","Buddy Call","Client Call","Team Meeting","Review","Networking","Other"]
REL_OPTS      = ["Manager","Buddy","Team Member","Client","Senior Leader","External Contact","Other"]
NET_TYPES     = ["Introduction","Follow-up","Informational Chat","Project Discussion","Casual Catch-up","Other"]

# ── Badge helpers ──────────────────────────────────────────────────────────────
def sbadge(status):
    m = {"Not Started":"b-gray","In Progress":"b-blue","Complete":"b-green","Blocked":"b-red","On Hold":"b-amber"}
    return f'<span class="badge {m.get(status,"b-gray")}">{status}</span>'

def pbadge(priority):
    m = {"High":"b-red","Medium":"b-amber","Low":"b-green"}
    return f'<span class="badge {m.get(priority,"b-gray")}">{priority}</span>'

def dlbadge(deadline, status):
    if status == "Complete":
        return '<span class="badge b-gray">Done</span>'
    try:
        d = (date.fromisoformat(deadline) - date.today()).days
        if d < 0:   return f'<span class="badge b-red">⚠ Overdue {abs(d)}d</span>'
        elif d <= 3: return f'<span class="badge b-red">Due in {d}d</span>'
        elif d <= 7: return f'<span class="badge b-amber">Due in {d}d</span>'
        else:        return f'<span class="badge b-green">Due in {d}d</span>'
    except:
        return ""

def card_cls(deadline, status):
    if status == "Complete": return "done"
    try:
        d = (date.fromisoformat(deadline) - date.today()).days
        if d < 0:   return "overdue"
        elif d <= 7: return "soon"
        return "ok"
    except:
        return "ok"

def initials(name):
    parts = name.strip().split()
    return ("".join(p[0] for p in parts[:2])).upper() if parts else "?"

def rel_color(rel):
    m = {"Manager":"#C0392B","Buddy":"#1E8449","Team Member":"#185FA5",
         "Client":"#8E44AD","Senior Leader":"#D4800A","External Contact":"#16A085","Other":"#4A5568"}
    return m.get(rel, "#4A5568")

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:8px 0 16px">
        <div style="font-size:18px;font-weight:700;color:#fff">📋 Internship</div>
        <div style="font-size:11px;color:#8899BB;margin-top:2px">Summer 2025 · Finserv</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Dashboard",
        "✅  Tasks",
        "📅  Calendar",
    ], label_visibility="hidden")

    kpis = get_kpis()
    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:11px;color:#8899BB;line-height:2">
        {"🔴 " if kpis['overdue'] > 0 else "✅ "} {kpis['overdue']} overdue<br>
        {"🟡 " if kpis['pending_questions'] > 0 else "✅ "} {kpis['pending_questions']} pending questions<br>
        {"🟣 " if kpis['pending_followups'] > 0 else "✅ "} {kpis['pending_followups']} follow-ups due<br>
        {"🔵 " if kpis['today_events'] > 0 else ""} {kpis['today_events']} events today
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:#8899BB;margin-top:12px'>{date.today().strftime('%a, %d %b %Y')}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Dashboard":
    st.markdown(f"""
    <div style="margin-bottom:4px">
        <span style="font-size:22px;font-weight:700;color:{NAVY}">Welcome back, Gaurav 👋</span>
    </div>
    <div style="font-size:13px;color:{GRAY};margin-bottom:16px">
        {date.today().strftime('%A, %d %B %Y')} · Accenture · Financial Services Consulting
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    # KPI row
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total Tasks",   kpis["total"])
    k2.metric("Completed",     kpis["completed"])
    k3.metric("In Progress",   kpis["in_progress"])
    k4.metric("Blocked",       kpis["blocked"])
    k5.metric("Overdue",       kpis["overdue"])
    k6.metric("Hours Logged",  f"{kpis['hours']}h")

    # Progress bar
    pct = kpis["progress"]
    st.markdown(f"""
    <div style="margin:14px 0 4px;display:flex;align-items:center;gap:12px">
        <div style="flex:1">
            <div class="prog-bg"><div class="prog-fill" style="width:{pct}%"></div></div>
        </div>
        <div style="font-size:13px;font-weight:600;color:{BLUE};min-width:40px">{pct}%</div>
    </div>
    <div style="font-size:11px;color:{GRAY};margin-bottom:16px">
        {kpis['completed']} of {kpis['total']} tasks complete
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.3, 1], gap="large")

    # ── To-do list ──
    with left:
        st.markdown('<div class="section-header">Today\'s To-Do</div>', unsafe_allow_html=True)
        tasks_df = get_all_tasks()
        active = tasks_df[tasks_df["status"] != "Complete"].copy() if not tasks_df.empty else pd.DataFrame()

        if active.empty:
            st.markdown('<div class="card" style="text-align:center;color:#4A5568;padding:24px">🎉 All tasks complete!</div>', unsafe_allow_html=True)
        else:
            active["_d"] = active["deadline"].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else 999)
            active = active.sort_values("_d")
            for _, r in active.iterrows():
                cc = card_cls(r["deadline"], r["status"])
                ns = r["next_step"] or "<em style='color:#aaa'>No log entry yet</em>"
                st.markdown(f"""
                <div class="task-row {cc}">
                    <div class="task-title">{r['task_id']} · {r['task_name']}</div>
                    <div class="task-sub">{dlbadge(r['deadline'],r['status'])} {sbadge(r['status'])} {pbadge(r['priority'])}</div>
                    <div class="task-next">→ {ns}</div>
                    <div style="font-size:11px;color:#94A3B8;margin-top:3px">{r['project'] or ''}</div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        # Today's schedule
        today_ev = get_events(status="upcoming", event_date=date.today().isoformat())
        if not today_ev.empty:
            st.markdown('<div class="section-header">Today\'s Schedule</div>', unsafe_allow_html=True)
            for _, ev in today_ev.iterrows():
                st.markdown(f"""
                <div class="event-item">
                    <div style="font-weight:600;font-size:13px">{ev['time']} · {ev['title']}</div>
                    <div style="font-size:11px;color:#5B21B6;margin-top:2px">
                        {ev['type']} · {ev['duration_mins']}min · with {ev['with_whom']}
                    </div>
                    {"<div style='font-size:11px;color:#555;margin-top:2px'>"+ev['agenda']+"</div>" if ev['agenda'] else ""}
                </div>
                """, unsafe_allow_html=True)

        # Upcoming events
        upcoming = get_events(status="upcoming")
        future = upcoming[upcoming["date"] > date.today().isoformat()].head(3) if not upcoming.empty else pd.DataFrame()
        if not future.empty:
            st.markdown('<div class="section-header">Upcoming</div>', unsafe_allow_html=True)
            for _, ev in future.iterrows():
                st.markdown(f"""
                <div class="event-item">
                    <div style="font-size:12px;font-weight:600">{ev['date']} {ev['time']} · {ev['title']}</div>
                    <div style="font-size:11px;color:#5B21B6">{ev['type']} with {ev['with_whom']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Manager queue
        mq = get_manager_queue(status="pending")
        if not mq.empty:
            st.markdown('<div class="section-header">Manager Queue</div>', unsafe_allow_html=True)
            for _, q in mq.head(4).iterrows():
                tid = f"[{q['task_id']}]" if q.get("task_id") else "[General]"
                st.markdown(f"""
                <div class="queue-item">
                    {pbadge(q['priority'])} <span style="font-size:10px;color:#888">{tid}</span><br>
                    <span style="font-size:12px">{q['question']}</span>
                </div>
                """, unsafe_allow_html=True)

        # Follow-up reminders
        followups = get_pending_followups()
        due_fu = followups[followups["follow_up_date"] <= date.today().isoformat()] if not followups.empty else pd.DataFrame()
        if not due_fu.empty:
            st.markdown('<div class="section-header">Follow-ups Due</div>', unsafe_allow_html=True)
            for _, f in due_fu.head(3).iterrows():
                st.markdown(f"""
                <div class="queue-item">
                    <span style="font-size:10px;color:#888">Follow up with</span>
                    <strong style="font-size:12px"> {f['contact_name']}</strong>
                    <span style="font-size:10px;color:#888"> · {f['follow_up_date']}</span><br>
                    <span style="font-size:11px;color:#555">{f['notes'][:60] if f['notes'] else ''}</span>
                </div>
                """, unsafe_allow_html=True)

    # Recent activity
    st.markdown('<div class="section-header" style="margin-top:16px">Recent Activity</div>', unsafe_allow_html=True)
    recent = get_recent_activity(5)
    if recent.empty:
        st.caption("No activity logged yet.")
    else:
        type_map = {"work":"📝 Work","communication":"💬 Comms","learning":"💡 Learning","manager_question":"❓ Question"}
        for _, r in recent.iterrows():
            label = type_map.get(r["type"], r["type"])
            detail = str(r["work_done"] or r["discussion"] or r["learning_note"] or "")[:90]
            st.markdown(f"""
            <div class="log-item">
                <span style="font-weight:600;color:{NAVY}">{r['date']}</span>
                · <span style="color:{BLUE}">{r['task_id']}</span>
                <span class="badge b-gray">{label}</span><br>
                <span style="color:{GRAY}">{detail}</span>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TASKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✅  Tasks":
    tasks_df = get_all_tasks()

    # Sub-navigation
    sub = st.radio("", ["📋 All Tasks", "👥 Contacts & Networking"], horizontal=True, label_visibility="hidden")

    # ── ALL TASKS ──────────────────────────────────────────────────────────────
    if sub == "📋 All Tasks":
        st.title("Task Tracker")

        # Filters bar — no pre-selections, show all by default
        fc1,fc2,fc3,fc4 = st.columns([2,1,1,1])
        with fc1:
            search = st.text_input("", placeholder="🔍  Search by task name or project...", label_visibility="collapsed")
        with fc2:
            status_f = st.multiselect("Filter by status", STATUS_OPTS, default=[], placeholder="All statuses")
        with fc3:
            priority_f = st.multiselect("Filter by priority", PRIORITY_OPTS, default=[], placeholder="All priorities")
        with fc4:
            if st.button("➕  Add New Task", use_container_width=True):
                st.session_state["add_task"] = not st.session_state.get("add_task", False)

        # Add task form
        if st.session_state.get("add_task"):
            with st.container():
                st.markdown('<div class="card-section">', unsafe_allow_html=True)
                st.markdown("#### New Task")
                with st.form("new_task_form", clear_on_submit=True):
                    nc1,nc2 = st.columns(2)
                    with nc1:
                        tn  = st.text_input("Task name *")
                        prj = st.text_input("Project / Workstream")
                        asb = st.text_input("Assigned by")
                    with nc2:
                        ddl = st.number_input("Deadline — days from today", 1, 365, 14)
                        pri = st.selectbox("Priority", PRIORITY_OPTS)
                        nts = st.text_input("Notes (optional)")
                    b1,b2 = st.columns(2)
                    with b1:
                        submitted = st.form_submit_button("Create Task", use_container_width=True)
                    with b2:
                        cancelled = st.form_submit_button("Cancel", use_container_width=True)
                    if submitted:
                        if not tn:
                            st.error("Task name is required.")
                        else:
                            tid = add_task(tn, prj, asb, ddl, pri, nts)
                            st.success(f"✅  Task {tid} created — status: Not Started")
                            st.session_state["add_task"] = False
                            st.rerun()
                    if cancelled:
                        st.session_state["add_task"] = False
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Filter tasks — empty selection = show all
        df = tasks_df.copy()
        if status_f:
            df = df[df["status"].isin(status_f)]
        if priority_f:
            df = df[df["priority"].isin(priority_f)]
        if search:
            df = df[df["task_name"].str.contains(search,case=False,na=False)|
                    df["project"].str.contains(search,case=False,na=False)]
        df["_d"] = df["deadline"].apply(lambda x: (date.fromisoformat(x)-date.today()).days if x else 999)
        df = df.sort_values("_d")

        st.caption(f"{len(df)} tasks shown")

        for _, r in df.iterrows():
            cc = card_cls(r["deadline"], r["status"])
            exp_label = f"{r['task_id']}  ·  {r['task_name']}  ·  {r['status']}  ·  {r['deadline']}"
            with st.expander(exp_label):

                # Header row
                hc1,hc2,hc3,hc4 = st.columns(4)
                hc1.markdown(f"**Project:** {r['project'] or '—'}")
                hc2.markdown(f"**Assigned by:** {r['assigned_by'] or '—'}")
                hc3.markdown(f"**Priority:** {r['priority']}")
                hc4.markdown(f"**Hours:** {r['total_hours']}h")
                hc1.markdown(f"**Assigned:** {r['assigned_date'] or '—'}")
                hc2.markdown(f"**Deadline:** {r['deadline']}")
                hc3.markdown(f"**Status:** {r['status']}")
                hc4.markdown(f"**Last updated:** {r['last_updated'] or '—'}")

                if r["next_step"]:
                    st.info(f"**Next step:** {r['next_step']}")
                if r["notes"]:
                    st.caption(f"Notes: {r['notes']}")

                st.markdown("---")

                # Tabs
                t1,t2,t3,t4,t5 = st.tabs(["📝  Log Work","💬  Communication","📅  Schedule","❓  Manager Queue","🗂  History"])

                # ── LOG WORK ──
                with t1:
                    with st.form(f"lw_{r['task_id']}", clear_on_submit=True):
                        work = st.text_area("What did you work on? *",
                            placeholder="Verb-first: 'Built segment pivot for NPA analysis'", height=80)
                        lc1,lc2,lc3 = st.columns(3)
                        with lc1:
                            hrs = st.number_input("Hours spent", 0.0, 24.0, 1.0, 0.5)
                        with lc2:
                            new_st = st.selectbox("Update status", ["No change"]+STATUS_OPTS)
                        with lc3:
                            ext_ddl = st.checkbox("Extend deadline?")
                        if ext_ddl:
                            new_ddl_days = st.number_input("New deadline — days from today", 1, 365, 7)
                            new_ddl_val  = (date.today()+timedelta(days=int(new_ddl_days))).isoformat()
                            st.caption(f"New deadline: **{new_ddl_val}**")
                        else:
                            new_ddl_val = ""
                        ns  = st.text_input("Next step *", placeholder="Most important next action — shows on Dashboard")
                        blk = st.text_input("Blockers / issues (optional)")
                        if st.form_submit_button("💾  Save Work Log", use_container_width=True):
                            if not work or not ns:
                                st.error("Work done and Next step are required.")
                            else:
                                add_log(r['task_id'],"work",work_done=work,time_spent=hrs,
                                        blockers=blk,next_step=ns,
                                        status_update="" if new_st=="No change" else new_st,
                                        deadline_update=new_ddl_val)
                                st.success("Logged! Dashboard updated.")
                                st.rerun()

                # ── COMMUNICATION ──
                with t2:
                    mode = st.radio("",["Log past communication","Schedule future call"],
                        horizontal=True, key=f"cmode_{r['task_id']}")

                    if mode == "Log past communication":
                        with st.form(f"comm_{r['task_id']}", clear_on_submit=True):
                            cc1,cc2 = st.columns(2)
                            with cc1:
                                stk = st.text_input("Person *", placeholder="Who did you speak with?")
                                med = st.selectbox("Medium", MEDIUM_OPTS)
                            with cc2:
                                disc = st.text_area("What was discussed? *", height=80)
                                act  = st.text_input("Action item / decision")
                            if st.form_submit_button("💾  Log Communication", use_container_width=True):
                                if not stk or not disc:
                                    st.error("Person and discussion are required.")
                                else:
                                    add_log(r['task_id'],"communication",stakeholder=stk,medium=med,
                                            discussion=disc,action_item=act)
                                    st.success("Communication logged.")
                                    st.rerun()
                    else:
                        with st.form(f"sched_{r['task_id']}", clear_on_submit=True):
                            sc1,sc2 = st.columns(2)
                            with sc1:
                                ev_title = st.text_input("Meeting title *")
                                ev_type  = st.selectbox("Type", EVENT_TYPES)
                                ev_with  = st.text_input("With whom *")
                            with sc2:
                                ev_date  = st.date_input("Date *", value=date.today()+timedelta(1))
                                ev_time  = st.time_input("Time *")
                                ev_dur   = st.number_input("Duration (mins)", 15, 180, 30, 15)
                            ev_agenda = st.text_area("Agenda", height=60, placeholder="What do you want to cover?")
                            if st.form_submit_button("📅  Schedule", use_container_width=True):
                                if not ev_title or not ev_with:
                                    st.error("Title and person required.")
                                else:
                                    add_event(r['task_id'],ev_date.isoformat(),
                                              ev_time.strftime("%H:%M"),ev_dur,
                                              ev_type,ev_title,ev_agenda,ev_with)
                                    st.success("Scheduled! Appears on calendar and dashboard.")
                                    st.rerun()

                # ── SCHEDULE VIEW ──
                with t3:
                    st.markdown("**Scheduled events for this task**")
                    evs = get_events_for_month(date.today().year, date.today().month)
                    if not evs.empty:
                        task_evs = evs[evs["task_id"]==r["task_id"]]
                        if task_evs.empty:
                            st.caption("No events scheduled.")
                        else:
                            for _, ev in task_evs.iterrows():
                                ec1,ec2 = st.columns([4,1])
                                with ec1:
                                    st.markdown(f"""<div class="event-item">
                                        <strong>{ev['date']} {ev['time']}</strong> · {ev['title']}
                                        <span class="badge b-purple">{ev['status']}</span><br>
                                        <span style="font-size:11px">{ev['type']} · {ev['duration_mins']}min · {ev['with_whom']}</span>
                                        {"<br><span style='font-size:11px;color:#555'>"+ev['agenda']+"</span>" if ev['agenda'] else ""}
                                    </div>""", unsafe_allow_html=True)
                                with ec2:
                                    if ev["status"]=="upcoming":
                                        if st.button("Done",key=f"evd_{ev['event_id']}"):
                                            update_event_status(ev["event_id"],"done")
                                            st.rerun()
                    else:
                        st.caption("No events this month.")

                # ── MANAGER QUEUE ──
                with t4:
                    with st.form(f"mq_{r['task_id']}", clear_on_submit=True):
                        q_text = st.text_area("What do you need to ask or clarify? *", height=70)
                        q_pri  = st.selectbox("Priority", PRIORITY_OPTS, key=f"qp_{r['task_id']}")
                        if st.form_submit_button("➕  Add to Manager Queue", use_container_width=True):
                            if not q_text:
                                st.error("Question is required.")
                            else:
                                add_manager_item(r['task_id'], q_text, q_pri)
                                st.success("Added — visible on Dashboard.")
                                st.rerun()

                    st.markdown("**Pending questions for this task**")
                    tmq = get_manager_queue(status="pending")
                    if not tmq.empty:
                        tmq_f = tmq[tmq["task_id"]==r["task_id"]]
                        for _, q in tmq_f.iterrows():
                            qc1,qc2 = st.columns([3,2])
                            with qc1:
                                st.markdown(f"""<div class="queue-item">
                                    {pbadge(q['priority'])}
                                    <span style="font-size:12px;margin-left:4px">{q['question']}</span>
                                </div>""", unsafe_allow_html=True)
                            with qc2:
                                ans = st.text_input("Answer",key=f"ans_{q['item_id']}",label_visibility="collapsed",placeholder="Type answer…")
                                if st.button("✓ Resolve",key=f"res_{q['item_id']}"):
                                    resolve_manager_item(q['item_id'],ans)
                                    st.rerun()

                # ── HISTORY ──
                with t5:
                    logs = get_logs_for_task(r['task_id'])
                    if logs.empty:
                        st.info("No activity logged yet.")
                    else:
                        type_icons = {"work":"📝","communication":"💬","learning":"💡","manager_question":"❓"}
                        for _, lg in logs.iterrows():
                            parts=[]
                            if lg["work_done"]:      parts.append(f"<b>Work:</b> {lg['work_done']}")
                            if lg["next_step"]:      parts.append(f"<b>Next:</b> {lg['next_step']}")
                            if lg["blockers"]:       parts.append(f"<b>Blockers:</b> {lg['blockers']}")
                            if lg["discussion"]:     parts.append(f"<b>Discussion:</b> {lg['discussion']}")
                            if lg["action_item"]:    parts.append(f"<b>Action:</b> {lg['action_item']}")
                            if lg["stakeholder"]:    parts.append(f"<b>With:</b> {lg['stakeholder']} via {lg['medium']}")
                            if lg["learning_note"]:  parts.append(f"<b>Learning:</b> {lg['learning_note']}")
                            if lg["status_update"]:  parts.append(f"<b>Status →</b> {lg['status_update']}")
                            if lg["deadline_update"]:parts.append(f"<b>Deadline →</b> {lg['deadline_update']}")
                            if lg["time_spent"] and float(lg["time_spent"])>0:
                                parts.append(f"<b>Time:</b> {lg['time_spent']}h")
                            icon = type_icons.get(lg["type"],"•")
                            st.markdown(f"""<div class="log-item">
                                {icon} <b>{lg['date']}</b>
                                <span class="badge b-gray">{lg['type']}</span><br>
                                <span style="font-size:12px">{"&nbsp; · &nbsp;".join(parts)}</span>
                            </div>""", unsafe_allow_html=True)

                st.markdown("---")
                if st.button("🗑  Delete task", key=f"del_{r['task_id']}"):
                    delete_task(r['task_id'])
                    st.warning("Task deleted.")
                    st.rerun()

    # ── CONTACTS & NETWORKING ──────────────────────────────────────────────────
    else:
        st.title("Contacts & Networking")
        contacts_df = get_all_contacts()

        cn_tab1, cn_tab2, cn_tab3 = st.tabs(["👥  Contacts","🤝  Log Networking","📋  Networking History"])

        # Contacts directory
        with cn_tab1:
            ca1,ca2 = st.columns([3,1])
            with ca2:
                if st.button("➕  Add Contact", use_container_width=True):
                    st.session_state["add_contact"] = not st.session_state.get("add_contact",False)

            if st.session_state.get("add_contact"):
                with st.form("add_contact_form", clear_on_submit=True):
                    st.markdown("#### New Contact")
                    ac1,ac2 = st.columns(2)
                    with ac1:
                        c_name = st.text_input("Name *")
                        c_role = st.text_input("Role / Designation")
                        c_rel  = st.selectbox("Relationship", REL_OPTS)
                        c_comp = st.text_input("Company / Firm")
                    with ac2:
                        c_email = st.text_input("Email")
                        c_phone = st.text_input("Phone")
                        c_li    = st.text_input("LinkedIn URL")
                        c_notes = st.text_input("Notes")
                    ab1,ab2 = st.columns(2)
                    with ab1:
                        if st.form_submit_button("Save Contact", use_container_width=True):
                            if not c_name:
                                st.error("Name is required.")
                            else:
                                add_contact(c_name,c_role,c_rel,c_comp,c_email,c_phone,c_li,c_notes)
                                st.success(f"Contact '{c_name}' added.")
                                st.session_state["add_contact"] = False
                                st.rerun()
                    with ab2:
                        if st.form_submit_button("Cancel", use_container_width=True):
                            st.session_state["add_contact"] = False
                            st.rerun()

            if contacts_df.empty:
                st.info("No contacts yet. Add your manager, buddy and team members to get started.")
            else:
                # Group by relationship
                for rel in REL_OPTS:
                    grp = contacts_df[contacts_df["relationship"]==rel]
                    if grp.empty:
                        continue
                    st.markdown(f'<div class="section-header">{rel}s</div>', unsafe_allow_html=True)
                    for _, ct in grp.iterrows():
                        col1,col2 = st.columns([4,1])
                        with col1:
                            init = initials(ct["name"])
                            rc   = rel_color(ct["relationship"])
                            st.markdown(f"""<div class="contact-card">
                                <span class="contact-avatar" style="background:{rc}">{init}</span>
                                <strong style="font-size:14px">{ct['name']}</strong>
                                <span class="badge b-navy">{ct['relationship']}</span><br>
                                <span style="font-size:12px;color:{GRAY};margin-left:48px">
                                    {ct['role'] or ''}{' · ' if ct['role'] and ct['company'] else ''}{ct['company'] or ''}
                                </span>
                                {"<br><span style='font-size:11px;color:#94A3B8;margin-left:48px'>"+ct['email']+"</span>" if ct['email'] else ""}
                                {"&nbsp;<span style='font-size:11px;color:#94A3B8'>"+ct['phone']+"</span>" if ct['phone'] else ""}
                                {"<br><span style='font-size:11px;color:#94A3B8;margin-left:48px'>"+ct['notes']+"</span>" if ct['notes'] else ""}
                            </div>""", unsafe_allow_html=True)
                        with col2:
                            if ct["linkedin"]:
                                st.link_button("LinkedIn", ct["linkedin"])
                            if st.button("Delete", key=f"delc_{ct['contact_id']}"):
                                delete_contact(ct['contact_id'])
                                st.rerun()

        # Log networking
        with cn_tab2:
            with st.form("net_log_form", clear_on_submit=True):
                st.markdown("#### Log networking interaction")
                nl1,nl2 = st.columns(2)
                with nl1:
                    # Pick contact or type manually
                    contact_opts = {"— Type manually —": None}
                    if not contacts_df.empty:
                        contact_opts.update({f"{r['name']} ({r['relationship']})": r['contact_id']
                                            for _,r in contacts_df.iterrows()})
                    selected_ct  = st.selectbox("Contact *", list(contact_opts.keys()))
                    contact_id   = contact_opts[selected_ct]

                    if contact_id is None:
                        manual_name = st.text_input("Name (type manually)", placeholder="Person's name")
                        contact_name_final = manual_name
                    else:
                        ct_row = get_contact(contact_id)
                        contact_name_final = ct_row["name"] if ct_row is not None else selected_ct
                        st.caption(f"Role: {contacts_df[contacts_df['contact_id']==contact_id]['role'].values[0] if not contacts_df.empty else ''}")

                    net_type = st.selectbox("Interaction type", NET_TYPES)
                    medium   = st.selectbox("Medium", MEDIUM_OPTS)

                with nl2:
                    notes    = st.text_area("What happened / what was discussed? *", height=100)
                    fu_need  = st.checkbox("Set follow-up reminder?")
                    if fu_need:
                        fu_date = st.date_input("Follow-up by", value=date.today()+timedelta(7))
                    else:
                        fu_date = None

                if st.form_submit_button("💾  Log Interaction", use_container_width=True):
                    name_to_save = contact_name_final if contact_id is None else contacts_df[contacts_df["contact_id"]==contact_id]["name"].values[0] if not contacts_df.empty else ""
                    if not name_to_save or not notes:
                        st.error("Contact name and notes are required.")
                    else:
                        add_networking_log(contact_id, name_to_save, net_type, medium, notes,
                                          fu_need, fu_date.isoformat() if fu_date else None)
                        st.success("Interaction logged!")
                        st.rerun()

        # Networking history
        with cn_tab3:
            net_df = get_all_networking()
            if net_df.empty:
                st.info("No networking interactions logged yet.")
            else:
                fu_filter = st.checkbox("Show only pending follow-ups")
                if fu_filter:
                    net_df = net_df[(net_df["follow_up_needed"]==1) & (net_df["follow_up_done"]==0)]

                st.caption(f"{len(net_df)} interactions")
                for _, n in net_df.iterrows():
                    fu_badge = ""
                    if n["follow_up_needed"] and not n["follow_up_done"]:
                        fu_badge = f'<span class="badge b-amber">Follow-up: {n["follow_up_date"]}</span>'
                    elif n["follow_up_needed"] and n["follow_up_done"]:
                        fu_badge = '<span class="badge b-green">Follow-up done</span>'

                    nc1,nc2 = st.columns([4,1])
                    with nc1:
                        st.markdown(f"""<div class="log-item">
                            <b>{n['date']}</b> · <b style="color:{NAVY}">{n['contact_name']}</b>
                            <span class="badge b-gray">{n['interaction_type']}</span>
                            <span class="badge b-blue">{n['medium']}</span>
                            {fu_badge}<br>
                            <span style="font-size:12px;color:{GRAY}">{n['notes']}</span>
                        </div>""", unsafe_allow_html=True)
                    with nc2:
                        if n["follow_up_needed"] and not n["follow_up_done"]:
                            if st.button("✓ Done", key=f"fu_{n['net_id']}"):
                                mark_followup_done(n['net_id'])
                                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅  Calendar":
    today = date.today()

    # ── Top bar: month nav + schedule button ───────────────────────────────────
    nav1, nav2, nav3, nav4 = st.columns([1, 1, 3, 1.4])
    with nav1:
        month = st.selectbox("", list(range(1,13)), index=today.month-1,
                             format_func=lambda x: cal_lib.month_name[x],
                             label_visibility="collapsed")
    with nav2:
        year = st.number_input("", 2024, 2027, today.year,
                               label_visibility="collapsed")
    with nav4:
        if st.button("➕  Schedule event", use_container_width=True):
            st.session_state["show_cal_form"] = not st.session_state.get("show_cal_form", False)

    # ── Schedule form (toggleable) ─────────────────────────────────────────────
    if st.session_state.get("show_cal_form"):
        with st.container():
            st.markdown(f'<div class="card-section">', unsafe_allow_html=True)
            st.markdown("#### Schedule New Event")
            with st.form("cal_sched", clear_on_submit=True):
                cse1, cse2 = st.columns(2)
                with cse1:
                    cse_title = st.text_input("Event title *", placeholder="e.g. Weekly sync with Rahul")
                    cse_type  = st.selectbox("Type", EVENT_TYPES)
                    cse_with  = st.text_input("With whom *", placeholder="Name of person")
                    all_tasks = get_all_tasks()
                    t_opts = {"No specific task": None}
                    t_opts.update({f"{r['task_id']} · {r['task_name']}": r['task_id']
                                   for _, r in all_tasks.iterrows()})
                    linked = st.selectbox("Link to task (optional)", list(t_opts.keys()))
                with cse2:
                    cse_date = st.date_input("Date *", value=today + timedelta(1))
                    cse_time = st.time_input("Time *")
                    cse_dur  = st.number_input("Duration (mins)", 15, 180, 30, 15)
                    cse_ag   = st.text_area("Agenda / notes", height=86,
                                            placeholder="What do you want to cover?")
                b1, b2 = st.columns(2)
                with b1:
                    if st.form_submit_button("📅  Save Event", use_container_width=True):
                        if not cse_title or not cse_with:
                            st.error("Title and person are required.")
                        else:
                            add_event(t_opts[linked], cse_date.isoformat(),
                                      cse_time.strftime("%H:%M"), cse_dur,
                                      cse_type, cse_title, cse_ag, cse_with)
                            st.success("Event scheduled!")
                            st.session_state["show_cal_form"] = False
                            st.rerun()
                with b2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state["show_cal_form"] = False
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    tasks_cal, logs_cal, events_cal, net_cal = get_calendar_data(year, month)

    # ── Month title + legend ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin:12px 0 8px">
        <div style="font-size:18px;font-weight:700;color:{NAVY}">
            {cal_lib.month_name[month]} {year}
        </div>
        <div style="font-size:11px;color:{GRAY};display:flex;gap:12px;align-items:center">
            <span><span style="color:{RED};font-size:9px">⬤</span> Deadline</span>
            <span><span style="color:{BLUE};font-size:9px">⬤</span> Work</span>
            <span><span style="color:{GREEN};font-size:9px">⬤</span> Comms</span>
            <span><span style="color:{PURPLE};font-size:9px">⬤</span> Event</span>
            <span><span style="color:{AMBER};font-size:9px">⬤</span> Follow-up</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Day-of-week headers ────────────────────────────────────────────────────
    day_cols = st.columns(7)
    for i, h in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
        day_cols[i].markdown(
            f"<div style='text-align:center;font-size:11px;font-weight:600;"
            f"color:{GRAY};padding:6px 0;border-bottom:2px solid {BORDER};margin-bottom:4px'>{h}</div>",
            unsafe_allow_html=True)

    # ── Calendar grid ──────────────────────────────────────────────────────────
    selected_day = st.session_state.get("cal_selected_day", today.day
                                         if today.month == month and today.year == year
                                         else 1)

    for week in cal_lib.monthcalendar(year, month):
        wcols = st.columns(7)
        for i, day in enumerate(week):
            with wcols[i]:
                if day == 0:
                    st.markdown("<div style='min-height:88px'></div>", unsafe_allow_html=True)
                    continue

                ds = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
                is_today    = (ds == today.isoformat())
                is_selected = (day == selected_day)

                dt  = tasks_cal[tasks_cal["deadline"]==ds]  if not tasks_cal.empty  else pd.DataFrame()
                dl  = logs_cal[logs_cal["date"]==ds]         if not logs_cal.empty   else pd.DataFrame()
                de  = events_cal[events_cal["date"]==ds]     if not events_cal.empty else pd.DataFrame()
                dw  = dl[dl["type"]=="work"]                 if not dl.empty         else pd.DataFrame()
                dc  = dl[dl["type"]=="communication"]        if not dl.empty         else pd.DataFrame()
                dfu = net_cal[net_cal["follow_up_date"]==ds] if not net_cal.empty    else pd.DataFrame()

                has_content = not (dt.empty and dw.empty and dc.empty and de.empty and dfu.empty)

                # Colors
                if is_today:
                    bg     = BLUE
                    numcol = WHITE
                    border = f"2px solid {BLUE}"
                elif is_selected:
                    bg     = "#EBF5FB"
                    numcol = BLUE
                    border = f"2px solid {BLUE}"
                elif has_content:
                    bg     = WHITE
                    numcol = NAVY
                    border = f"1px solid {BORDER}"
                else:
                    bg     = WHITE
                    numcol = "#94A3B8"
                    border = f"1px solid #F1F5F9"

                # Dot indicators — compact colored squares
                dot_html = ""
                if not dt.empty:  dot_html += f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:{RED};margin:0 1px'></span>"
                if not dw.empty:  dot_html += f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:{BLUE if not is_today else WHITE};margin:0 1px'></span>"
                if not dc.empty:  dot_html += f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:{GREEN};margin:0 1px'></span>"
                if not de.empty:  dot_html += f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:{PURPLE};margin:0 1px'></span>"
                if not dfu.empty: dot_html += f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:{AMBER};margin:0 1px'></span>"

                # Event time preview
                preview = ""
                if not de.empty:
                    first_ev = de.iloc[0]
                    ev_color = WHITE if is_today else PURPLE
                    preview += f"<div style='font-size:9px;color:{ev_color};margin-top:2px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis'>🕐 {first_ev['time']} {first_ev['title'][:10]}</div>"
                if not dt.empty:
                    dl_color = WHITE if is_today else RED
                    preview += f"<div style='font-size:9px;color:{dl_color};overflow:hidden;white-space:nowrap;text-overflow:ellipsis'>📌 {dt.iloc[0]['task_id']}</div>"

                st.markdown(f"""
                <div style='border:{border};border-radius:10px;background:{bg};
                    padding:8px 8px 6px;min-height:88px;margin:2px;cursor:pointer'>
                    <div style='font-size:13px;font-weight:{"700" if is_today or is_selected else "500"};
                        color:{numcol};margin-bottom:4px'>{day}</div>
                    <div style='margin-bottom:4px'>{dot_html}</div>
                    {preview}
                </div>""", unsafe_allow_html=True)

                # Invisible button to select day
                if st.button(f"{day}", key=f"calday_{year}_{month}_{day}",
                             help=f"View {cal_lib.month_name[month]} {day}"):
                    st.session_state["cal_selected_day"] = day
                    st.rerun()

    # ── Day detail panel ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin:20px 0 8px;padding:12px 16px;background:{NAVY};border-radius:10px;
        display:flex;align-items:center;justify-content:space-between">
        <div style="font-size:14px;font-weight:600;color:{WHITE}">
            {cal_lib.month_name[month]} {selected_day}, {year}
        </div>
        <div style="font-size:11px;color:#8899BB">Click any date above to view details</div>
    </div>
    """, unsafe_allow_html=True)

    sel_str = f"{year}-{str(month).zfill(2)}-{str(selected_day).zfill(2)}"

    d_tasks  = tasks_cal[tasks_cal["deadline"]==sel_str]              if not tasks_cal.empty  else pd.DataFrame()
    d_events = events_cal[events_cal["date"]==sel_str]                if not events_cal.empty else pd.DataFrame()
    d_work   = logs_cal[(logs_cal["date"]==sel_str)&(logs_cal["type"]=="work")] if not logs_cal.empty else pd.DataFrame()
    d_comms  = logs_cal[(logs_cal["date"]==sel_str)&(logs_cal["type"]=="communication")] if not logs_cal.empty else pd.DataFrame()
    d_fu     = net_cal[net_cal["follow_up_date"]==sel_str]            if not net_cal.empty    else pd.DataFrame()

    has_anything = not (d_tasks.empty and d_events.empty and d_work.empty and d_comms.empty and d_fu.empty)

    if not has_anything:
        st.markdown(f"""<div style="text-align:center;padding:24px;color:{GRAY};
            border:1px dashed {BORDER};border-radius:10px;font-size:13px">
            Nothing logged for this date
        </div>""", unsafe_allow_html=True)
    else:
        dd1, dd2, dd3, dd4 = st.columns(4)

        with dd1:
            st.markdown(f'<div style="font-size:11px;font-weight:700;color:{GRAY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">Tasks due</div>', unsafe_allow_html=True)
            if d_tasks.empty:
                st.caption("None")
            else:
                for _, r in d_tasks.iterrows():
                    status_col = GREEN if r['status']=="Complete" else RED if r['status']=="Blocked" else BLUE
                    st.markdown(f"""<div class="log-item" style="border-left:3px solid {status_col}">
                        <div style="font-size:12px;font-weight:600">{r['task_id']}</div>
                        <div style="font-size:11px;color:{GRAY}">{r['task_name'][:30]}</div>
                        <span class="badge b-gray">{r['status']}</span>
                    </div>""", unsafe_allow_html=True)

        with dd2:
            st.markdown(f'<div style="font-size:11px;font-weight:700;color:{GRAY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">Scheduled events</div>', unsafe_allow_html=True)
            if d_events.empty:
                st.caption("None")
            else:
                for _, ev in d_events.iterrows():
                    done_badge = f'<span class="badge b-green">Done</span>' if ev["status"]=="done" else f'<span class="badge b-purple">Upcoming</span>'
                    st.markdown(f"""<div class="event-item">
                        <div style="font-size:13px;font-weight:600">{ev['time']} · {ev['title']}</div>
                        <div style="font-size:11px;color:#5B21B6;margin-top:2px">
                            {ev['type']} · {ev['with_whom']} · {ev['duration_mins']}min
                        </div>
                        {done_badge}
                        {"<div style='font-size:11px;color:#555;margin-top:4px'>"+ev['agenda']+"</div>" if ev['agenda'] else ""}
                    </div>""", unsafe_allow_html=True)
                    if ev["status"] == "upcoming":
                        if st.button("✓ Mark done", key=f"cald_{ev['event_id']}_{selected_day}"):
                            update_event_status(ev["event_id"], "done")
                            st.rerun()

        with dd3:
            st.markdown(f'<div style="font-size:11px;font-weight:700;color:{GRAY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">Work logged</div>', unsafe_allow_html=True)
            if d_work.empty:
                st.caption("None")
            else:
                total_hrs = d_work["time_spent"].sum()
                st.markdown(f"""<div style="font-size:11px;font-weight:600;color:{BLUE};
                    margin-bottom:6px">{total_hrs:.1f}h total</div>""", unsafe_allow_html=True)
                for _, l in d_work.iterrows():
                    st.markdown(f"""<div class="log-item">
                        <div style="font-size:12px;font-weight:600;color:{BLUE}">{l['task_id']} · {l['time_spent']}h</div>
                    </div>""", unsafe_allow_html=True)

        with dd4:
            st.markdown(f'<div style="font-size:11px;font-weight:700;color:{GRAY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">Follow-ups due</div>', unsafe_allow_html=True)
            if d_fu.empty:
                st.caption("None")
            else:
                for _, f in d_fu.iterrows():
                    done = bool(f["follow_up_done"])
                    st.markdown(f"""<div class="queue-item">
                        <div style="font-size:12px;font-weight:600">
                            Follow up with {f['contact_name']}
                        </div>
                        {"<span class='badge b-green'>Done</span>" if done else "<span class='badge b-amber'>Pending</span>"}
                    </div>""", unsafe_allow_html=True)
                    if not done:
                        if st.button("✓ Mark done", key=f"fucd_{f['net_id']}_{selected_day}"):
                            mark_followup_done(f['net_id'])
                            st.rerun()
