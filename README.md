# 🧠 AI Mining Copilot

An intelligent **AI-powered mining analytics and assistant platform** that helps monitor equipment status, analyze production trends, and provide real-time insights using AI and data visualization.

---

## 🚀 Features

- 📊 **Dynamic Dashboard**
  - Equipment status (Pie Chart)
  - Incidents trend (Bar Chart)
  - Production trend (Line Chart)
  - Auto-generates charts for new metrics dynamically

- 🧠 **AI Assistant**
  - Natural language Q&A on mining data
  - Multilingual support (English / Other languages)
  - Optional voice output

- 🗂️ **Data Management**
  - Connects to **MySQL** for structured data
  - RAG-based engine for intelligent context retrieval

- 🔐 **User Authentication**
  - JWT-based Login / Signup API
  - Secure token handling

- 🐳 **Dockerized Deployment**
  - One-click setup for **Backend**, **MySQL**, and **Frontend (Flutter Web)**

---

## 🏗️ Project Structure
```
AI-Mining-Copilot/
│
├── backend/ # Flask + LangChain + RAG + MySQL
│ ├── app.py
│ ├── models/
│ ├── database/
│ ├── utils/
│ ├── config.py
│ └── requirements.txt
│
├── flutter_app/ # Flutter Frontend (Web + Mobile)
│ ├── lib/
│ ├── assets/
│ └── pubspec.yaml
│
├── mysql/ # MySQL Container setup
│ ├── Dockerfile
│ └── init.sql
│
├── docker-compose.yml # Full-stack Docker setup
└── README.md
```


---

## ⚙️ Tech Stack
```

| Layer        | Technology Used                 |
|---------------|--------------------------------|
| **Frontend**  | Flutter (Material UI, fl_chart) |
| **Backend**   | Python Flask, LangChain, RAG   |
| **Database**  | MySQL                          |
| **Deployment**| Docker, Gunicorn               |
| **AI Engine** | OpenAI API / LangChain         |
```
---

## 🧩 Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/AI-Mining-Copilot.git
cd AI-Mining-Copilot
```
2️⃣ Configure Environment Variables
Create a .env file inside the backend directory:

```bash

MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=mining_db

OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_secret_key
```
3️⃣ Run with Docker (Recommended)
```bash

docker-compose up --build
```
This starts:

🐍 Flask backend → http://localhost:5000

🗄️ MySQL DB → localhost:3307

💻 Flutter Web app → http://localhost:8080

🧠 API Endpoints
Endpoint	Method	Description
```
/api/signup	POST	Register new user
/api/login	POST	User authentication
/api/dashboard	GET	Get analytics data
/api/query	POST	AI mining assistant query
```
🧰 Development Setup (Without Docker)
Backend
```bash

cd backend
pip install -r requirements.txt
python app.py
```
Flutter Frontend
```bash

cd flutter_app
flutter pub get
flutter run -d chrome
```
📈 Example Dashboard Visuals
🟢 Equipment Status → Pie Chart

🟠 Incidents Trend → Bar Chart

🔵 Production Trend → Line Chart

All charts auto-update based on backend data or user query.
