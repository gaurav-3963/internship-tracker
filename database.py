import sqlite3
import pandas as pd
from datetime import date, timedelta

DB_PATH = "internship.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        task_name TEXT NOT NULL,
        project TEXT,
        assigned_by TEXT,
        assigned_date TEXT,
        deadline TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Not Started',
        next_step TEXT,
        last_updated TEXT,
        total_hours REAL DEFAULT 0,
        closed_date TEXT,
        notes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        task_id TEXT,
        type TEXT,
        work_done TEXT,
        time_spent REAL DEFAULT 0,
        blockers TEXT,
        next_step TEXT,
        status_update TEXT,
        deadline_update TEXT,
        stakeholder TEXT,
        medium TEXT,
        discussion TEXT,
        action_item TEXT,
        learning_note TEXT,
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS scheduled_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        date TEXT,
        time TEXT,
        duration_mins INTEGER DEFAULT 30,
        type TEXT,
        title TEXT,
        agenda TEXT,
        with_whom TEXT,
        contact_id INTEGER,
        status TEXT DEFAULT 'upcoming',
        notes TEXT,
        FOREIGN KEY (task_id) REFERENCES tasks(task_id),
        FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS manager_queue (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        date_added TEXT,
        question TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'pending',
        answer TEXT,
        resolved_date TEXT,
        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT,
        relationship TEXT,
        company TEXT,
        email TEXT,
        phone TEXT,
        linkedin TEXT,
        notes TEXT,
        date_added TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS networking_log (
        net_id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        contact_id INTEGER,
        contact_name TEXT,
        interaction_type TEXT,
        medium TEXT,
        notes TEXT,
        follow_up_needed INTEGER DEFAULT 0,
        follow_up_date TEXT,
        follow_up_done INTEGER DEFAULT 0,
        FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
    )""")

    conn.commit()
    conn.close()

# ── Tasks ──────────────────────────────────────────────────────────────────────
def get_next_task_id():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks")
    n = c.fetchone()[0]
    conn.close()
    return f"T-{str(n).zfill(3)}"

def add_task(task_name, project, assigned_by, deadline_days, priority, notes):
    conn = get_conn()
    c = conn.cursor()
    tid = get_next_task_id()
    today = date.today().isoformat()
    deadline = (date.today() + timedelta(days=int(deadline_days))).isoformat()
    c.execute("""INSERT INTO tasks
        (task_id,task_name,project,assigned_by,assigned_date,deadline,priority,status,last_updated,total_hours,notes)
        VALUES (?,?,?,?,?,?,?,'Not Started',?,0,?)""",
        (tid, task_name, project, assigned_by, today, deadline, priority, today, notes))
    conn.commit()
    conn.close()
    return tid

def get_all_tasks():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM tasks ORDER BY deadline ASC", conn)
    conn.close()
    return df

def get_task(task_id):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM tasks WHERE task_id=?", conn, params=(task_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def update_task(task_id, **kwargs):
    conn = get_conn()
    c = conn.cursor()
    kwargs['last_updated'] = date.today().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [task_id]
    c.execute(f"UPDATE tasks SET {sets} WHERE task_id=?", vals)
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_conn()
    c = conn.cursor()
    for tbl in ['activity_log','scheduled_events','manager_queue']:
        c.execute(f"DELETE FROM {tbl} WHERE task_id=?", (task_id,))
    c.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
    conn.commit()
    conn.close()

# ── Activity Log ───────────────────────────────────────────────────────────────
def add_log(task_id, log_type, work_done="", time_spent=0, blockers="",
            next_step="", status_update="", deadline_update="",
            stakeholder="", medium="", discussion="", action_item="", learning_note=""):
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""INSERT INTO activity_log
        (date,task_id,type,work_done,time_spent,blockers,next_step,status_update,
         deadline_update,stakeholder,medium,discussion,action_item,learning_note)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (today, task_id, log_type, work_done, time_spent, blockers, next_step,
         status_update, deadline_update, stakeholder, medium, discussion, action_item, learning_note))

    updates = {'last_updated': today}
    if next_step:
        updates['next_step'] = next_step
    if time_spent and float(time_spent) > 0:
        c.execute("SELECT COALESCE(SUM(time_spent),0) FROM activity_log WHERE task_id=? AND type='work'", (task_id,))
        updates['total_hours'] = round(c.fetchone()[0] + float(time_spent), 2)
    if status_update and status_update != "No change":
        updates['status'] = status_update
        if status_update == "Complete":
            updates['closed_date'] = today
    if deadline_update:
        updates['deadline'] = deadline_update

    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [task_id]
    c.execute(f"UPDATE tasks SET {sets} WHERE task_id=?", vals)
    conn.commit()
    conn.close()

def get_logs_for_task(task_id):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM activity_log WHERE task_id=? ORDER BY date DESC, log_id DESC",
        conn, params=(task_id,))
    conn.close()
    return df

def get_recent_activity(limit=6):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM activity_log ORDER BY date DESC, log_id DESC LIMIT ?",
        conn, params=(limit,))
    conn.close()
    return df

# ── Scheduled Events ───────────────────────────────────────────────────────────
def add_event(task_id, event_date, event_time, duration, event_type, title, agenda, with_whom, contact_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO scheduled_events
        (task_id,date,time,duration_mins,type,title,agenda,with_whom,contact_id,status)
        VALUES (?,?,?,?,?,?,?,?,?,'upcoming')""",
        (task_id or None, event_date, event_time, duration, event_type, title, agenda, with_whom, contact_id or None))
    conn.commit()
    conn.close()

