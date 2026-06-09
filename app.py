"""
app.py — Employee Attendance & Log Tracking Application
Stack: Python · Streamlit · SQLite · Pandas · Plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import calendar

from database import (
    init_db, get_setting, set_setting,
    PRESET_ROLES, DAYS_OF_WEEK,
    add_employee, get_all_employees, get_employee,
    update_employee, deactivate_employee, delete_employee,
    get_schedule, upsert_schedule,
    upsert_attendance, get_attendance_for_date,
    get_monthly_summary, get_employee_daily_log,
    get_attendance_range,
)

# ─── Bootstrap ────────────────────────────────────────────────────────────────
init_db()

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AttendIQ",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #28282B; /* Dark charcoal text for readability */
  }

  /* Target the main Streamlit app background */
  .stApp {
    background-color: #FFFAF0 !important; /* Floral White */
  }

  h1, h2, h3, .stMarkdown h1, .stMarkdown h2 {
    font-family: 'Syne', sans-serif !important;
    color: #FFFAF0 !important; /* Making headers brown looks great on floral white */
  }

/* Sidebar */
  [data-testid="stSidebar"] {
    background: #765341; /* Brown */

  }
  [data-testid="stSidebar"] * { color: #e8eaf0 !important; }

  /* Main background */
  .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    background: #FFFAFO;

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #FFFAFO;
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 1rem 1.25rem;
  }
  [data-testid="metric-container"] label { color: #28282B !important; font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #28282B !important; font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 700; }

  /* Status badges */
  .badge-full  { background:#1a3a2a; color:#4ade80; border:1px solid #22c55e; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }
  .badge-half  { background:#3a2a0a; color:#fbbf24; border:1px solid #f59e0b; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }
  .badge-short { background:#2a1a2a; color:#c084fc; border:1px solid #a855f7; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }
  .badge-absent{ background:#3a1a1a; color:#f87171; border:1px solid #ef4444; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }
  .badge-present{background:#1a2a3a; color:#60a5fa; border:1px solid #3b82f6; border-radius:6px; padding:2px 10px; font-size:0.78rem; font-weight:600; }

 /* Header strip */
  .app-header {
    /* Using brown to a slightly darker brown for the gradient */
    background: linear-gradient(135deg, #8A9A5B 0%, #5a3f31 100%); 
    border-bottom: 2px solid #8A9A5B; /* Sage Green */
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 1rem;
  }
  .app-header h1 { margin:0; font-size:1.6rem; color:#f0f2ff; font-family:'Syne',sans-serif; font-weight:800; }
  .app-header .company { color:#e8eaf0; font-size:0.85rem; margin:0; }

  /* Row cards for attendance */
  .att-row {
    background: #12151f;
    border: 1px solid #1e2130;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    transition: border-color 0.2s;
  }
  .att-row:hover { border-color: #2563eb; }

  /* Section headers */
  .section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8eaf0;
    border-left: 3px solid #2563eb;
    padding-left: 0.75rem;
    margin: 1.5rem 0 1rem 0;
  }

  /* Data tables */
  .stDataFrame { border: 1px solid #1e2130; border-radius: 10px; overflow: hidden; }

  /* Buttons */
  .stButton > button {
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    border: 1px solid #2a2d3e;
    background: #1a1d2e;
    color: #e8eaf0;
    transition: all 0.15s;
  }
  .stButton > button:hover {
    background: #2563eb;
    border-color: #2563eb;
    color: #fff;
  }
  .stButton > button[kind="primary"] {
    background: #2563eb;
    border-color: #2563eb;
    color: #fff;
  }

  /* Inputs */
  /* Inputs - Outer Wrappers */
  div[data-testid="stTextInput"] div[data-baseweb="input"],
  div[data-testid="stSelectbox"] div[data-baseweb="select"],
  div[data-testid="stTimeInput"] div[data-baseweb="select"],
  div[data-testid="stTimeInput"] div[data-baseweb="input"] {
    background-color: #28282B !important;
    border: 1px solid #2a2d3e !important;
    border-radius: 8px !important;
  }

  /* Inputs - Inner Text Fields */
  div[data-testid="stTextInput"] input,
  div[data-testid="stTimeInput"] input,
  div[data-testid="stSelectbox"] input {
    color: #28282B !important;
    -webkit-text-fill-color: #28282B !important;
    background-color: transparent !important; /* This removes the blocking box */
    border: none !important;
  }

  /* Remove Streamlit branding */
  #MainMenu, footer, { visibility: hidden; }
  header { background: transparent !important; }

  /* Divider */
  hr { border-color: #1e2130; }

  /* Toast / success message */
  .stSuccess { background: #1a3a2a; border: 1px solid #22c55e; border-radius: 8px; }
  .stError   { background: #3a1a1a; border: 1px solid #ef4444; border-radius: 8px; }
  .stWarning { background: #3a2a0a; border: 1px solid #f59e0b; border-radius: 8px; }

  /* Expander */
  .streamlit-expanderHeader {
    background: #12151f !important;
    border: 1px solid #1e2130 !important;
    border-radius: 8px !important;
    color: #28282B !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #0f1117; border-radius: 10px; padding: 4px; }
  .stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 8px; color: #28282B;
    font-family: 'DM Sans', sans-serif; font-weight: 500;
  }
  .stTabs [aria-selected="true"] { background: #1a1d2e !important; color: #28282B !important; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def status_badge(status: str) -> str:
    mapping = {
        "Full Day": "badge-full",
        "Half Day": "badge-half",
        "Short Day": "badge-short",
        "Absent":   "badge-absent",
        "Present":  "badge-present",
    }
    cls = mapping.get(status, "badge-present")
    return f'<span class="{cls}">{status}</span>'


def time_str_to_obj(t: str):
    """Parse HH:MM → datetime.time or None."""
    if not t:
        return None
    try:
        return datetime.strptime(t, "%H:%M").time()
    except Exception:
        return None


# ─── Sidebar Navigation ───────────────────────────────────────────────────────

with st.sidebar:
    company_name = get_setting("company_name", "My Company")
    st.markdown(f"## 📋 AttendIQ")
    st.markdown(f"*{company_name}*")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📅  Daily Log", "👥  Employees", "📊  Monthly Report", "⚙️  Settings"],
    )
    st.markdown("---")
    st.caption("AttendIQ v1.0 · Built with Streamlit")


page_key = page.split("  ")[1]   # strip emoji prefix

# ─── Company header ──────────────────────────────────────────────────────────
company_name = get_setting("company_name", "My Company")
today_label  = date.today().strftime("%A, %B %d %Y")
st.markdown(
    f"""<div class="app-header">
      <div>
        <h1>📋 AttendIQ</h1>
        <p class="company">{company_name} &nbsp;·&nbsp; {today_label}</p>
      </div>
    </div>""",
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — DAILY LOG
# ════════════════════════════════════════════════════════════════════════════
if page_key == "Daily Log":
    
    # 1. Select Date (Moved outside columns to keep UI clean)
    log_date = st.date_input("Select Date", value=date.today(), key="log_date")
    log_date_str = log_date.strftime("%Y-%m-%d")
    employees    = get_all_employees()

    if not employees:
        st.info("No employees yet. Go to **Employees** to add your team.")
        st.stop()

    # Pre-load existing records for the chosen date
    saved_records = get_attendance_for_date(log_date_str)
    existing = {r["employee_id"]: r for r in saved_records}

    # --- STATE MANAGEMENT ---
    # Keep track of which date we are actively editing
    if "edit_date" not in st.session_state:
        st.session_state.edit_date = None

    # It is Edit Mode IF there are no records saved yet, OR if the user explicitly clicked edit for this date
    is_edit_mode = (not saved_records) or (st.session_state.edit_date == log_date_str)

    if is_edit_mode:
        # ---------------------------------------------------------
        # EDIT MODE: Display the Attendance Roster
        # ---------------------------------------------------------
        col_title, col_save = st.columns([2, 1])
        with col_title:
            st.markdown('<div class="section-title">Attendance Roster</div>', unsafe_allow_html=True)
        with col_save:
            st.markdown("<br>", unsafe_allow_html=True)
            save_all_btn = st.button("💾  Save All Records", type="primary", use_container_width=True)

        # Column headers
        hdr = st.columns([0.4, 2.5, 1.5, 1.2, 1.2, 1.5])
        for col, label in zip(hdr, ["✓", "Employee", "Role", "Arrival", "Departure", "Status"]):
            col.markdown(f"**{label}**")
        st.markdown('<hr style="margin:4px 0 10px 0">', unsafe_allow_html=True)

        rows_data = []
        
        # 1. Check if this is a brand new day being logged
        is_new_day = (len(saved_records) == 0)

        for emp in employees:
            eid    = emp["id"]
            rec    = existing.get(eid, {})
            key_p  = f"present_{eid}"
            key_a  = f"arrival_{eid}"
            key_d  = f"depart_{eid}"

            # 2. Default to PRESENT if it is a new day, otherwise keep whatever was saved
            default_present = bool(rec.get("present", is_new_day))

            default_arrival = time_str_to_obj(rec.get("arrival_time", ""))
            default_depart  = time_str_to_obj(rec.get("departure_time", ""))

            # 3. Fetch this employee's specifically assigned schedule!
            sched = get_schedule(eid) or {}
            def_in_t  = time_str_to_obj(sched.get("expected_in",  "09:00"))
            def_out_t = time_str_to_obj(sched.get("expected_out", "18:00"))

            # 4. If no time is saved yet, inject their expected schedule into the UI
            if key_a not in st.session_state:
                st.session_state[key_a] = default_arrival or def_in_t
            if key_d not in st.session_state:
                st.session_state[key_d] = default_depart or def_out_t

            cols = st.columns([0.4, 2.5, 1.5, 1.2, 1.2, 1.5])
            present  = cols[0].checkbox("", value=default_present, key=key_p, label_visibility="collapsed")
            cols[1].markdown(f"**{emp['name']}**")
            cols[2].markdown(f"<small style='color:#8b90a8'>{emp['role']}</small>", unsafe_allow_html=True)

            if present:
                # Times show up automatically, restricted to 15-min intervals (step=900)
                arrival  = cols[3].time_input("In",  key=key_a,  label_visibility="collapsed", step=900)
                departure= cols[4].time_input("Out", key=key_d,  label_visibility="collapsed", step=900)
                
                arr_str  = arrival.strftime("%H:%M")   if arrival    else ""
                dep_str  = departure.strftime("%H:%M") if departure else ""
                
                # 🛑 NEW LOGIC: Arrival cannot be after departure
                if arrival and departure and arrival > departure:
                    cols[5].markdown('<span class="badge-absent">⚠️ Invalid Time</span>', unsafe_allow_html=True)
                    # We pass "ERROR" to rows_data so the save button knows it failed
                    rows_data.append((eid, present, "ERROR", "ERROR"))
                    continue # Skip the normal status preview for this row
                
                # live status preview
                from database import _calc_status
                sch_in  = sched.get("expected_in", "09:00")
                sch_out = sched.get("expected_out","18:00")
                live_status = _calc_status(True, arr_str, dep_str, sch_in, sch_out)
                cols[5].markdown(status_badge(live_status), unsafe_allow_html=True)
            else:
                cols[3].markdown("<span style='color:#3a3d50'>—</span>", unsafe_allow_html=True)
                cols[4].markdown("<span style='color:#3a3d50'>—</span>", unsafe_allow_html=True)
                cols[5].markdown(status_badge("Absent"), unsafe_allow_html=True)
                arr_str = dep_str = ""

            rows_data.append((eid, present, arr_str, dep_str))

        st.markdown("---")

        st.markdown("---")

        if save_all_btn:
            # 🛑 NEW LOGIC: Check if any row triggered our "ERROR" flag above
            if any(arr == "ERROR" for _, _, arr, _ in rows_data):
                st.error("❌ Cannot save: One or more employees have an Arrival time set after their Departure time. Please fix the highlighted rows.")
            else:
                for eid, present, arr, dep in rows_data:
                    upsert_attendance(eid, log_date_str, present, arr or None, dep or None)
                
                # Clear edit mode to trigger View Mode
                st.session_state.edit_date = None
                st.rerun() # Forces page to refresh immediately

    else:
        # ---------------------------------------------------------
        # VIEW MODE: Display Results & Edit Button
        # ---------------------------------------------------------
        col_title, col_edit = st.columns([2, 1])
        with col_title:
            st.markdown('<div class="section-title">Today\'s Summary</div>', unsafe_allow_html=True)
        with col_edit:
            st.markdown("<br>", unsafe_allow_html=True)
            # Edit Button sets the session state to the current date and reloads
            if st.button("✏️ Edit Attendance", use_container_width=True):
                st.session_state.edit_date = log_date_str
                st.rerun()

        # Day Summary Strip
        c1, c2, c3, c4, c5 = st.columns(5)
        total   = len(saved_records)
        present_count = sum(1 for r in saved_records if r["present"])
        full    = sum(1 for r in saved_records if r["status"] == "Full Day")
        half    = sum(1 for r in saved_records if r["status"] in ("Half Day","Short Day"))
        absent  = sum(1 for r in saved_records if r["status"] == "Absent")
        
        c1.metric("Total Staff",   total)
        c2.metric("Present",       present_count)
        c3.metric("Full Day",      full)
        c4.metric("Half/Short",    half)
        c5.metric("Absent",        absent)
        
        st.markdown("---")
        
        # Display a clean, read-only table of the records below the summary
        st.markdown("**Logged Records:**")
        display_df = pd.DataFrame(saved_records)[["name", "role", "arrival_time", "departure_time", "status"]]
        display_df.columns = ["Employee", "Role", "Time In", "Time Out", "Final Status"]
        display_df.fillna("—", inplace=True) # Replace empty times with dashes
        st.dataframe(display_df, use_container_width=True, hide_index=True)
# ════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — EMPLOYEES
# ════════════════════════════════════════════════════════════════════════════
elif page_key == "Employees":
    tab_list, tab_add = st.tabs(["👥  Employee Directory", "➕  Add Employee"])

    # ── Directory ────────────────────────────────────────────────────────────
    with tab_list:
        employees = get_all_employees()
        if not employees:
            st.info("No employees yet. Use the **Add Employee** tab to get started.")
        else:
            st.markdown(f'<div class="section-title">{len(employees)} Active Employees</div>', unsafe_allow_html=True)
            for emp in employees:
                sched = get_schedule(emp["id"]) or {}
                work_days   = sched.get("work_days", "Mon–Fri")
                exp_in      = sched.get("expected_in", "09:00")
                exp_out     = sched.get("expected_out", "18:00")

                with st.expander(f"**{emp['name']}** — {emp['role']}", expanded=False):
                    col_info, col_sched, col_actions = st.columns([2, 2, 1])

                    with col_info:
                        st.markdown("**Employee Details**")
                        new_name = st.text_input("Name", value=emp["name"], key=f"name_{emp['id']}")
                        role_opts = PRESET_ROLES + ["Custom…"]
                        cur_role  = emp["role"]
                        if cur_role in PRESET_ROLES:
                            role_idx = PRESET_ROLES.index(cur_role)
                            sel_role = st.selectbox("Role", PRESET_ROLES, index=role_idx, key=f"role_sel_{emp['id']}")
                            new_role = sel_role
                        else:
                            st.selectbox("Role", PRESET_ROLES + ["Custom…"], index=len(PRESET_ROLES), key=f"role_sel_{emp['id']}")
                            new_role = st.text_input("Custom Role", value=cur_role, key=f"role_cust_{emp['id']}")

                        if st.button("Update Info", key=f"upd_{emp['id']}"):
                            update_employee(emp["id"], new_name, new_role)
                            st.success("Updated!")
                            st.rerun()

                    with col_sched:
                        st.markdown("**Schedule Settings**")
                        all_days   = DAYS_OF_WEEK
                        saved_days = sched.get("work_days", "Mon,Tue,Wed,Thu,Fri").split(",")
                        sel_days   = st.multiselect("Working Days", all_days, default=saved_days, key=f"days_{emp['id']}")
                        t_in  = st.time_input("Expected Clock-In",  value=time_str_to_obj(exp_in)  or datetime.strptime("09:00","%H:%M").time(), key=f"in_{emp['id']}",  step=900)
                        t_out = st.time_input("Expected Clock-Out", value=time_str_to_obj(exp_out) or datetime.strptime("18:00","%H:%M").time(), key=f"out_{emp['id']}", step=900)

                        if st.button("Save Schedule", key=f"sched_{emp['id']}"):
                            upsert_schedule(emp["id"], sel_days, t_in.strftime("%H:%M"), t_out.strftime("%H:%M"))
                            st.success("Schedule saved!")
                            st.rerun()

                    with col_actions:
                        st.markdown("**Actions**")
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️  Remove", key=f"del_{emp['id']}", help="Deactivate this employee"):
                            deactivate_employee(emp["id"])
                            st.warning(f"{emp['name']} deactivated.")
                            st.rerun()
                        if st.button("⚠️  Delete", key=f"hard_del_{emp['id']}", help="Permanently delete (cannot undo)"):
                            delete_employee(emp["id"])
                            st.error(f"{emp['name']} permanently deleted.")
                            st.rerun()

    # ── Add Employee ─────────────────────────────────────────────────────────
    with tab_add:
        st.markdown('<div class="section-title">New Employee</div>', unsafe_allow_html=True)

        with st.form("add_emp_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            new_name   = col1.text_input("Full Name *")
            role_sel   = col2.selectbox("Role *", PRESET_ROLES + ["Custom…"])

            custom_role = ""
            if role_sel == "Custom…":
                custom_role = st.text_input("Enter Custom Role *")

            st.markdown("**Default Schedule**")
            sc1, sc2, sc3 = st.columns(3)
            sel_days = sc1.multiselect("Working Days", DAYS_OF_WEEK, default=["Mon","Tue","Wed","Thu","Fri"])
            t_in     = sc2.time_input("Expected In",  value=datetime.strptime("09:00","%H:%M").time(), step=900)
            t_out    = sc3.time_input("Expected Out", value=datetime.strptime("18:00","%H:%M").time(), step=900)

            submitted = st.form_submit_button("➕  Add Employee", type="primary", use_container_width=True)
            if submitted:
                final_role = custom_role.strip() if role_sel == "Custom…" else role_sel
                if not new_name.strip():
                    st.error("Name is required.")
                elif not final_role:
                    st.error("Role is required.")
                else:
                    eid = add_employee(new_name, final_role)
                    upsert_schedule(eid, sel_days, t_in.strftime("%H:%M"), t_out.strftime("%H:%M"))
                    st.success(f"✅  **{new_name}** added successfully!")


# ════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — MONTHLY REPORT
# ════════════════════════════════════════════════════════════════════════════
elif page_key == "Monthly Report":
    st.markdown('<div class="section-title">Monthly Overview & Analytics</div>', unsafe_allow_html=True)

   # Month / Year selectors (Dropdown Style)
    col_m, col_y, _ = st.columns([2, 1, 3])
    
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    
    # Defaults based on today's date
    current_month_idx = date.today().month - 1
    current_year_idx = date.today().year - 2020
    
    # Render the dropdowns
    month_name = col_m.selectbox("Month", months, index=current_month_idx)
    year       = col_y.selectbox("Year", range(2020, 2031), index=current_year_idx)
    
    # Convert "January" back to 1, "February" to 2, etc. for your database
    month = months.index(month_name) + 1

    summary = get_monthly_summary(int(year), int(month))
    month_name = calendar.month_name[int(month)]

    if not summary:
        st.info("No data found for this period.")
        st.stop()

    # ── KPI strip ────────────────────────────────────────────────────────────
    total_full  = sum(r["full_days"]    for r in summary)
    total_half  = sum(r["half_days"]    for r in summary)
    total_short = sum(r["short_days"]   for r in summary)
    total_abs   = sum(r["total_absent"] for r in summary)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Full Days (total)",  total_full)
    k2.metric("Half Days (total)",  total_half)
    k3.metric("Short Days (total)", total_short)
    k4.metric("Absences (total)",   total_abs)

    st.markdown("---")

    # ── Summary Table ─────────────────────────────────────────────────────────
    df = pd.DataFrame(summary)
    df["attendance_rate"] = df.apply(
        lambda r: f"{(r['total_present'] / r['total_logged'] * 100):.0f}%" if r["total_logged"] > 0 else "N/A",
        axis=1,
    )
    display_df = df[["name","role","full_days","half_days","short_days","total_absent","attendance_rate"]].rename(columns={
        "name":            "Employee",
        "role":            "Role",
        "full_days":       "Full Days",
        "half_days":       "Half Days",
        "short_days":      "Short Days",
        "total_absent":    "Absences",
        "attendance_rate": "Attendance %",
    })
    st.markdown(f"#### {month_name} {int(year)} — Employee Summary")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    tab_bar, tab_detail = st.tabs(["📊 Attendance Bars", "📆 Daily Detail"])

    with tab_bar:
        if not df.empty:
            fig = go.Figure()
            fig.add_bar(name="Full Day",  x=df["name"], y=df["full_days"],  marker_color="#4ade80")
            fig.add_bar(name="Half Day",  x=df["name"], y=df["half_days"],  marker_color="#fbbf24")
            fig.add_bar(name="Short Day", x=df["name"], y=df["short_days"], marker_color="#c084fc")
            fig.add_bar(name="Absent",    x=df["name"], y=df["total_absent"],marker_color="#f87171")
            fig.update_layout(
                barmode="stack",
                title=f"Attendance Distribution — {month_name} {int(year)}",
                plot_bgcolor="#0f1117",
                paper_bgcolor="#0f1117",
                font_color="#e8eaf0",
                legend=dict(orientation="h", y=1.08),
                margin=dict(t=60, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

  
    with tab_detail:
        employees = get_all_employees()
        emp_names = {e["id"]: e["name"] for e in employees}
        sel_emp   = st.selectbox("Select Employee", employees, format_func=lambda e: e["name"])
        if sel_emp:
            daily = get_employee_daily_log(sel_emp["id"], int(year), int(month))
            if not daily:
                st.info("No records for this employee this month.")
            else:
                daily_df = pd.DataFrame(daily)[["log_date","present","arrival_time","departure_time","status"]]
                daily_df.columns = ["Date","Present","Arrival","Departure","Status"]
                daily_df["Present"] = daily_df["Present"].map({1:"✅", 0:"❌"})
                st.dataframe(daily_df, use_container_width=True, hide_index=True)

                # Trend line: cumulative present days
                daily_df["CumPresent"] = (daily_df["Present"] == "✅").cumsum()
                fig3 = px.line(
                    daily_df, x="Date", y="CumPresent",
                    title=f"Cumulative Present Days — {sel_emp['name']}",
                    markers=True,
                    color_discrete_sequence=["#60a5fa"],
                )
                fig3.update_layout(
                    plot_bgcolor="#0f1117",
                    paper_bgcolor="#0f1117",
                    font_color="#e8eaf0",
                )
                st.plotly_chart(fig3, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — SETTINGS
# ════════════════════════════════════════════════════════════════════════════
elif page_key == "Settings":
    st.markdown('<div class="section-title">Application Settings</div>', unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("#### 🏢  Company")
        company = st.text_input("Company Name", value=get_setting("company_name", "My Company"))

        st.markdown("#### 📅  Defaults")
        c1, c2 = st.columns(2)
        default_in  = c1.time_input("Default Clock-In",  value=time_str_to_obj(get_setting("default_in","09:00"))  or datetime.strptime("09:00","%H:%M").time(), step=900)
        default_out = c2.time_input("Default Clock-Out", value=time_str_to_obj(get_setting("default_out","18:00")) or datetime.strptime("18:00","%H:%M").time(), step=900)

        saved = st.form_submit_button("💾  Save Settings", type="primary")
        if saved:
            set_setting("company_name", company.strip())
            set_setting("default_in",  default_in.strftime("%H:%M"))
            set_setting("default_out", default_out.strftime("%H:%M"))
            st.success("Settings saved! Reload the page to see the updated company name.")

    st.markdown("---")
    st.markdown("#### ℹ️  About")
    st.markdown("""
    **AttendIQ** — Employee Attendance & Log Tracker  
    - Built with **Python · Streamlit · SQLite · Pandas · Plotly**  
    - All data is stored locally in `attendance.db`  
    - No internet connection required after install  

    **Attendance Logic:**
    | Status | Criteria |
    |---|---|
    | Full Day | ≥ 85% of scheduled hours worked |
    | Half Day | 45–84% of scheduled hours |
    | Short Day | < 45% of scheduled hours |
    | Absent | Checkbox not ticked |
    """)
