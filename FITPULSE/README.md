# ⚡ FITPULSE — Fitness Activity Visualization Platform

> **Tagline:** *Visualize Your Movement. Understand Your Progress.*

FITPULSE is a Streamlit fitness dashboard for viewing recorded activity, exploring daily/weekly/monthly trends, and tracking configurable goals. The app does not connect to a wearable or health API.

The sidebar contains four sections: **Overview**, **Analytics**, **Activity History**, and **Goals**. Previously saved activity records and goals continue to load.

---

## 📌 Project Overview

- **Target Audience:** Health-conscious individuals, fitness enthusiasts, and academic demonstrators.
- **Academic Context:** B.Tech Artificial Intelligence and Data Science project demonstration.
- **Architecture:** Streamlit components and Plotly charts, with the shared responsive design system in `assets/styles.css`. Components render their existing HTML through Streamlit; no separate JavaScript bundle or additional UI framework is required.
- **Theme:** Clean light surfaces with a soft blue-gray background, vivid blue for steps, warm orange for calories, and distinct teal and violet accents for other activity metrics.
- **Analytics:** Daily recorded values and weekly/monthly totals for steps, calories, distance, and active minutes.
- **Goals:** Persistent daily step and optional calorie goals, with progress based on the selected recorded date.
- **Data storage:** CSV import/manual entry are saved to `data/user_activity_records.csv`; goals are saved to `data/user_goals.json`. User rows replace bundled sample rows on matching dates without modifying the sample file.

---

## 🛠️ Technology Stack & Prerequisites

- **Language:** Python `3.10+` (Detected: Python 3.12.x)
- **UI Framework:** [Streamlit](https://streamlit.io/)
- **Visualizations:** [Plotly](https://plotly.com/python/)
- **Data Manipulation:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **Testing:** [pytest](https://docs.pytest.org/)

---

## 🚀 Getting Started

Follow these steps to set up and run FITPULSE on your machine.

### 1. Clone or Open the Workspace
Open your terminal (PowerShell or Bash) and navigate to the project root:
```bash
cd c:\Users\Dell\Desktop\FITPULSE
```

### 2. Create the Python Virtual Environment
Creating an isolated environment keeps dependencies clean and prevents conflicts with other system packages:

**On Windows (PowerShell):**
```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

**On Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies
Install all required libraries pinned in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

---

## 📊 Dataset Notice

- The dataset located in `data/sample_fitness_data.csv` contains **simulated sample records** for 7 consecutive days.
- **Disclaimer:** These values are realistic demonstration figures created for testing and interface verification. They do **not** represent real human medical measurements.
- The bundled dataset is the fallback starting dataset, not a live wearable feed. Previously saved records in `data/user_activity_records.csv` continue to load; the dashboard does not expose data-import or manual-entry controls.
- A daily calorie goal of `0` disables calorie-goal progress. Step goals are limited to 1,000–50,000.

---

## 🖥️ Running the Application

Launch the Streamlit dashboard server using the virtual environment's Streamlit binary:
```powershell
streamlit run app.py
```
Or directly via Python:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The application will automatically open in your default browser at:
`http://localhost:8501`

---

## 🧪 Running Automated Tests

To run the unit test suite verifying data structures and validation schemas:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

---

## 📁 Project Structure

```text
FITPULSE/
├── .streamlit/
│   └── config.toml             # Native light theme
├── app.py                      # Main application orchestrator
├── requirements.txt            # Dependency manifest
├── README.md                   # Project documentation & guide
├── assets/
│   └── styles.css               # Shared responsive dashboard styling
├── data/
│   └── sample_fitness_data.csv # 7-day demonstration activity dataset
├── components/
│   ├── __init__.py             # Visual UI components package
│   ├── header.py               # Dashboard section header
│   ├── hero.py                 # Welcome and activity summary
│   ├── metrics.py              # Selected-date actual activity cards
│   ├── analytics.py            # Daily, weekly, and monthly analytics
│   ├── history.py              # Calendar-selected history and comparisons
│   ├── goals.py                # Persistent daily goal tracking
│   ├── sidebar.py              # Core dashboard navigation
│   ├── comparison.py           # Activity-period comparisons
│   ├── theme.py                # Shared CSS and Plotly theme
│   └── charts.py               # Interactive Plotly visualizations
├── utils/
│   ├── data_processor.py       # Validation, aggregation, and calculations
│   └── storage.py              # Atomic local goal and activity persistence
└── tests/
    ├── test_calculations.py    # Data and aggregation tests
    └── test_storage.py         # Persistence and input validation tests
```
