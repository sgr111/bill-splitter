---

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
| POST | /ai/agent/{group_id} | 5/min | Full LangGraph agent run |

---

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
# source venv/bin/activate  # Linux/Mac

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

---

## Split Types

| Type | How it works |
|------|-------------|
| `equal` | Total divided equally among all members |
| `unequal` | Caller provides exact amount for each user (must sum to total) |
| `percentage` | Caller provides percentage for each user (must sum to 100%) |

---

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
// Returns: { "category": "Food" }
```

**POST /ai/agent/{group_id}** — Full group analysis:
```json
// Returns: summary, reminders, and AI-generated report
```

---

## Security

- **JWT tokens** — Short-lived access tokens (30 min) + long-lived refresh tokens (7 days)
- **bcrypt hashing** — Passwords never stored in plain text
- **UUID primary keys** — Prevents enumeration/IDOR attacks
- **Per-endpoint authorization** — Every endpoint verifies group membership
- **IDOR test suite** — 8 dedicated security tests verify data isolation
- **Rate limiting** — AI endpoints protected with slowapi

---

## Author

**Saurabh Sagar** — Backend Developer & QA Automation Engineer
- GitHub: [@sgr111](https://github.com/sgr111)
- Email: sgrsourabh111@gmail.com