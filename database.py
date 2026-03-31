import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import date, timedelta
import os
import secrets
import string
from dotenv import load_dotenv
import bcrypt
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def read_sql(query, params=None):
    import re
    if params:
        counter = [0]
        def replacer(m):
            key = f"p{counter[0]}"
            counter[0] += 1
            return f":{key}"
        converted = re.sub(r'%s', replacer, query)
        param_dict = {f"p{i}": v for i, v in enumerate(params)}
        with get_engine().connect() as conn:
            return pd.read_sql(text(converted), conn, params=param_dict)
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        firm TEXT,
        phone TEXT,
        internship_start DATE,
        internship_end DATE,
        role TEXT DEFAULT 'intern',
        is_active BOOLEAN DEFAULT TRUE,
        profile_complete BOOLEAN DEFAULT FALSE,
        created_at DATE DEFAULT CURRENT_DATE,
        last_login DATE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT NOT NULL,
        user_id UUID REFERENCES users(user_id),
        task_name TEXT NOT NULL,
        project TEXT,
        assigned_by TEXT,
        assigned_date DATE,
        deadline DATE,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Not Started',
        next_step TEXT,
        last_updated DATE,
        total_hours REAL DEFAULT 0,
        closed_date DATE,
        notes TEXT,
        PRIMARY KEY (task_id, user_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        log_id SERIAL PRIMARY KEY,
        user_id UUID REFERENCES users(user_id),
        date DATE,
        task_id TEXT,
        type TEXT,
        work_done TEXT,
        time_spent REAL DEFAULT 0,
        blockers TEXT,
        next_step TEXT,
        status_update TEXT,
        deadline_update DATE,
        stakeholder TEXT,
        medium TEXT,
        discussion TEXT,
        action_item TEXT,
        learning_note TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS scheduled_events (
        event_id SERIAL PRIMARY KEY,
        user_id UUID REFERENCES users(user_id),
        task_id TEXT,
        date DATE,
        time TEXT,
        duration_mins INTEGER DEFAULT 30,
        type TEXT,
        title TEXT,
        agenda TEXT,
        with_whom TEXT,
        status TEXT DEFAULT 'upcoming',
        notes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS manager_queue (
        item_id SERIAL PRIMARY KEY,
        user_id UUID REFERENCES users(user_id),
        task_id TEXT,
        date_added DATE,
        question TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'pending',
        answer TEXT,
        resolved_date DATE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        contact_id SERIAL PRIMARY KEY,
        user_id UUID REFERENCES users(user_id),
        name TEXT NOT NULL,
        role TEXT,
        relationship TEXT,
        company TEXT,
        email TEXT,
        phone TEXT,
        linkedin TEXT,
        notes TEXT,
        date_added DATE DEFAULT CURRENT_DATE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS networking_log (
        net_id SERIAL PRIMARY KEY,
        user_id UUID REFERENCES users(user_id),
        date DATE,
        contact_id INTEGER,
        contact_name TEXT,
        interaction_type TEXT,
        medium TEXT,
        notes TEXT,
        follow_up_needed BOOLEAN DEFAULT FALSE,
        follow_up_date DATE,
        follow_up_done BOOLEAN DEFAULT FALSE
    )""")

    # Safe column additions for existing databases
    for col, defn in [("phone","TEXT"),("internship_start","DATE"),
                      ("internship_end","DATE"),("profile_complete","BOOLEAN DEFAULT FALSE")]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {defn}")
            conn.commit()
        except Exception:
            conn.rollback()

    conn.commit()
    c.close(); conn.close()

# ── Password ───────────────────────────────────────────────────────────────────
def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def generate_temp_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# ── User management ────────────────────────────────────────────────────────────
def create_user_by_admin(email, role="intern"):
    conn = get_conn()
    c = conn.cursor()
    try:
        temp_pw = generate_temp_password()
        h = hash_password(temp_pw)
        c.execute("""INSERT INTO users (email,password_hash,role,profile_complete)
                     VALUES (%s,%s,%s,FALSE) RETURNING user_id""",
                  (email.lower(), h, role))
        uid = c.fetchone()[0]
        conn.commit()
        return str(uid), temp_pw, None
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None, None, "Email already registered."
    finally:
        c.close(); conn.close()

def create_user(name, email, password, firm, role="intern"):
    conn = get_conn()
    c = conn.cursor()
    try:
        h = hash_password(password)
        c.execute("""INSERT INTO users (name,email,password_hash,firm,role,profile_complete)
                     VALUES (%s,%s,%s,%s,%s,TRUE) RETURNING user_id""",
                  (name, email.lower(), h, firm, role))
        uid = c.fetchone()[0]
        conn.commit()
        return str(uid), None
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None, "Email already registered."
    finally:
        c.close(); conn.close()

def login_user(email, password):
    conn = get_conn()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM users WHERE email=%s AND is_active=TRUE", (email.lower(),))
    user = c.fetchone()
    if user and verify_password(password, user["password_hash"]):
        c.execute("UPDATE users SET last_login=%s WHERE user_id=%s",
                  (date.today(), user["user_id"]))
        conn.commit()
        c.close(); conn.close()
        return dict(user), None
    c.close(); conn.close()
    return None, "Invalid email or password."

def complete_profile(user_id, name, firm, phone, internship_start, internship_end, new_password):
    conn = get_conn()
    c = conn.cursor()
    h = hash_password(new_password)
    c.execute("""UPDATE users SET name=%s,firm=%s,phone=%s,
        internship_start=%s,internship_end=%s,
        password_hash=%s,profile_complete=TRUE WHERE user_id=%s""",
        (name, firm, phone, internship_start, internship_end, h, user_id))
    conn.commit()
    c.close(); conn.close()

def get_all_users():
    return read_sql("""SELECT user_id,name,email,firm,phone,role,
        is_active,profile_complete,created_at,last_login
        FROM users ORDER BY created_at DESC""")

def toggle_user_active(user_id, active):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_active=%s WHERE user_id=%s", (active, user_id))
    conn.commit()
    c.close(); conn.close()

def change_password(user_id, new_password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash=%s WHERE user_id=%s",
              (hash_password(new_password), user_id))
    conn.commit()
    c.close(); conn.close()

# ── Tasks ──────────────────────────────────────────────────────────────────────
def get_next_task_id(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=%s", (uid,))
    n = c.fetchone()[0]
    c.close(); conn.close()
    return f"T-{str(n).zfill(3)}"

def add_task(uid, task_name, project, assigned_by, deadline_days, priority, notes):
    conn = get_conn()
    c = conn.cursor()
    tid = get_next_task_id(uid)
    today = date.today()
    deadline = today + timedelta(days=int(deadline_days))
    c.execute("""INSERT INTO tasks
        (task_id,user_id,task_name,project,assigned_by,assigned_date,deadline,
         priority,status,last_updated,total_hours,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Not Started',%s,0,%s)""",
        (tid,uid,task_name,project,assigned_by,today,deadline,priority,today,notes))
    conn.commit()
    c.close(); conn.close()
    return tid

def get_all_tasks(uid):
    return read_sql("SELECT * FROM tasks WHERE user_id=%s ORDER BY deadline ASC", params=(uid,))

def get_task(uid, task_id):
    df = read_sql("SELECT * FROM tasks WHERE user_id=%s AND task_id=%s", params=(uid, task_id))
    return df.iloc[0] if not df.empty else None

def update_task(uid, task_id, **kwargs):
    conn = get_conn()
    c = conn.cursor()
    kwargs["last_updated"] = date.today()
    sets = ", ".join(f"{k}=%s" for k in kwargs)
    vals = list(kwargs.values()) + [uid, task_id]
    c.execute(f"UPDATE tasks SET {sets} WHERE user_id=%s AND task_id=%s", vals)
    conn.commit()
    c.close(); conn.close()

def delete_task(uid, task_id):
    conn = get_conn()
    c = conn.cursor()
    for tbl in ["activity_log","scheduled_events","manager_queue"]:
        c.execute(f"DELETE FROM {tbl} WHERE user_id=%s AND task_id=%s", (uid, task_id))
    c.execute("DELETE FROM tasks WHERE user_id=%s AND task_id=%s", (uid, task_id))
    conn.commit()
    c.close(); conn.close()

# ── Activity Log ───────────────────────────────────────────────────────────────
def add_log(uid, task_id, log_type, work_done="", time_spent=0, blockers="",
            next_step="", status_update="", deadline_update=None,
            stakeholder="", medium="", discussion="", action_item="", learning_note=""):
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    c.execute("""INSERT INTO activity_log
        (user_id,date,task_id,type,work_done,time_spent,blockers,next_step,
         status_update,deadline_update,stakeholder,medium,discussion,action_item,learning_note)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (uid,today,task_id,log_type,work_done,time_spent,blockers,next_step,
         status_update,deadline_update,stakeholder,medium,discussion,action_item,learning_note))

    updates = {"last_updated": today}
    if next_step:
        updates["next_step"] = next_step
    if time_spent and float(time_spent) > 0:
        c.execute("""SELECT COALESCE(SUM(time_spent),0) FROM activity_log
                     WHERE user_id=%s AND task_id=%s AND type='work'""", (uid, task_id))
        updates["total_hours"] = round(c.fetchone()[0] + float(time_spent), 2)
    if status_update and status_update != "No change":
        updates["status"] = status_update
        if status_update == "Complete":
            updates["closed_date"] = today
    if deadline_update:
        updates["deadline"] = deadline_update

    sets = ", ".join(f"{k}=%s" for k in updates)
    vals = list(updates.values()) + [uid, task_id]
    c.execute(f"UPDATE tasks SET {sets} WHERE user_id=%s AND task_id=%s", vals)
    conn.commit()
    c.close(); conn.close()

def get_logs_for_task(uid, task_id):
    return read_sql("""SELECT * FROM activity_log WHERE user_id=%s AND task_id=%s
                       ORDER BY date DESC, log_id DESC""", params=(uid, task_id))

def get_recent_activity(uid, limit=6):
    return read_sql("""SELECT * FROM activity_log WHERE user_id=%s
                       ORDER BY date DESC, log_id DESC LIMIT %s""", params=(uid, limit))

# ── Scheduled Events ───────────────────────────────────────────────────────────
def add_event(uid, task_id, event_date, event_time, duration, event_type, title, agenda, with_whom):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO scheduled_events
        (user_id,task_id,date,time,duration_mins,type,title,agenda,with_whom,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'upcoming')""",
        (uid, task_id or None, event_date, event_time, duration, event_type, title, agenda, with_whom))
    conn.commit()
    c.close(); conn.close()

def get_events(uid, status=None, event_date=None):
    q = "SELECT * FROM scheduled_events WHERE user_id=%s"
    p = [uid]
    if status:     q += " AND status=%s";  p.append(status)
    if event_date: q += " AND date=%s";    p.append(event_date)
    q += " ORDER BY date ASC, time ASC"
    return read_sql(q, params=tuple(p))

def get_events_for_month(uid, year, month):
    return read_sql("""SELECT * FROM scheduled_events WHERE user_id=%s
        AND EXTRACT(YEAR FROM date)=%s AND EXTRACT(MONTH FROM date)=%s""",
        params=(uid, year, month))

def update_event_status(uid, event_id, status, notes=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE scheduled_events SET status=%s,notes=%s WHERE event_id=%s AND user_id=%s",
              (status, notes, event_id, uid))
    conn.commit()
    c.close(); conn.close()

# ── Manager Queue ──────────────────────────────────────────────────────────────
def add_manager_item(uid, task_id, question, priority):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO manager_queue (user_id,task_id,date_added,question,priority,status)
                 VALUES (%s,%s,%s,%s,%s,'pending')""",
              (uid, task_id or None, date.today(), question, priority))
    conn.commit()
    c.close(); conn.close()

def get_manager_queue(uid, status=None):
    q = """SELECT m.*,t.task_name FROM manager_queue m
           LEFT JOIN tasks t ON m.task_id=t.task_id AND t.user_id=m.user_id
           WHERE m.user_id=%s"""
    p = [uid]
    if status: q += " AND m.status=%s"; p.append(status)
    q += " ORDER BY CASE m.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,m.date_added ASC"
    return read_sql(q, params=tuple(p))

def resolve_manager_item(uid, item_id, answer):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""UPDATE manager_queue SET status='resolved',answer=%s,resolved_date=%s
                 WHERE item_id=%s AND user_id=%s""",
              (answer, date.today(), item_id, uid))
    conn.commit()
    c.close(); conn.close()

# ── Contacts ───────────────────────────────────────────────────────────────────
def add_contact(uid, name, role, relationship, company, email, phone, linkedin, notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO contacts
        (user_id,name,role,relationship,company,email,phone,linkedin,notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (uid,name,role,relationship,company,email,phone,linkedin,notes))
    conn.commit()
    c.close(); conn.close()

def get_all_contacts(uid):
    return read_sql("SELECT * FROM contacts WHERE user_id=%s ORDER BY relationship,name", params=(uid,))

def get_contact(uid, contact_id):
    df = read_sql("SELECT * FROM contacts WHERE user_id=%s AND contact_id=%s", params=(uid, contact_id))
    return df.iloc[0] if not df.empty else None

def delete_contact(uid, contact_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE user_id=%s AND contact_id=%s", (uid, contact_id))
    conn.commit()
    c.close(); conn.close()

# ── Networking Log ─────────────────────────────────────────────────────────────
def add_networking_log(uid, contact_id, contact_name, interaction_type,
                       medium, notes, follow_up_needed, follow_up_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO networking_log
        (user_id,date,contact_id,contact_name,interaction_type,medium,notes,
         follow_up_needed,follow_up_date,follow_up_done)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE)""",
        (uid, date.today(), contact_id or None, contact_name,
         interaction_type, medium, notes, follow_up_needed,
         follow_up_date if follow_up_needed else None))
    conn.commit()
    c.close(); conn.close()

def get_all_networking(uid):
    return read_sql("SELECT * FROM networking_log WHERE user_id=%s ORDER BY date DESC", params=(uid,))

def get_pending_followups(uid):
    return read_sql("""SELECT * FROM networking_log WHERE user_id=%s
        AND follow_up_needed=TRUE AND follow_up_done=FALSE
        ORDER BY follow_up_date ASC""", params=(uid,))

def mark_followup_done(uid, net_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE networking_log SET follow_up_done=TRUE WHERE net_id=%s AND user_id=%s",
              (net_id, uid))
    conn.commit()
    c.close(); conn.close()

# ── KPIs — single query ────────────────────────────────────────────────────────
def get_kpis(uid):
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    c.execute("""SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE status='Complete'),
        COUNT(*) FILTER (WHERE status='In Progress'),
        COUNT(*) FILTER (WHERE status='Blocked'),
        COUNT(*) FILTER (WHERE deadline < %s AND status != 'Complete'),
        COUNT(*) FILTER (WHERE deadline >= %s AND deadline <= %s AND status != 'Complete'),
        COALESCE(SUM(total_hours),0)
        FROM tasks WHERE user_id=%s""",
        (today, today, today + timedelta(days=2), uid))
    total,completed,in_prog,blocked,overdue,due_soon,hours = c.fetchone()

    c.execute("SELECT COUNT(*) FROM manager_queue WHERE user_id=%s AND status='pending'", (uid,))
    pending_q = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM scheduled_events WHERE user_id=%s AND date=%s AND status='upcoming'", (uid, today))
    today_ev = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM networking_log WHERE user_id=%s AND follow_up_needed=TRUE AND follow_up_done=FALSE", (uid,))
    followups = c.fetchone()[0]

    c.close(); conn.close()
    progress = round(completed / total * 100, 1) if total > 0 else 0
    return dict(total=total,completed=completed,in_progress=in_prog,blocked=blocked,
                overdue=overdue,due_soon=due_soon,hours=round(hours,1),
                progress=progress,pending_questions=pending_q,
                today_events=today_ev,pending_followups=followups)

# ── Calendar ───────────────────────────────────────────────────────────────────
def get_calendar_data(uid, year, month):
    tasks_df  = read_sql("""SELECT task_id,task_name,deadline,status,priority FROM tasks
        WHERE user_id=%s AND EXTRACT(YEAR FROM deadline)=%s AND EXTRACT(MONTH FROM deadline)=%s""",
        params=(uid,year,month))
    logs_df   = read_sql("""SELECT date,task_id,type,time_spent FROM activity_log
        WHERE user_id=%s AND EXTRACT(YEAR FROM date)=%s AND EXTRACT(MONTH FROM date)=%s""",
        params=(uid,year,month))
    events_df = read_sql("""SELECT * FROM scheduled_events WHERE user_id=%s
        AND EXTRACT(YEAR FROM date)=%s AND EXTRACT(MONTH FROM date)=%s""",
        params=(uid,year,month))
    net_df    = read_sql("""SELECT * FROM networking_log WHERE user_id=%s
        AND EXTRACT(YEAR FROM follow_up_date)=%s AND EXTRACT(MONTH FROM follow_up_date)=%s""",
        params=(uid,year,month))
    return tasks_df, logs_df, events_df, net_df

# ── Export — clean, 5 targeted CSVs ───────────────────────────────────────────
def export_user_data(uid):
    tasks = read_sql("""SELECT task_id,task_name,project,assigned_by,assigned_date,
        deadline,priority,status,next_step,last_updated,total_hours,closed_date,notes
        FROM tasks WHERE user_id=%s ORDER BY deadline""", params=(uid,))
    work_log = read_sql("""SELECT date,task_id,work_done,time_spent,blockers,
        next_step,status_update,deadline_update
        FROM activity_log WHERE user_id=%s AND type='work' ORDER BY date DESC""", params=(uid,))
    comms = read_sql("""SELECT date,task_id,stakeholder,medium,discussion,action_item
        FROM activity_log WHERE user_id=%s AND type='communication' ORDER BY date DESC""", params=(uid,))
    networking = read_sql("""SELECT date,contact_name,interaction_type,medium,
        notes,follow_up_needed,follow_up_date,follow_up_done
        FROM networking_log WHERE user_id=%s ORDER BY date DESC""", params=(uid,))
    contacts = read_sql("""SELECT name,role,relationship,company,email,phone,linkedin,notes
        FROM contacts WHERE user_id=%s ORDER BY relationship,name""", params=(uid,))
    return tasks, work_log, comms, networking, contacts
