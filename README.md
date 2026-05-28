# 📋 AttendIQ — Employee Attendance & Log Tracker

A clean, high-efficiency attendance tracking application for administrators.  
Built with **Python · Streamlit · SQLite · Pandas · Plotly**.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Employee Directory** | Add, edit, deactivate or delete employees with roles |
| **Role Management** | Preset roles + custom text input |
| **Shift Schedules** | Per-employee working days, clock-in & clock-out times |
| **Fast Daily Log** | One-screen checkbox + time-picker roster |
| **Auto Status** | Full Day / Half Day / Short Day / Absent calculated automatically |
| **Monthly Reports** | Per-employee summaries with stacked bar, pie, and trend charts |
| **Persistent Storage** | SQLite — data never resets |

---

## 🚀 Quick Start

### 1. Clone / Download

```bash
# If you have git:
git clone <your-repo-url>
cd attendance_app

# Or just place the files in a folder:
#   attendance_app/
#   ├── app.py
#   ├── database.py
#   ├── requirements.txt
#   └── README.md
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## 📁 File Structure

```
attendance_app/
├── app.py           ← Streamlit UI (all pages & logic)
├── database.py      ← SQLite schema, queries, CRUD helpers
├── requirements.txt ← Python dependencies
├── attendance.db    ← Auto-created on first run (your data)
└── README.md
```

---

## 🗄️ Database Schema

```sql
settings        (key TEXT PK, value TEXT)
employees       (id, name, role, active, created_at)
schedules       (id, employee_id FK, work_days, expected_in, expected_out)
attendance      (id, employee_id FK, log_date, present, arrival_time,
                 departure_time, status, notes)
```

---

## 🔢 Attendance Status Logic

| Status | Condition |
|---|---|
| **Full Day** | Hours worked ≥ 85% of scheduled shift |
| **Half Day** | 45%–84% of scheduled shift |
| **Short Day** | < 45% of scheduled shift |
| **Absent** | Checkbox unchecked |
| **Present** | Checked but no times entered |

---

## 📖 How to Use

### First Run
1. Go to ⚙️ **Settings** → enter your company name.
2. Go to 👥 **Employees** → **Add Employee** tab → add your team members and set their schedules.

### Daily Attendance
1. Open 📅 **Daily Log**.
2. Select the date (defaults to today).
3. Check ✓ each present employee and enter arrival/departure times.
4. Status updates **live** as you type.
5. Hit **💾 Save All Records** once done.

### Monthly Reports
1. Go to 📊 **Monthly Report**.
2. Pick the year and month.
3. View the summary table and interactive charts.
4. Drill into any employee's daily log via the **Daily Detail** tab.

---

## 🔒 Data & Privacy

- All data is stored **locally** in `attendance.db` (SQLite).  
- No cloud, no external servers.  
- Back up the `.db` file to preserve your data.

---

## 📦 Backup & Export

To export monthly data, use the Streamlit built-in download — you can add CSV export by right-clicking the dataframe tables in the Monthly Report page and selecting **Download as CSV**.
