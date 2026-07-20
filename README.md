# Bill Splitter API 💸

A production-ready **Splitwise-style REST API** built with FastAPI, PostgreSQL, and AI features.
Users can create groups, add shared expenses, split bills (equal/unequal/percentage),
settle debts, and get AI-powered expense insights.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-blue)
![Tests](https://img.shields.io/badge/Tests-54%20Passing-brightgreen)
![AI](https://img.shields.io/badge/AI-Groq%20%2B%20LangChain-orange)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-green)

## Features

- **JWT Authentication** — Register, login, refresh tokens, bcrypt password hashing
- **Group Management** — Create groups, invite members via Base62 short links, leave groups
- **Expense Splitting** — 3 split modes: equal, unequal, percentage
- **Debt Minimization** — Greedy algorithm to suggest minimum settlements
- **AI Assistant** — Natural language expense queries powered by Groq + LangChain
- **Expense Categorization** — Auto-categorize expenses using LLM (Food, Transport, etc.)
- **LangGraph Agent** — Conditional routing agent with 3 dynamic paths based on group financial state
- **IDOR Protection** — UUID primary keys + per-endpoint authorization checks
- **Soft Deletes** — Groups and expenses use is_active/is_deleted flags
- **APScheduler** — Background reminders for unsettled dues older than 3 days
- **Rate Limiting** — slowapi per-IP limits on AI endpoints
- **54+ Tests** — Unit, integration, and security (IDOR) test suite
- **CI/CD** — GitHub Actions runs full test suite on every push

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Language | Python 3.11 |
| Database | PostgreSQL (Neon cloud) |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| AI | Groq (llama-3.1-8b) + LangChain + LangGraph |
| Scheduler | APScheduler |
| Rate Limiting | slowapi |
| Testing | pytest + pytest-asyncio + httpx |
| CI/CD | GitHub Actions |
| Deployment | Render (coming soon) |

## Project Structure

```
bill-splitter/
├── app/
│   ├── ai/
│   │   ├── langchain_qa.py      # LangChain Q&A + categorization
│   │   └── langgraph_agent.py   # LangGraph conditional routing agent
│   ├── models/
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── expense.py
│   │   ├── settlement.py
│   │   └── invite.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── groups.py
│   │   ├── expenses.py
│   │   ├── splits.py
│   │   ├── settlements.py
│   │   ├── invites.py
│   │   └── ai.py
│   ├── schemas/
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── split_service.py
│   │   ├── settle_service.py
│   │   ├── invite_service.py
│   │   └── reminder_service.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py             # 10 tests
│   ├── test_groups.py           # 7 tests
│   ├── test_expenses.py         # 7 tests
│   ├── test_splits.py           # 3 tests
│   ├── test_settlements.py      # 4 tests
│   ├── test_invites.py          # 7 tests
│   ├── test_security.py         # 8 IDOR tests
│   └── test_ai.py               # 8 AI tests
├── alembic/
├── .env.example
├── requirements.txt
└── README.md
```

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Register new user |
| POST | /auth/login | No | Login, get tokens |
| POST | /auth/refresh | No | Refresh access token |
| GET | /auth/me | Yes | Get current user |

### Groups
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /groups | Yes | Create group |
| GET | /groups | Yes | List my groups |
| GET | /groups/{id} | Yes | Get group details |
| PUT | /groups/{id} | Yes | Update group (admin only) |
| DELETE | /groups/{id} | Yes | Soft delete (admin only) |
| POST | /groups/{id}/leave | Yes | Leave group |

### Expenses
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /expenses | Yes | Add expense (auto-generates splits) |
| GET | /expenses/group/{id} | Yes | List group expenses |
| GET | /expenses/{id} | Yes | Get expense details |
| PUT | /expenses/{id} | Yes | Update expense |
| DELETE | /expenses/{id} | Yes | Soft delete (payer only) |

### Splits
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /splits/{expense_id} | Yes | View splits |
| POST | /splits/{id}/settle | Yes | Settle your split |

### Settlements
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /settlements | Yes | Record payment |
| GET | /settlements/{group_id} | Yes | List settlements |
| GET | /settle-up/{group_id} | Yes | Get minimum settlement suggestions |

### Invites
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /invites/{group_id} | Yes | Generate invite link |
| GET | /invites/{group_id} | Yes | List active invites |
| POST | /join/{short_code} | Yes | Join via invite link |
| DELETE | /invites/{id} | Yes | Deactivate invite link |

### AI (Rate Limited)
| Method | Endpoint | Limit | Description |
|--------|----------|-------|-------------|
| POST | /ai/ask | 10/min | Natural language expense query |
| POST | /ai/categorize | 20/min | Auto-categorize expense |
| POST | /ai/agent/{group_id} | 5/min | LangGraph conditional routing agent |

## LangGraph Agent — 3 Dynamic Routes

The AI agent analyzes group financial state and dynamically selects one of 3 paths:

```
START
  ↓
[analyze_state] — checks expenses + balances
  ↓
  ├── empty    → No expenses → Direct message (no LLM call)
  ├── all_clear → All settled → Short congratulations (1 LLM call)
  └── analyze  → Unsettled dues → Full analysis + reminders (1 LLM call)
```

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (or Neon free tier)
- Groq API key (free at console.groq.com)

### Local Setup

```bash
# Clone the repo
git clone https://github.com/sgr111/bill-splitter.git
cd bill-splitter

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
python -m pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your values

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GROQ_API_KEY=gsk_your_groq_key
GEMINI_API_KEY=your_gemini_key
BASE_URL=http://localhost:8000
INVITE_EXPIRE_DAYS=7
```

### Running Tests

```bash
pytest tests/ -v
```

## Split Types

| Type | How it works |
|------|-------------|
| `equal` | Total divided equally among all members |
| `unequal` | Caller provides exact amount for each user (must sum to total) |
| `percentage` | Caller provides percentage for each user (must sum to 100%) |

## AI Features

**POST /ai/ask** — Ask natural language questions:

```json
{
  "group_id": "uuid-here",
  "question": "Who owes the most in this group?"
}
```

**POST /ai/categorize** — Auto-categorize expenses:

```json
{
  "description": "Dinner at Barbeque Nation"
}
```

Returns: `{ "category": "Food" }`

**POST /ai/agent/{group_id}** — Conditional routing agent:

Returns: `summary`, `reminders`, and AI-generated `final_report`

## Security

- **JWT tokens** — Short-lived access tokens (30 min) + long-lived refresh tokens (7 days)
- **bcrypt hashing** — Passwords never stored in plain text
- **UUID primary keys** — Prevents enumeration/IDOR attacks
- **Per-endpoint authorization** — Every endpoint verifies group membership
- **IDOR test suite** — 8 dedicated security tests verify data isolation
- **Rate limiting** — AI endpoints protected with slowapi
- **Secrets management** — All secrets in .env, never committed to git

## Author

**Saurabh Sagar** — Backend Developer & QA Automation Engineer

- GitHub: [@sgr111](https://github.com/sgr111)
- Email: sgrsourabh111@gmail.com