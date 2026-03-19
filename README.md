# 🚀 DataPilot AI

**DataPilot AI** is an intelligent web scraping engine and comprehensive dashboard built to automate data extraction, visualize insights, and streamline background tasks.

![DataPilot AI](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Flask](https://img.shields.io/badge/Framework-Flask-black)

## ✨ Features

- **🛡️ Secure User Authentication:** Full login/signup system with protected, user-isolated data streams.
- **🌐 Real-Time Data Extraction:** Custom scraping engine (`BeautifulSoup`) tailored for public job boards like LinkedIn.
- **🔍 Advanced Scraping Filters:** Target data dynamically by Location, Company, Time Period, and Salary.
- **📈 Interactive Visualizations:** Built-in charts and graphs generated via `Pandas` and `Plotly` to analyze job market trends.
- **🤖 Background Automations:** Configure the engine to run hourly, daily, or weekly scrapes autonomously via `APScheduler`.
- **✉️ Automated Reporting:** Receive automatic SMTP email notifications with a raw CSV attachment whenever a task completes.
- **👑 Admin Operations:** A dedicated Admin Control Panel to manage active users and system-wide automations.
- **📱 Responsive UI:** A premium, modern interface leveraging Bootstrap 5, DataTables, and custom CSS styling.

## 🛠️ Technology Stack

- **Backend:** Python, Flask, SQLAlchemy (SQLite Engine)
- **Data Processing:** Pandas, urllib
- **Automations:** APScheduler
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, DataTables
- **Visualizations:** Plotly Python
- **Notifications:** smtplib, Python EmailMessage

## ⚙️ Installation & Setup

Follow these steps to run DataPilot AI locally:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/datapilot-ai.git
   cd datapilot-ai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, manually install: `flask flask_sqlalchemy apscheduler beautifulsoup4 pandas plotly`)*

4. **Environment Variables (Optional but recommended for Email features):**
   ```bash
   export MAIL_SERVER="smtp.gmail.com"
   export MAIL_PORT=587
   export MAIL_USERNAME="your-email@gmail.com"
   export MAIL_PASSWORD="your-app-password"
   export MAIL_DEFAULT_SENDER="noreply@datapilotai.com"
   ```

5. **Run the Application:**
   ```bash
   python app.py
   ```

6. **Access the Dashboard:**
   Open your browser and navigate to `http://127.0.0.1:5000/`.

## 📁 Project Structure

- `app.py`: Main Flask application router.
- `models.py`: SQLAlchemy database models representing Users, Tasks, Jobs, and Schedules.
- `scrapers/`: Core web scraping logic and custom web drivers.
- `automation/scheduler.py`: The background autonomous engine handling tasks.
- `processing/`: Data cleanup and transformation logic using Pandas.
- `visualization/`: Chart generators building JSON specifications for Plotly.
- `templates/`: HTML interface templates and Admin panels.
- `email_service.py`: Automated report generator and SMTP handler.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License
This project is [MIT](LICENSE) licensed.