def get_events(status=None, event_date=None):
    conn = get_conn()
    query = "SELECT * FROM scheduled_events WHERE 1=1"
    params = []
    if status:
        query += " AND status=?"
        params.append(status)
    if event_date:
        query += " AND date=?"
        params.append(event_date)
    query += " ORDER BY date ASC, time ASC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_events_for_month(year, month):
    prefix = f"{year}-{str(month).zfill(2)}"
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM scheduled_events WHERE date LIKE ?", conn, params=(f"{prefix}%",))
    conn.close()
    return df

def update_event_status(event_id, status, notes=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE scheduled_events SET status=?, notes=? WHERE event_id=?", (status, notes, event_id))
    conn.commit()
    conn.close()

# ── Manager Queue ──────────────────────────────────────────────────────────────
def add_manager_item(task_id, question, priority):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO manager_queue (task_id,date_added,question,priority,status)
        VALUES (?,?,?,?,'pending')""",
        (task_id or None, date.today().isoformat(), question, priority))
    conn.commit()
    conn.close()

def get_manager_queue(status=None):
    conn = get_conn()
    query = """SELECT m.*, t.task_name FROM manager_queue m
               LEFT JOIN tasks t ON m.task_id=t.task_id"""
    params = []
    if status:
        query += " WHERE m.status=?"
        params.append(status)
    query += " ORDER BY CASE m.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, m.date_added ASC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def resolve_manager_item(item_id, answer):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE manager_queue SET status='resolved', answer=?, resolved_date=? WHERE item_id=?",
              (answer, date.today().isoformat(), item_id))
    conn.commit()
    conn.close()

# ── Contacts ───────────────────────────────────────────────────────────────────
def add_contact(name, role, relationship, company, email, phone, linkedin, notes):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO contacts (name,role,relationship,company,email,phone,linkedin,notes,date_added)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (name, role, relationship, company, email, phone, linkedin, notes, date.today().isoformat()))
    conn.commit()
    conn.close()

def get_all_contacts():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM contacts ORDER BY relationship, name", conn)
    conn.close()
    return df

def get_contact(contact_id):
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM contacts WHERE contact_id=?", conn, params=(contact_id,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def delete_contact(contact_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE contact_id=?", (contact_id,))
    conn.commit()
    conn.close()

# ── Networking Log ─────────────────────────────────────────────────────────────
def add_networking_log(contact_id, contact_name, interaction_type, medium, notes, follow_up_needed, follow_up_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO networking_log
        (date,contact_id,contact_name,interaction_type,medium,notes,follow_up_needed,follow_up_date,follow_up_done)
        VALUES (?,?,?,?,?,?,?,?,0)""",
        (date.today().isoformat(), contact_id or None, contact_name,
         interaction_type, medium, notes,
         1 if follow_up_needed else 0,
         follow_up_date if follow_up_needed else None))
    conn.commit()
    conn.close()

def get_all_networking():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM networking_log ORDER BY date DESC", conn)
    conn.close()
    return df

def get_pending_followups():
    conn = get_conn()
    today = date.today().isoformat()
    df = pd.read_sql_query("""SELECT * FROM networking_log
        WHERE follow_up_needed=1 AND follow_up_done=0
        ORDER BY follow_up_date ASC""", conn)
    conn.close()
    return df

def mark_followup_done(net_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE networking_log SET follow_up_done=1 WHERE net_id=?", (net_id,))
    conn.commit()
    conn.close()

# ── KPIs ───────────────────────────────────────────────────────────────────────
def get_kpis():
    conn = get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM tasks"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE status='Complete'"); completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE status='In Progress'"); in_prog = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE status='Blocked'"); blocked = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE deadline<? AND status!='Complete'", (today,)); overdue = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total_hours),0) FROM tasks"); hours = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM manager_queue WHERE status='pending'"); pending_q = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM scheduled_events WHERE date=? AND status='upcoming'", (today,)); today_ev = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM networking_log WHERE follow_up_needed=1 AND follow_up_done=0"); followups = c.fetchone()[0]
    conn.close()
    progress = round(completed / total * 100, 1) if total > 0 else 0
    return dict(total=total, completed=completed, in_progress=in_prog,
                blocked=blocked, overdue=overdue, hours=round(hours,1),
                progress=progress, pending_questions=pending_q,
                today_events=today_ev, pending_followups=followups)

# ── Calendar ───────────────────────────────────────────────────────────────────
def get_calendar_data(year, month):
    prefix = f"{year}-{str(month).zfill(2)}"
    conn = get_conn()
    tasks_df   = pd.read_sql_query("SELECT task_id,task_name,deadline,status,priority FROM tasks WHERE deadline LIKE ?", conn, params=(f"{prefix}%",))
    logs_df    = pd.read_sql_query("SELECT date,task_id,type,time_spent FROM activity_log WHERE date LIKE ?", conn, params=(f"{prefix}%",))
    events_df  = pd.read_sql_query("SELECT * FROM scheduled_events WHERE date LIKE ?", conn, params=(f"{prefix}%",))
    network_df = pd.read_sql_query("SELECT * FROM networking_log WHERE date LIKE ? OR follow_up_date LIKE ?", conn, params=(f"{prefix}%", f"{prefix}%"))
    conn.close()
    return tasks_df, logs_df, events_df, network_df
