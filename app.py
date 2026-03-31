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
    add_networking_log, get_all_networking, get_pending_followups,
    mark_followup_done, get_kpis, get_calendar_data
)
from auth import (render_welcome, render_login, render_onboarding,
                  is_logged_in, profile_is_complete, logout, render_admin_users)
from export_utils import render_export_buttons

st.set_page_config(
    page_title="Internship Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# ── Welcome / Login gate ───────────────────────────────────────────────────────
if not is_logged_in():
    if st.session_state.get("show_login"):
        render_login()
    else:
        render_welcome()
    st.stop()

if not profile_is_complete():
    render_onboarding()
    st.stop()

# ── Session ────────────────────────────────────────────────────────────────────
UID   = st.session_state["user_id"]
UNAME = st.session_state["name"]
ROLE  = st.session_state["role"]
FIRM  = st.session_state["user"].get("firm","") or ""

# ── Design tokens ──────────────────────────────────────────────────────────────
NAVY   = "#1B2A4A"
BLUE   = "#185FA5"
GREEN  = "#2D6A4F"
AMBER  = "#B7791F"
RED    = "#C0392B"
PURPLE = "#553C9A"
GRAY   = "#4A5568"
WHITE  = "#FFFFFF"
BORDER = "#E2E8F0"
BG     = "#F7F8FA"

st.markdown(f"""
<style>
  header[data-testid="stHeader"]{{display:none!important}}
  #MainMenu{{display:none!important}}
  footer{{display:none!important}}
  [data-testid="stToolbar"]{{display:none!important}}
  [data-testid="stDecoration"]{{display:none!important}}
  .block-container{{padding:1.2rem 1.5rem 2rem;max-width:1280px}}
  body{{background:{BG}}}
  h1{{font-size:20px!important;font-weight:700!important;color:{NAVY}!important;margin:0!important}}
  h2{{font-size:15px!important;font-weight:600!important;color:{NAVY}!important}}
  h3{{font-size:13px!important;font-weight:600!important;color:{NAVY}!important}}
  [data-testid="stSidebar"]{{background:{NAVY}!important}}
  [data-testid="stSidebar"] *{{color:#CBD5E0!important}}
  [data-testid="stSidebar"] .stRadio label{{color:#CBD5E0!important;font-size:14px;padding:8px 0}}
  div[data-testid="metric-container"]{{background:{WHITE};border:1px solid {BORDER};
    border-radius:10px;padding:12px 16px}}
  div[data-testid="metric-container"] label{{font-size:10px!important;font-weight:700!important;
    text-transform:uppercase;letter-spacing:.05em;color:{GRAY}!important}}
  div[data-testid="metric-container"] [data-testid="stMetricValue"]{{font-size:26px!important;
    font-weight:700!important;color:{NAVY}!important}}
  .task-row{{background:{WHITE};border:1px solid {BORDER};border-left:4px solid {BORDER};
    border-radius:10px;padding:12px 16px;margin:5px 0}}
  .task-row.overdue{{border-left-color:{RED};background:#FFFAFA}}
  .task-row.soon{{border-left-color:{AMBER};background:#FFFDF5}}
  .task-row.ok{{border-left-color:{GREEN};background:#FAFFFC}}
  .task-row.done{{border-left-color:#A0AEC0;opacity:.65}}
  .task-title{{font-size:14px;font-weight:600;color:{NAVY}}}
  .task-sub{{font-size:12px;color:{GRAY};margin-top:2px}}
  .task-next{{font-size:12px;color:#2B6CB0;margin-top:4px}}
  .log-item{{background:{BG};border:1px solid {BORDER};border-radius:8px;padding:10px 14px;margin:4px 0;font-size:13px}}
  .event-item{{background:#F5F3FF;border:1px solid #C4B5FD;border-radius:8px;padding:10px 14px;margin:4px 0;font-size:13px}}
  .queue-item{{background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:10px 14px;margin:4px 0;font-size:13px}}
  .alert-banner{{background:#FEE2E2;border:1px solid #FCA5A5;border-radius:10px;
    padding:12px 18px;margin:8px 0;display:flex;align-items:center;gap:12px}}
  .section-hdr{{font-size:10px;font-weight:700;color:{GRAY};text-transform:uppercase;
    letter-spacing:.07em;padding:10px 0 6px;border-bottom:1px solid {BORDER};margin-bottom:8px}}
  .prog-bg{{background:#E2E8F0;border-radius:6px;height:8px;overflow:hidden;margin:6px 0}}
  .prog-fill{{height:100%;background:{BLUE};border-radius:6px}}
  .divider{{border:none;border-top:1px solid {BORDER};margin:14px 0}}
  .badge{{display:inline-block;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;margin:1px 2px}}
  .b-red{{background:#FEE2E2;color:#991B1B}}
  .b-amber{{background:#FEF3C7;color:#92400E}}
  .b-green{{background:#D1FAE5;color:#065F46}}
  .b-blue{{background:#DBEAFE;color:#1E40AF}}
  .b-gray{{background:#F1F5F9;color:#475569}}
  .b-purple{{background:#EDE9FE;color:#5B21B6}}
  .b-navy{{background:#E8EDF5;color:{NAVY}}}
  .cal-day{{border-radius:10px;padding:8px;min-height:96px;margin:2px;cursor:pointer;transition:all .15s}}
  .cal-day:hover{{box-shadow:0 2px 8px rgba(0,0,0,.1)}}
  .stTabs [data-baseweb="tab-list"]{{gap:2px;background:{BG};border-radius:8px;padding:3px}}
  .stTabs [data-baseweb="tab"]{{border-radius:6px;padding:6px 14px;font-size:13px;font-weight:500}}
  .stTabs [aria-selected="true"]{{background:{WHITE}!important;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
  .stButton>button{{border-radius:8px;font-weight:500;font-size:13px;border:1px solid {BORDER}}}
  .stButton>button:hover{{border-color:{BLUE};color:{BLUE}}}
  @media(max-width:768px){{
    .block-container{{padding:.75rem .75rem}}
    div[data-testid="metric-container"] [data-testid="stMetricValue"]{{font-size:20px!important}}
    .stTabs [data-baseweb="tab"]{{padding:5px 8px;font-size:12px}}
  }}
</style>
""", unsafe_allow_html=True)

STATUS_OPTS   = ["Not Started","In Progress","Complete","Blocked","On Hold"]
PRIORITY_OPTS = ["High","Medium","Low"]
MEDIUM_OPTS   = ["Call","Meeting","Email","Teams/Slack","In-Person","Written Brief"]
EVENT_TYPES   = ["Manager Call","Buddy Call","Client Call","Team Meeting","Review","Networking","Other"]
REL_OPTS      = ["Manager","Buddy","Team Member","Client","Senior Leader","External Contact","Other"]
NET_TYPES     = ["Introduction","Follow-up","Informational Chat","Project Discussion","Casual Catch-up","Other"]

def sbadge(s):
    m={"Not Started":"b-gray","In Progress":"b-blue","Complete":"b-green","Blocked":"b-red","On Hold":"b-amber"}
    return f'<span class="badge {m.get(s,"b-gray")}">{s}</span>'

def pbadge(p):
    m={"High":"b-red","Medium":"b-amber","Low":"b-green"}
    return f'<span class="badge {m.get(p,"b-gray")}">{p}</span>'

def dlbadge(dl, status):
    if status=="Complete": return '<span class="badge b-gray">Done</span>'
    try:
        d=(date.fromisoformat(str(dl))-date.today()).days
        if d<0:    return f'<span class="badge b-red">⚠ Overdue {abs(d)}d</span>'
        elif d<=2: return f'<span class="badge b-red">Due in {d}d</span>'
        elif d<=7: return f'<span class="badge b-amber">Due in {d}d</span>'
        else:      return f'<span class="badge b-green">Due in {d}d</span>'
    except: return ""

def card_cls(dl, status):
    if status=="Complete": return "done"
    try:
        d=(date.fromisoformat(str(dl))-date.today()).days
        if d<0: return "overdue"
        elif d<=7: return "soon"
        return "ok"
    except: return "ok"

def initials(name):
    parts = name.strip().split()
    return ("".join(p[0] for p in parts[:2])).upper() if parts else "?"

def rel_color(rel):
    m={"Manager":"#C0392B","Buddy":"#1E8449","Team Member":"#185FA5",
       "Client":"#8E44AD","Senior Leader":"#D4800A","External Contact":"#16A085","Other":"#4A5568"}
    return m.get(rel,"#4A5568")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:8px 0 14px">
        <div style="font-size:17px;font-weight:700;color:#fff">📋 Internship</div>
        <div style="font-size:11px;color:#8899BB;margin-top:2px">{UNAME} · {FIRM}</div>
    </div>""", unsafe_allow_html=True)

    pages = ["🏠  Dashboard","✅  Tasks","📅  Calendar"]
    if ROLE == "admin":
        pages.append("⚙️  Admin")
    page = st.radio("Navigation", pages, label_visibility="hidden")

    kpis = get_kpis(UID)
    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:11px;color:#8899BB;line-height:2.2">
        {"🔴" if kpis['overdue']>0 else "✅"} {kpis['overdue']} overdue<br>
        {"🟡" if kpis['pending_questions']>0 else "✅"} {kpis['pending_questions']} pending questions<br>
        {"🟣" if kpis['pending_followups']>0 else "✅"} {kpis['pending_followups']} follow-ups due<br>
        {"🔵" if kpis['today_events']>0 else "  "} {kpis['today_events']} events today
    </div>""", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:#8899BB;margin-top:10px'>{date.today().strftime('%a, %d %b %Y')}</div>",
                unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Sign Out", use_container_width=True):
        logout()

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Dashboard":
    hc1, hc2 = st.columns([4,1])
    with hc1:
        st.markdown(f"""
        <div style="margin-bottom:4px">
            <span style="font-size:22px;font-weight:700;color:{NAVY}">Welcome back, {UNAME} 👋</span>
        </div>
        <div style="font-size:13px;color:{GRAY};margin-bottom:12px">
            {date.today().strftime('%A, %d %B %Y')} · {FIRM}
        </div>""", unsafe_allow_html=True)
    with hc2:
        if st.button("📥 Export", use_container_width=True):
            st.session_state["show_export"] = not st.session_state.get("show_export", False)

    if st.session_state.get("show_export"):
        with st.container():
            render_export_buttons(UID, UNAME)
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if kpis["overdue"] > 0 or kpis["due_soon"] > 0:
        parts = []
        if kpis["overdue"] > 0:
            parts.append(f"{kpis['overdue']} task{'s' if kpis['overdue']>1 else ''} overdue")
        if kpis["due_soon"] > 0:
            parts.append(f"{kpis['due_soon']} due within 48 hours")
        st.markdown(f"""
        <div class="alert-banner">
            <span style="font-size:20px">⚠️</span>
            <div>
                <div style="font-size:13px;font-weight:600;color:#991B1B">
                    Action needed — {" · ".join(parts)}
                </div>
                <div style="font-size:11px;color:#B91C1C;margin-top:2px">
                    Open the task below to update status or extend the deadline
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Total Tasks",  kpis["total"])
    k2.metric("Completed",    kpis["completed"])
    k3.metric("In Progress",  kpis["in_progress"])
    k4.metric("Blocked",      kpis["blocked"])
    k5.metric("Overdue",      kpis["overdue"])
    k6.metric("Hours Logged", f"{kpis['hours']}h")

    pct = kpis["progress"]
    st.markdown(f"""
    <div style="margin:12px 0 4px;display:flex;align-items:center;gap:12px">
        <div style="flex:1"><div class="prog-bg"><div class="prog-fill" style="width:{pct}%"></div></div></div>
        <div style="font-size:13px;font-weight:700;color:{BLUE};min-width:42px">{pct}%</div>
    </div>
    <div style="font-size:11px;color:{GRAY};margin-bottom:14px">
        {kpis['completed']} of {kpis['total']} tasks complete
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.3,1], gap="large")

    with left:
        st.markdown('<div class="section-hdr">Today\'s To-Do</div>', unsafe_allow_html=True)
        tasks_df = get_all_tasks(UID)
        active   = tasks_df[tasks_df["status"] != "Complete"].copy() if not tasks_df.empty else pd.DataFrame()
        if active.empty:
            st.markdown(f'<div style="text-align:center;padding:24px;color:{GRAY};'
                        f'border:1px dashed {BORDER};border-radius:10px">🎉 All tasks complete!</div>',
                        unsafe_allow_html=True)
        else:
            active["_d"] = active["deadline"].apply(
                lambda x: (date.fromisoformat(str(x))-date.today()).days if x else 999)
            active = active.sort_values("_d")
            for _, r in active.iterrows():
                cc = card_cls(r["deadline"], r["status"])
                ns = r["next_step"] or f"<em style='color:#aaa'>No log yet — open task to log work</em>"
                st.markdown(f"""
                <div class="task-row {cc}">
                    <div class="task-title">{r['task_id']} · {r['task_name']}</div>
                    <div class="task-sub">
                        {dlbadge(r['deadline'],r['status'])} {sbadge(r['status'])} {pbadge(r['priority'])}
                    </div>
                    <div class="task-next">→ {ns}</div>
                    <div style="font-size:11px;color:#94A3B8;margin-top:2px">{r['project'] or ''}</div>
                </div>""", unsafe_allow_html=True)

    with right:
        today_ev = get_events(UID, status="upcoming", event_date=date.today())
        if not today_ev.empty:
            st.markdown('<div class="section-hdr">Today\'s Schedule</div>', unsafe_allow_html=True)
            for _, ev in today_ev.iterrows():
                st.markdown(f"""<div class="event-item">
                    <div style="font-weight:600;font-size:13px">{ev['time']} · {ev['title']}</div>
                    <div style="font-size:11px;color:#5B21B6;margin-top:2px">
                        {ev['type']} · {ev['duration_mins']}min · with {ev['with_whom']}
                    </div>
                    {"<div style='font-size:11px;color:#555;margin-top:2px'>"+str(ev['agenda'])+"</div>" if ev['agenda'] else ""}
                </div>""", unsafe_allow_html=True)

        upcoming = get_events(UID, status="upcoming")
        future   = upcoming[upcoming["date"].astype(str) > date.today().isoformat()].head(3) \
                   if not upcoming.empty else pd.DataFrame()
        if not future.empty:
            st.markdown('<div class="section-hdr">Upcoming</div>', unsafe_allow_html=True)
            for _, ev in future.iterrows():
                st.markdown(f"""<div class="event-item">
                    <div style="font-size:12px;font-weight:600">{str(ev['date'])} {ev['time']} · {ev['title']}</div>
                    <div style="font-size:11px;color:#5B21B6">{ev['type']} with {ev['with_whom']}</div>
                </div>""", unsafe_allow_html=True)

        mq = get_manager_queue(UID, status="pending")
        if not mq.empty:
            st.markdown('<div class="section-hdr">Manager Queue</div>', unsafe_allow_html=True)
            for _, q in mq.head(4).iterrows():
                tid = f"[{q['task_id']}]" if q.get("task_id") else "[General]"
                st.markdown(f"""<div class="queue-item">
                    {pbadge(q['priority'])} <span style="font-size:10px;color:#888">{tid}</span><br>
                    <span style="font-size:12px">{q['question']}</span>
                </div>""", unsafe_allow_html=True)

        followups = get_pending_followups(UID)
        if not followups.empty:
            due = followups[followups["follow_up_date"].astype(str) <= date.today().isoformat()]
            if not due.empty:
                st.markdown('<div class="section-hdr">Follow-ups Due</div>', unsafe_allow_html=True)
                for _, f in due.head(3).iterrows():
                    st.markdown(f"""<div class="queue-item">
                        <div style="font-size:12px;font-weight:600">Follow up with {f['contact_name']}</div>
                        <span style="font-size:11px;color:#555">{str(f['notes'])[:60] if f['notes'] else ''}</span>
                    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Recent Activity</div>', unsafe_allow_html=True)
    recent = get_recent_activity(UID, 5)
    if recent.empty:
        st.caption("No activity logged yet.")
    else:
        type_map = {"work":"📝 Work","communication":"💬 Comms",
                    "learning":"💡 Learning","manager_question":"❓ Question"}
        for _, r in recent.iterrows():
            label  = type_map.get(r["type"], r["type"])
            detail = str(r["work_done"] or r["discussion"] or r["learning_note"] or "")[:90]
            st.markdown(f"""<div class="log-item">
                <span style="font-weight:600;color:{NAVY}">{str(r['date'])}</span>
                · <span style="color:{BLUE}">{r['task_id']}</span>
                <span class="badge b-gray">{label}</span><br>
                <span style="color:{GRAY}">{detail}</span>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TASKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✅  Tasks":
    tasks_df = get_all_tasks(UID)
    sub = st.radio("Section", ["📋 All Tasks","👥 Contacts & Networking"],
                   horizontal=True, label_visibility="hidden")

    if sub == "📋 All Tasks":
        st.title("Task Tracker")
        fc1,fc2,fc3,fc4 = st.columns([2,1,1,1])
        with fc1:
            search = st.text_input("Search", placeholder="🔍 Search tasks...", label_visibility="collapsed")
        with fc2:
            status_f = st.multiselect("Status filter", STATUS_OPTS, default=[], placeholder="All statuses")
        with fc3:
            priority_f = st.multiselect("Priority filter", PRIORITY_OPTS, default=[], placeholder="All priorities")
        with fc4:
            if st.button("➕ New Task", use_container_width=True):
                st.session_state["add_task"] = not st.session_state.get("add_task", False)

        if st.session_state.get("add_task"):
            with st.form("new_task_form", clear_on_submit=True):
                st.markdown("#### New Task")
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
                    sub_btn = st.form_submit_button("Create Task", use_container_width=True)
                with b2:
                    can_btn = st.form_submit_button("Cancel", use_container_width=True)
                if sub_btn:
                    if not tn:
                        st.error("Task name required.")
                    else:
                        tid = add_task(UID, tn, prj, asb, ddl, pri, nts)
                        st.success(f"✅ Task {tid} created.")
                        st.session_state["add_task"] = False
                        st.rerun()
                if can_btn:
                    st.session_state["add_task"] = False
                    st.rerun()

        df = tasks_df.copy()
        if status_f:   df = df[df["status"].isin(status_f)]
        if priority_f: df = df[df["priority"].isin(priority_f)]
        if search:
            df = df[df["task_name"].str.contains(search,case=False,na=False)|
                    df["project"].fillna("").str.contains(search,case=False,na=False)]
        df["_d"] = df["deadline"].apply(
            lambda x: (date.fromisoformat(str(x))-date.today()).days if x else 999)
        df = df.sort_values("_d")
        st.caption(f"{len(df)} tasks")

        for _, r in df.iterrows():
            with st.expander(f"{r['task_id']}  ·  {r['task_name']}  ·  {r['status']}  ·  {str(r['deadline'])}"):
                hc1,hc2,hc3,hc4 = st.columns(4)
                hc1.markdown(f"**Project:** {r['project'] or '—'}")
                hc2.markdown(f"**Assigned by:** {r['assigned_by'] or '—'}")
                hc3.markdown(f"**Priority:** {r['priority']}")
                hc4.markdown(f"**Hours:** {r['total_hours']}h")
                hc1.markdown(f"**Assigned:** {str(r['assigned_date']) or '—'}")
                hc2.markdown(f"**Deadline:** {str(r['deadline'])}")
                hc3.markdown(f"**Status:** {r['status']}")
                hc4.markdown(f"**Last updated:** {str(r['last_updated']) or '—'}")
                if r["next_step"]:
                    st.info(f"**Next step:** {r['next_step']}")
                if r["notes"]:
                    st.caption(f"Notes: {r['notes']}")
                st.markdown("---")

                t1,t2,t3,t4,t5 = st.tabs(
                    ["📝 Log Work","💬 Communication","📅 Schedule","❓ Manager Queue","🗂 History"])

                with t1:
                    with st.form(f"lw_{r['task_id']}", clear_on_submit=True):
                        work = st.text_area("What did you work on? *",
                            placeholder="Verb-first: 'Built segment pivot for NPA analysis'",height=80)
                        lc1,lc2,lc3 = st.columns(3)
                        with lc1: hrs = st.number_input("Hours", 0.0, 24.0, 1.0, 0.5)
                        with lc2: new_st = st.selectbox("Update status", ["No change"]+STATUS_OPTS)
                        with lc3: ext_ddl = st.checkbox("Extend deadline?")
                        if ext_ddl:
                            new_ddl_days = st.number_input("New deadline — days from today", 1, 365, 7)
                            new_ddl_val  = date.today() + timedelta(days=int(new_ddl_days))
                            st.caption(f"New deadline: **{new_ddl_val}**")
                        else:
                            new_ddl_val = None
                        ns  = st.text_input("Next step *",
                            placeholder="Most important next action — shows on Dashboard")
                        blk = st.text_input("Blockers (optional)")
                        if st.form_submit_button("💾 Save Work Log", use_container_width=True):
                            if not work or not ns:
                                st.error("Work done and Next step required.")
                            else:
                                add_log(UID, r['task_id'], "work", work_done=work,
                                        time_spent=hrs, blockers=blk, next_step=ns,
                                        status_update="" if new_st=="No change" else new_st,
                                        deadline_update=new_ddl_val)
                                st.success("Logged! Dashboard updated.")
                                st.rerun()

                with t2:
                    mode = st.radio("Entry type", ["Log past communication","Schedule future call"],
                                    horizontal=True, key=f"cmode_{r['task_id']}")
                    if mode == "Log past communication":
                        with st.form(f"comm_{r['task_id']}", clear_on_submit=True):
                            cc1,cc2 = st.columns(2)
                            with cc1:
                                stk = st.text_input("Person *")
                                med = st.selectbox("Medium", MEDIUM_OPTS)
                            with cc2:
                                disc = st.text_area("What was discussed? *", height=80)
                                act  = st.text_input("Action item")
                            if st.form_submit_button("💾 Log Communication", use_container_width=True):
                                if not stk or not disc:
                                    st.error("Person and discussion required.")
                                else:
                                    add_log(UID, r['task_id'], "communication",
                                            stakeholder=stk, medium=med,
                                            discussion=disc, action_item=act)
                                    st.success("Logged.")
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
                            ev_agenda = st.text_area("Agenda", height=60)
                            if st.form_submit_button("📅 Schedule", use_container_width=True):
                                if not ev_title or not ev_with:
                                    st.error("Title and person required.")
                                else:
                                    add_event(UID, r['task_id'], ev_date,
                                              ev_time.strftime("%H:%M"), ev_dur,
                                              ev_type, ev_title, ev_agenda, ev_with)
                                    st.success("Scheduled!")
                                    st.rerun()

                with t3:
                    evs = get_events_for_month(UID, date.today().year, date.today().month)
                    if not evs.empty:
                        task_evs = evs[evs["task_id"]==r["task_id"]]
                        if task_evs.empty:
                            st.caption("No events for this task this month.")
                        else:
                            for _, ev in task_evs.iterrows():
                                ec1,ec2 = st.columns([4,1])
                                with ec1:
                                    st.markdown(f"""<div class="event-item">
                                        <strong>{str(ev['date'])} {ev['time']}</strong> · {ev['title']}
                                        <span class="badge b-purple">{ev['status']}</span><br>
                                        <span style="font-size:11px">{ev['type']} · {ev['duration_mins']}min · {ev['with_whom']}</span>
                                    </div>""", unsafe_allow_html=True)
                                with ec2:
                                    if ev["status"]=="upcoming":
                                        if st.button("Done", key=f"evd_{ev['event_id']}"):
                                            update_event_status(UID, ev["event_id"], "done")
                                            st.rerun()
                    else:
                        st.caption("No events this month.")

                with t4:
                    with st.form(f"mq_{r['task_id']}", clear_on_submit=True):
                        q_text = st.text_area("Question to raise with manager *", height=70)
                        q_pri  = st.selectbox("Priority", PRIORITY_OPTS, key=f"qp_{r['task_id']}")
                        if st.form_submit_button("➕ Add to Manager Queue", use_container_width=True):
                            if not q_text:
                                st.error("Question required.")
                            else:
                                add_manager_item(UID, r['task_id'], q_text, q_pri)
                                st.success("Added — visible on Dashboard.")
                                st.rerun()
                    tmq = get_manager_queue(UID, status="pending")
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
                                ans = st.text_input("Answer", key=f"ans_{q['item_id']}",
                                                    label_visibility="collapsed", placeholder="Answer…")
                                if st.button("✓ Resolve", key=f"res_{q['item_id']}"):
                                    resolve_manager_item(UID, q['item_id'], ans)
                                    st.rerun()

                with t5:
                    logs = get_logs_for_task(UID, r['task_id'])
                    if logs.empty:
                        st.info("No activity logged yet.")
                    else:
                        icons = {"work":"📝","communication":"💬","learning":"💡","manager_question":"❓"}
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
                            if lg["deadline_update"]:parts.append(f"<b>Deadline →</b> {str(lg['deadline_update'])}")
                            if lg["time_spent"] and float(lg["time_spent"])>0:
                                parts.append(f"<b>Time:</b> {lg['time_spent']}h")
                            icon = icons.get(lg["type"],"•")
                            st.markdown(f"""<div class="log-item">
                                {icon} <b>{str(lg['date'])}</b>
                                <span class="badge b-gray">{lg['type']}</span><br>
                                <span style="font-size:12px">{"&nbsp;·&nbsp;".join(parts)}</span>
                            </div>""", unsafe_allow_html=True)

                st.markdown("---")
                if st.button("🗑 Delete task", key=f"del_{r['task_id']}"):
                    delete_task(UID, r['task_id'])
                    st.warning("Task deleted.")
                    st.rerun()

    else:
        st.title("Contacts & Networking")
        contacts_df = get_all_contacts(UID)
        cn1, cn2, cn3 = st.tabs(["👥 Contacts","🤝 Log Interaction","📋 History"])

        with cn1:
            _,ca2 = st.columns([4,1])
            with ca2:
                if st.button("➕ Add Contact", use_container_width=True):
                    st.session_state["add_contact"] = not st.session_state.get("add_contact",False)
            if st.session_state.get("add_contact"):
                with st.form("add_contact_form", clear_on_submit=True):
                    st.markdown("#### New Contact")
                    ac1,ac2 = st.columns(2)
                    with ac1:
                        cn_name = st.text_input("Name *")
                        cn_role = st.text_input("Role / Designation")
                        cn_rel  = st.selectbox("Relationship", REL_OPTS)
                        cn_comp = st.text_input("Company")
                    with ac2:
                        cn_email= st.text_input("Email")
                        cn_phone= st.text_input("Phone")
                        cn_li   = st.text_input("LinkedIn URL")
                        cn_notes= st.text_input("Notes")
                    ab1,ab2 = st.columns(2)
                    with ab1:
                        if st.form_submit_button("Save", use_container_width=True):
                            if not cn_name:
                                st.error("Name required.")
                            else:
                                add_contact(UID,cn_name,cn_role,cn_rel,cn_comp,cn_email,cn_phone,cn_li,cn_notes)
                                st.success(f"'{cn_name}' added.")
                                st.session_state["add_contact"] = False
                                st.rerun()
                    with ab2:
                        if st.form_submit_button("Cancel", use_container_width=True):
                            st.session_state["add_contact"] = False
                            st.rerun()

            if contacts_df.empty:
                st.info("No contacts yet. Add your manager, buddy and team members.")
            else:
                for rel in REL_OPTS:
                    grp = contacts_df[contacts_df["relationship"]==rel]
                    if grp.empty: continue
                    st.markdown(f'<div class="section-hdr">{rel}s</div>', unsafe_allow_html=True)
                    for _, ct in grp.iterrows():
                        col1,col2 = st.columns([5,1])
                        with col1:
                            rc   = rel_color(ct["relationship"])
                            init = initials(ct["name"])
                            st.markdown(f"""<div style="background:{WHITE};border:1px solid {BORDER};
                                border-radius:10px;padding:12px 16px;margin:5px 0">
                                <span style="display:inline-flex;align-items:center;justify-content:center;
                                    width:36px;height:36px;border-radius:50%;background:{rc};
                                    color:#fff;font-weight:700;font-size:13px;margin-right:10px;
                                    vertical-align:middle">{init}</span>
                                <strong style="font-size:14px">{ct['name']}</strong>
                                <span class="badge b-navy">{ct['relationship']}</span><br>
                                <span style="font-size:12px;color:{GRAY};margin-left:46px">
                                    {ct['role'] or ''}{' · ' if ct['role'] and ct['company'] else ''}{ct['company'] or ''}
                                </span>
                                {"<br><span style='font-size:11px;color:#94A3B8;margin-left:46px'>"+ct['email']+"</span>" if ct['email'] else ""}
                            </div>""", unsafe_allow_html=True)
                        with col2:
                            if ct["linkedin"]:
                                st.link_button("LinkedIn", ct["linkedin"])
                            if st.button("Delete", key=f"dc_{ct['contact_id']}"):
                                delete_contact(UID, ct['contact_id'])
                                st.rerun()

        with cn2:
            with st.form("net_log_form", clear_on_submit=True):
                st.markdown("#### Log networking interaction")
                nl1,nl2 = st.columns(2)
                with nl1:
                    ct_opts = {"— Type manually —": None}
                    if not contacts_df.empty:
                        ct_opts.update({f"{r['name']} ({r['relationship']})": r['contact_id']
                                        for _,r in contacts_df.iterrows()})
                    sel_ct = st.selectbox("Contact *", list(ct_opts.keys()))
                    cid    = ct_opts[sel_ct]
                    if cid is None:
                        manual_name = st.text_input("Name", placeholder="Type name")
                        cname_final = manual_name
                    else:
                        ct_row = get_contact(UID, cid)
                        cname_final = ct_row["name"] if ct_row is not None else sel_ct
                        st.caption(f"Role: {contacts_df[contacts_df['contact_id']==cid]['role'].values[0]}")
                    net_type = st.selectbox("Interaction type", NET_TYPES)
                    medium   = st.selectbox("Medium", MEDIUM_OPTS)
                with nl2:
                    notes   = st.text_area("What happened? *", height=100)
                    fu_need = st.checkbox("Set follow-up reminder?")
                    fu_date = st.date_input("Follow-up by", value=date.today()+timedelta(7)) if fu_need else None
                if st.form_submit_button("💾 Log Interaction", use_container_width=True):
                    if not cname_final or not notes:
                        st.error("Contact name and notes required.")
                    else:
                        add_networking_log(UID, cid, cname_final, net_type, medium, notes, fu_need, fu_date)
                        st.success("Logged!")
                        st.rerun()

        with cn3:
            net_df = get_all_networking(UID)
            if net_df.empty:
                st.info("No interactions logged yet.")
            else:
                fu_only = st.checkbox("Pending follow-ups only")
                if fu_only:
                    net_df = net_df[(net_df["follow_up_needed"]==True)&(net_df["follow_up_done"]==False)]
                st.caption(f"{len(net_df)} interactions")
                for _, n in net_df.iterrows():
                    fu_badge = ""
                    if n["follow_up_needed"] and not n["follow_up_done"]:
                        fu_badge = f'<span class="badge b-amber">Follow-up: {str(n["follow_up_date"])}</span>'
                    elif n["follow_up_needed"] and n["follow_up_done"]:
                        fu_badge = '<span class="badge b-green">Follow-up done</span>'
                    nc1,nc2 = st.columns([4,1])
                    with nc1:
                        st.markdown(f"""<div class="log-item">
                            <b>{str(n['date'])}</b> · <b style="color:{NAVY}">{n['contact_name']}</b>
                            <span class="badge b-gray">{n['interaction_type']}</span>
                            <span class="badge b-blue">{n['medium']}</span>
                            {fu_badge}<br>
                            <span style="font-size:12px;color:{GRAY}">{n['notes']}</span>
                        </div>""", unsafe_allow_html=True)
                    with nc2:
                        if n["follow_up_needed"] and not n["follow_up_done"]:
                            if st.button("✓ Done", key=f"fu_{n['net_id']}"):
                                mark_followup_done(UID, n['net_id'])
                                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  CALENDAR — redesigned
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅  Calendar":
    today = date.today()
    if "cal_month" not in st.session_state:
        st.session_state["cal_month"] = today.month
    if "cal_year" not in st.session_state:
        st.session_state["cal_year"] = today.year
    if "cal_selected_day" not in st.session_state:
        st.session_state["cal_selected_day"] = today.day

    month = st.session_state["cal_month"]
    year  = st.session_state["cal_year"]

    # ── Top bar: arrows + month name + schedule button ──
    nav1, nav2, nav3, nav4, nav5 = st.columns([1, 3, 1, 1, 2])
    with nav1:
        if st.button("← Prev", use_container_width=True):
            if month == 1:
                st.session_state["cal_month"] = 12
                st.session_state["cal_year"]  = year - 1
            else:
                st.session_state["cal_month"] = month - 1
            st.session_state["cal_selected_day"] = 1
            st.rerun()
    with nav2:
        st.markdown(f"""<div style="text-align:center;font-size:18px;font-weight:700;
            color:{NAVY};padding:6px 0">{cal_lib.month_name[month]} {year}</div>""",
            unsafe_allow_html=True)
    with nav3:
        if st.button("Next →", use_container_width=True):
            if month == 12:
                st.session_state["cal_month"] = 1
                st.session_state["cal_year"]  = year + 1
            else:
                st.session_state["cal_month"] = month + 1
            st.session_state["cal_selected_day"] = 1
            st.rerun()
    with nav4:
        if st.button("Today", use_container_width=True):
            st.session_state["cal_month"] = today.month
            st.session_state["cal_year"]  = today.year
            st.session_state["cal_selected_day"] = today.day
            st.rerun()
    with nav5:
        if st.button("➕ Schedule Event", use_container_width=True):
            st.session_state["show_cal_form"] = not st.session_state.get("show_cal_form",False)

    # ── Schedule form ──
    if st.session_state.get("show_cal_form"):
        with st.form("cal_sched", clear_on_submit=True):
            st.markdown("#### Schedule New Event")
            cse1,cse2 = st.columns(2)
            with cse1:
                cse_title = st.text_input("Event title *")
                cse_type  = st.selectbox("Type", EVENT_TYPES)
                cse_with  = st.text_input("With whom *")
                all_t = get_all_tasks(UID)
                t_opts = {"No specific task": None}
                t_opts.update({f"{r['task_id']} · {r['task_name']}": r['task_id']
                               for _,r in all_t.iterrows()})
                linked = st.selectbox("Link to task", list(t_opts.keys()))
            with cse2:
                cse_date = st.date_input("Date *", value=today+timedelta(1))
                cse_time = st.time_input("Time *")
                cse_dur  = st.number_input("Duration (mins)", 15, 180, 30, 15)
                cse_ag   = st.text_area("Agenda", height=80)
            b1,b2 = st.columns(2)
            with b1:
                if st.form_submit_button("📅 Save Event", use_container_width=True):
                    if not cse_title or not cse_with:
                        st.error("Title and person required.")
                    else:
                        add_event(UID, t_opts[linked], cse_date,
                                  cse_time.strftime("%H:%M"), cse_dur,
                                  cse_type, cse_title, cse_ag, cse_with)
                        st.success("Scheduled!")
                        st.session_state["show_cal_form"] = False
                        st.rerun()
            with b2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state["show_cal_form"] = False
                    st.rerun()

    # ── Legend ──
    st.markdown(f"""
    <div style="display:flex;gap:16px;font-size:11px;color:{GRAY};margin:8px 0 4px;flex-wrap:wrap">
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
            background:{RED};margin-right:4px"></span>Deadline</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
            background:{BLUE};margin-right:4px"></span>Work logged</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
            background:{GREEN};margin-right:4px"></span>Communication</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
            background:{PURPLE};margin-right:4px"></span>Scheduled event</span>
        <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
            background:{AMBER};margin-right:4px"></span>Follow-up due</span>
    </div>""", unsafe_allow_html=True)

    tasks_cal, logs_cal, events_cal, net_cal = get_calendar_data(UID, year, month)

    # ── Day headers ──
    day_cols = st.columns(7)
    for i, h in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
        day_cols[i].markdown(
            f"<div style='text-align:center;font-size:11px;font-weight:600;color:{GRAY};"
            f"padding:6px 0;border-bottom:2px solid {BORDER};margin-bottom:6px'>{h}</div>",
            unsafe_allow_html=True)

    # ── Calendar grid ──
    selected_day = st.session_state.get("cal_selected_day", today.day)

    for week in cal_lib.monthcalendar(year, month):
        wcols = st.columns(7)
        for i, day in enumerate(week):
            with wcols[i]:
                if day == 0:
                    st.markdown("<div style='min-height:96px'></div>", unsafe_allow_html=True)
                    continue

                ds = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
                is_today    = (ds == today.isoformat())
                is_selected = (day == selected_day)

                dt  = tasks_cal[tasks_cal["deadline"].astype(str)==ds]  if not tasks_cal.empty  else pd.DataFrame()
                dl  = logs_cal[logs_cal["date"].astype(str)==ds]         if not logs_cal.empty   else pd.DataFrame()
                de  = events_cal[events_cal["date"].astype(str)==ds]     if not events_cal.empty else pd.DataFrame()
                dw  = dl[dl["type"]=="work"]                              if not dl.empty         else pd.DataFrame()
                dc  = dl[dl["type"]=="communication"]                     if not dl.empty         else pd.DataFrame()
                dfu = net_cal[net_cal["follow_up_date"].astype(str)==ds] if not net_cal.empty    else pd.DataFrame()

                has_content = not (dt.empty and dw.empty and dc.empty and de.empty and dfu.empty)

                # Cell colors
                if is_today:
                    bg, numcol, border = NAVY, WHITE, f"2px solid {NAVY}"
                elif is_selected:
                    bg, numcol, border = "#EBF5FB", BLUE, f"2px solid {BLUE}"
                elif has_content:
                    bg, numcol, border = WHITE, NAVY, f"1px solid {BORDER}"
                else:
                    bg, numcol, border = WHITE, "#94A3B8", f"1px solid #F1F5F9"

                # Dots
                dot_size = "display:inline-block;width:7px;height:7px;border-radius:50%;margin:0 1px"
                dots = ""
                if not dt.empty:  dots += f"<span style='{dot_size};background:{RED}'></span>"
                if not dw.empty:  dots += f"<span style='{dot_size};background:{'#fff' if is_today else BLUE}'></span>"
                if not dc.empty:  dots += f"<span style='{dot_size};background:{GREEN}'></span>"
                if not de.empty:  dots += f"<span style='{dot_size};background:{PURPLE}'></span>"
                if not dfu.empty: dots += f"<span style='{dot_size};background:{AMBER}'></span>"

                # Preview text
                preview = ""
                if not de.empty:
                    tc = "#fff" if is_today else PURPLE
                    preview += f"<div style='font-size:9px;color:{tc};overflow:hidden;white-space:nowrap;text-overflow:ellipsis;margin-top:2px'>🕐 {de.iloc[0]['time']}</div>"
                if not dt.empty:
                    tc = "#fff" if is_today else RED
                    preview += f"<div style='font-size:9px;color:{tc};overflow:hidden;white-space:nowrap;text-overflow:ellipsis'>📌 {dt.iloc[0]['task_id']}</div>"

                st.markdown(f"""
                <div style='border:{border};border-radius:10px;background:{bg};
                    padding:8px 8px 6px;min-height:96px;margin:2px'>
                    <div style='font-size:13px;font-weight:{"700" if is_today or is_selected else "500"};
                        color:{numcol};margin-bottom:5px'>{day}</div>
                    <div style='line-height:1.6'>{dots}</div>
                    {preview}
                </div>""", unsafe_allow_html=True)

                if st.button(str(day), key=f"cd_{year}_{month}_{day}",
                             help=f"View {cal_lib.month_name[month]} {day}"):
                    st.session_state["cal_selected_day"] = day
                    st.rerun()

    # ── Day detail panel ──
    sel_str = f"{year}-{str(month).zfill(2)}-{str(selected_day).zfill(2)}"
    d_tasks  = tasks_cal[tasks_cal["deadline"].astype(str)==sel_str]  if not tasks_cal.empty  else pd.DataFrame()
    d_events = events_cal[events_cal["date"].astype(str)==sel_str]    if not events_cal.empty else pd.DataFrame()
    d_work   = logs_cal[(logs_cal["date"].astype(str)==sel_str)&(logs_cal["type"]=="work")] if not logs_cal.empty else pd.DataFrame()
    d_comms  = logs_cal[(logs_cal["date"].astype(str)==sel_str)&(logs_cal["type"]=="communication")] if not logs_cal.empty else pd.DataFrame()
    d_fu     = net_cal[net_cal["follow_up_date"].astype(str)==sel_str] if not net_cal.empty  else pd.DataFrame()

    st.markdown(f"""
    <div style="margin:16px 0 10px;padding:10px 16px;background:{NAVY};border-radius:10px;
        display:flex;align-items:center;justify-content:space-between">
        <div style="font-size:14px;font-weight:600;color:{WHITE}">
            {cal_lib.month_name[month]} {selected_day}, {year}
        </div>
        <div style="font-size:11px;color:#8899BB">Click any date above to view details</div>
    </div>""", unsafe_allow_html=True)

    if d_tasks.empty and d_events.empty and d_work.empty and d_comms.empty and d_fu.empty:
        st.markdown(f"""<div style="text-align:center;padding:20px;color:{GRAY};
            border:1px dashed {BORDER};border-radius:10px;font-size:13px">
            Nothing logged for this date</div>""", unsafe_allow_html=True)
    else:
        dd1,dd2,dd3,dd4 = st.columns(4)
        lbl = f"font-size:11px;font-weight:700;color:{GRAY};text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px"

        with dd1:
            st.markdown(f'<div style="{lbl}">Tasks due</div>', unsafe_allow_html=True)
            if d_tasks.empty: st.caption("None")
            else:
                for _,r in d_tasks.iterrows():
                    sc = GREEN if r['status']=="Complete" else RED if r['status']=="Blocked" else BLUE
                    st.markdown(f"""<div class="log-item" style="border-left:3px solid {sc}">
                        <div style="font-size:12px;font-weight:600">{r['task_id']}</div>
                        <div style="font-size:11px;color:{GRAY}">{str(r['task_name'])[:30]}</div>
                        <span class="badge b-gray">{r['status']}</span>
                    </div>""", unsafe_allow_html=True)

        with dd2:
            st.markdown(f'<div style="{lbl}">Scheduled events</div>', unsafe_allow_html=True)
            if d_events.empty: st.caption("None")
            else:
                for _,ev in d_events.iterrows():
                    done_b = '<span class="badge b-green">Done</span>' if ev["status"]=="done" else '<span class="badge b-purple">Upcoming</span>'
                    st.markdown(f"""<div class="event-item">
                        <div style="font-size:13px;font-weight:600">{ev['time']} · {ev['title']}</div>
                        <div style="font-size:11px;color:#5B21B6">{ev['type']} · {ev['with_whom']} · {ev['duration_mins']}min</div>
                        {done_b}
                    </div>""", unsafe_allow_html=True)
                    if ev["status"]=="upcoming":
                        if st.button("✓ Mark done", key=f"cald_{ev['event_id']}_{selected_day}"):
                            update_event_status(UID, ev["event_id"], "done")
                            st.rerun()

        with dd3:
            st.markdown(f'<div style="{lbl}">Work logged</div>', unsafe_allow_html=True)
            if d_work.empty: st.caption("None")
            else:
                total_h = d_work["time_spent"].sum()
                st.markdown(f"<div style='font-size:12px;font-weight:600;color:{BLUE};margin-bottom:6px'>{total_h:.1f}h total</div>",
                            unsafe_allow_html=True)
                for _,l in d_work.iterrows():
                    st.markdown(f"""<div class="log-item">
                        <span style="font-size:12px;font-weight:600;color:{BLUE}">{l['task_id']}</span>
                        · {l['time_spent']}h
                    </div>""", unsafe_allow_html=True)

        with dd4:
            st.markdown(f'<div style="{lbl}">Follow-ups due</div>', unsafe_allow_html=True)
            if d_fu.empty: st.caption("None")
            else:
                for _,f in d_fu.iterrows():
                    done = bool(f["follow_up_done"])
                    st.markdown(f"""<div class="queue-item">
                        <div style="font-size:12px;font-weight:600">Follow up with {f['contact_name']}</div>
                        {"<span class='badge b-green'>Done</span>" if done else "<span class='badge b-amber'>Pending</span>"}
                    </div>""", unsafe_allow_html=True)
                    if not done:
                        if st.button("✓ Done", key=f"fucd_{f['net_id']}_{selected_day}"):
                            mark_followup_done(UID, f['net_id'])
                            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️  Admin":
    if ROLE != "admin":
        st.error("Access denied.")
        st.stop()
    st.title("Admin Panel")
    render_admin_users()
