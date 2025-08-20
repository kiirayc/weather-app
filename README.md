# 🌦️ Weather App

A simple weather app built with **Flask, SQLite, SQLAlchemy, and JavaScript**.  
It lets you:

- Check **current weather** by city, landmark, or your geolocation 🌍
- View a **5-day forecast** 📅
- Create and save **historical weather queries** stored in a local SQLite database 📊
- Export queries as **JSON** or **CSV**

## ⚙️ Setup & Installation

1. **Clone this repository**

```bash
git clone https://github.com/kiirayc/weather-app.git
cd weather-app
```

2. **Set up a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a .env file in the project root:
```bash
OPENWEATHER_API_KEY=your_api_key_here
```

5. **Run the app**
```bash
python3 app.py
```

Now open your browser at:
👉 http://127.0.0.1:5000/

## 🖥️ Usage
- Enter a city name or landmark and click **Get Current** to see the weather now.
- Click **Get 5-Day** Forecast for upcoming weather.
- Use **Use My Location** to fetch weather based on your geolocation.
- Create **historical queries*** by entering a location and date range.
- View and export saved queries from the **Saved Queries** section.

## 📂 Project Structure
```php
.
├── app.py              # Flask entry point
├── services/           # Database models and services
├── static/             # JS, CSS
├── templates/          # HTML templates
├── weather.db          # Local SQLite DB (ignored in .gitignore)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 📜 License
This project is open-source under the MIT License.
