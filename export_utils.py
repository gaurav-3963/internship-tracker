import io
import pandas as pd
from datetime import date
from database import export_user_data

def get_csv(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def render_export_buttons(uid, username):
    """Renders 4 clean download buttons — one per CSV."""
    import streamlit as st
    tasks, work_log, comms, networking, contacts = export_user_data(uid)
    today = date.today().strftime("%d%b%Y").lower()
    slug  = username.lower().replace(" ", "_")

    st.markdown("#### Export Your Data")
    st.caption("Download any table as a CSV file. Only your own data is included.")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            label=f"📋  Tasks ({len(tasks)} rows)",
            data=get_csv(tasks),
            file_name=f"tasks_{slug}_{today}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.download_button(
            label=f"💬  Communications ({len(comms)} rows)",
            data=get_csv(comms),
            file_name=f"communications_{slug}_{today}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c2:
        st.download_button(
            label=f"📝  Daily Work Log ({len(work_log)} rows)",
            data=get_csv(work_log),
            file_name=f"work_log_{slug}_{today}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.download_button(
            label=f"🤝  Networking ({len(networking)} rows)",
            data=get_csv(networking),
            file_name=f"networking_{slug}_{today}.csv",
            mime="text/csv",
            use_container_width=True
        )
