# InterSpeed — Internet Speed Monitor & Billing System

## Overview
InterSpeed is a professional-grade Windows desktop application for monitoring internet speed, tracking network data usage, and managing your ISP subscription billing.

## Features
- **Live Network Monitoring** — Real-time upload/download speed via psutil
- **Speed Tests** — Actual internet speed testing with history
- **Analytics** — Average, min, max speeds with interactive charts
- **Data Usage** — Hourly/daily/monthly tracking
- **Billing** — ₹707/month fixed subscription with cost breakdowns
- **PDF Invoice Generator** — Professional invoices via ReportLab
- **History** — Full records of all tests and sessions
- **Settings** — Fully configurable

## Requirements
- Python 3.9+
  **PySide6>=6.5.0
    psutil>=5.9.0
    speedtest-cli>=2.1.3
    matplotlib>=3.7.0
    pandas>=2.0.0
    sqlalchemy>=2.0.0
    reportlab>=4.0.0
    openpyxl>=3.1.0
    requests>=2.31.0

- Windows 10/11

## Quick Start

### 1. Setup (First Time)
```
Double-click setup.bat
```

### 2. Run Application
```
Double-click run.bat
```

## Default Plan
- **Plan:** Internet 70 Mbps
- **Monthly Price:** ₹707
- **Billing Cycle:** Monthly

## Project Structure
```
INTERSPEED/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── setup.bat            # Environment setup
├── run.bat              # Launch script
├── database/
│   ├── models.py        # SQLAlchemy ORM models
│   └── database.py      # DB connection & initialization
├── core/
│   ├── monitor.py       # Real-time network monitoring
│   ├── speedtest_engine.py  # Speed test logic
│   ├── analytics.py     # Analytics calculations
│   ├── billing.py       # Billing calculations
│   └── usage_tracker.py # Data usage tracking
├── ui/
│   ├── dashboard.py     # Dashboard page
│   ├── monitoring.py    # Live monitoring page
│   ├── speedtest.py     # Speed test page
│   ├── analytics.py     # Analytics page
│   ├── usage.py         # Data usage page
│   ├── billing.py       # Billing page
│   ├── history.py       # History page
│   ├── settings.py      # Settings page
│   ├── components.py    # Reusable UI components
│   └── styles.py        # Stylesheet definitions
├── services/
│   ├── invoice_generator.py  # PDF invoice creation
│   └── export_service.py     # CSV/Excel export
└── data/
    └── interspeed.db    # SQLite database
```

## Notes
- Network counters reflect all traffic on the machine, not just browser traffic.
- Speed test results represent actual internet bandwidth.
- Live monitoring speeds differ from speed test results — they show current transfer rates.
- Monthly billing is a fixed ₹707; data usage does not change the bill.
