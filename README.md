# 🌿 ArogyaAI — India's AI Health Companion

> **Bharat ka apna doctor** — AI-powered, multilingual, clinically intelligent health SaaS

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase)](https://supabase.com/)
[![Groq](https://img.shields.io/badge/AI-Groq_70B-F55036)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ What is ArogyaAI?

ArogyaAI is a **production-grade, billlion-dollar-tier health-tech SaaS** that gives every Indian access to instant, personalized medical guidance — in Hindi, Gujarati, Tamil, Telugu, Bengali, Marathi, Kannada, and English.

Built on **Groq's LLaMA-3.3 70B** with a multi-model fallback cascade, ArogyaAI delivers:

- 🤖 **AI Doctor** — Clinical-grade chat with emergency detection, symptom analysis, and risk scoring
- 💊 **Drug Interaction Checker** — FDA-data powered drug safety
- 🥗 **Nutrition Coach** — Personalized Indian diet plans
- 🏋️ **Fitness Coach** — Home workout programming
- 🧠 **Mindfulness Therapist** — CBT/ACT-backed mental wellness
- 🧬 **Genetics Counselor** — Nutrigenomics and precision medicine
- 📊 **Health Dashboard** — Score tracking, streak system, family management
- 🔐 **Secure Auth** — JWT + Refresh token system
- 💳 **Payments** — Razorpay Pro/Elite subscriptions

---

## 🏗️ Architecture

```
ArogyaAI/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # Application entry point
│   ├── app/
│   │   ├── api/                # REST API endpoints
│   │   │   ├── auth.py         # Signup, login, refresh tokens
│   │   │   ├── chat.py         # Main AI doctor chat
│   │   │   ├── premium.py      # Premium modules (nutrition, fitness, etc.)
│   │   │   ├── billing.py      # Razorpay subscription management
│   │   │   ├── user.py         # Profile, history, streaks
│   │   │   ├── admin.py        # Admin panel API
│   │   │   ├── analytics.py    # Privacy-first analytics
│   │   │   ├── health.py       # Health score & reports
│   │   │   ├── drugs.py        # Drug interaction checker
│   │   │   ├── voice.py        # Voice transcription (Whisper)
│   │   │   └── feedback.py     # User feedback
│   │   ├── core/
│   │   │   ├── config.py       # All settings from environment
│   │   │   ├── database.py     # Supabase service layer (with dev fallback)
│   │   │   ├── security.py     # JWT auth, bcrypt passwords
│   │   │   ├── middleware.py   # Request logging + observability
│   │   │   └── security_headers.py  # OWASP headers middleware
│   │   ├── services/
│   │   │   ├── ai_service.py   # Groq AI with multi-model fallback cascade
│   │   │   ├── health_engine.py     # Clinical scoring + emergency detection
│   │   │   ├── symptom_engine.py    # NLP symptom extraction
│   │   │   ├── risk_engine.py       # Risk stratification
│   │   │   ├── memory_service.py    # LRU response cache + conversation memory
│   │   │   ├── personalization_engine.py  # User context builder
│   │   │   ├── drug_checker.py      # FDA drug lookup
│   │   │   └── medical_service.py   # Wikipedia medical context
│   │   └── schemas/
│   │       └── __init__.py     # All Pydantic request/response models
│   ├── tests/                  # pytest test suite (93 tests, 0 failures)
│   └── requirements.txt
├── frontend/                   # Vanilla HTML/CSS/JS frontend
│   ├── index.html              # Landing page
│   ├── pages/                  # 17 app pages
│   ├── css/                    # Design system stylesheets
│   ├── js/
│   │   └── app.js             # Shared utilities (Auth, API, Toast, Analytics)
│   └── assets/                 # Icons, images
├── supabase_schema.sql         # Full database schema + migrations
├── Dockerfile                  # Production Docker container
├── docker-compose.yml          # Local development stack
├── pytest.ini                  # Test configuration
└── .env.example                # Environment variable template
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- [Groq API key](https://console.groq.com/) (free tier available)
- (Optional) [Supabase](https://supabase.com) project for persistence

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/arogyaai.git
cd arogyaai

# Create virtual environment
python -m venv backend/.venv
backend/.venv/Scripts/activate        # Windows
# source backend/.venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your GROQ_API_KEY at minimum
```

**Minimum required for local dev (no database needed):**
```env
GROQ_API_KEY=gsk_your_groq_key_here
JWT_SECRET=any-random-64-char-string-here-change-in-production
```

### 3. Run the Server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open [http://localhost:8000](http://localhost:8000) 🎉

---

## 🧪 Running Tests

```bash
# From project root (pytest.ini configures paths automatically)
backend/.venv/Scripts/python.exe -m pytest -v

# Output: 93 passed, 1 skipped ✅
```

---

## 🗄️ Database Setup (Optional — Supabase)

Without Supabase, the app runs fully in-memory (perfect for dev/demo). For production persistence:

1. Create a [Supabase](https://supabase.com) project
2. Run `supabase_schema.sql` in the SQL editor
3. Add `SUPABASE_URL` and `SUPABASE_KEY` to your `.env`

---

## 💳 Payment Setup (Razorpay)

Without Razorpay keys, billing runs in dev mock mode (no real payments). For production:

1. Create a [Razorpay](https://razorpay.com) account
2. Get your `Key ID` and `Key Secret` from the dashboard
3. Add to `.env`:
   ```env
   RAZORPAY_KEY_ID=rzp_live_xxxxx
   RAZORPAY_SECRET=your_secret
   ```

---

## 🌍 API Documentation

Interactive API docs available at: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Login, get tokens |
| POST | `/api/auth/refresh` | Renew access token |
| POST | `/api/chat/` | Main AI doctor chat |
| POST | `/api/premium/{module}/chat` | Premium specialist chat |
| GET | `/api/billing/plans` | Available plans |
| POST | `/api/billing/create-order` | Create payment order |
| POST | `/api/billing/verify-payment` | Verify & upgrade |
| GET | `/api/user/history` | Chat history |
| GET | `/api/user/streak` | Health streak |
| GET | `/health` | System health check |

---

## 🔐 Environment Variables

See [backend/.env.example](backend/.env.example) for the full list.

**Critical variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Groq cloud API key |
| `JWT_SECRET` | ✅ Yes | Min 64 chars, random string |
| `SUPABASE_URL` | ⚠️ Prod | Supabase project URL |
| `SUPABASE_KEY` | ⚠️ Prod | Supabase anon key |
| `RAZORPAY_KEY_ID` | 💳 Billing | Razorpay key ID |
| `RAZORPAY_SECRET` | 💳 Billing | Razorpay secret |
| `ADMIN_SECRET` | 🛡️ Admin | Admin panel access key |
| `APP_ENV` | ✅ Yes | `development` or `production` |

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t arogyaai .
docker run -p 8000:8000 --env-file backend/.env arogyaai
```

---

## ☁️ Cloud Deployment

### Render (Recommended — Easiest)

1. Connect your GitHub repository to [Render](https://render.com)
2. **New Web Service** → Python → Build command: `pip install -r backend/requirements.txt`
3. Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from `.env.example`

### Railway

```bash
railway login
railway new
railway up
railway variables set GROQ_API_KEY=gsk_xxx JWT_SECRET=xxx ...
```

### AWS / GCP / Azure

Use the provided `Dockerfile` with any container service (ECS, Cloud Run, ACI).

---

## 📊 Admin Panel

Access the admin panel at `/admin` with your `ADMIN_SECRET`:

- 📈 Real-time user and query stats
- 🚨 Error log ring buffer (last 100 errors)
- 👥 User management with pagination
- 📉 Conversion funnel analytics

---

## 🛡️ Security Features

- **OWASP Headers**: X-Frame-Options, XSS Protection, HSTS, CSP
- **JWT + Refresh Tokens**: 7-day access + 30-day refresh
- **bcrypt + SHA-256**: Safe password hashing (prevents the 72-byte truncation attack)
- **Input Validation**: Pydantic v2 with strict type checking
- **Rate Limiting**: Per-IP and per-user query limits
- **Admin Secret**: Header-based admin API protection
- **CORS**: Never wildcard in production
- **SQL Injection**: Supabase parameterized queries only

---

## 🤝 Supported Languages

English · हिन्दी · ગુજરાતી · मराठी · தமிழ் · తెలుగు · বাংলা · ಕನ್ನಡ

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Built with Love for Bharat

*ArogyaAI is not a substitute for professional medical advice. Always consult a qualified doctor for medical decisions. In emergencies, call 108.*
