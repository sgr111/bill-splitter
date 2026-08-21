# Bill Splitter API 💸

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/pytest-58_passing-brightgreen?logo=pytest&logoColor=white)
![AI](https://img.shields.io/badge/AI-Groq_%2B_Gemini_Fallback-4285F4?logo=google&logoColor=white)
![Observability](https://img.shields.io/badge/Observability-llm--observability-8b5cf6)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

> A production-style Splitwise clone built with FastAPI, PostgreSQL, and AI-powered expense
> insights — with automatic multi-provider LLM fallback (Groq primary, Gemini on failure),
> full LLM call observability, and streaming responses, so the AI layer is resilient,
> traceable, and responsive.

## Introduction

- REST API for group expense splitting — JWT auth, group management, three split modes
  (equal/unequal/percentage), and a greedy debt-minimization algorithm for settle-up suggestions.
- Three AI features on top: natural-language Q&A over a group's real expense data (available
  both as a single JSON response and as a streamed response), LLM-based expense categorization,
  and a **LangGraph conditional-routing agent** that picks one of three paths (empty group / all
  settled / needs analysis) based on actual financial state — skipping the LLM call entirely
  when there's nothing to analyze.
- Every LLM call — Q&A, categorization, and both LLM-calling agent nodes — goes through a single
  shared, fallback-wired LLM instance (`app/ai/llm_provider.py`): **Groq is primary**, and
  LangChain's `with_fallbacks()` automatically retries against **Gemini** if Groq fails, with no
  manual error handling at any call site.
- Every one of those calls is also logged for observability via a shared
  [`llm-observability`](https://github.com/sgr111/llm-observability) package — project, feature,
  which provider actually answered, model, prompt version, latency, and success/failure, all
  persisted to a `llm_calls` table for later inspection.
- IDOR-hardened by design — UUID primary keys plus explicit per-endpoint membership/ownership
  checks — and covered by a dedicated 8-test security suite alongside the main test suite.
- 58 tests total (auth, CRUD, security/IDOR, AI endpoints, and a dedicated provider-fallback
  suite that forces Groq to fail and verifies Gemini serves the request instead), run
  automatically on every push via GitHub Actions.

---

## Architecture

```
                ┌──────────────────────────────────┐
                │         FastAPI Application       │
                │                                   │
     JWT Auth ──┤  routers/auth.py                  │
                │  routers/groups.py                │
                │  routers/expenses.py   ───────────┼── SQLAlchemy async ORM
                │  routers/splits.py                │        │
                │  routers/settlements.py           │        │
                │  routers/invites.py               │        ▼
                │  routers/ai.py         ───────┐   │  ┌─────────────┐
                │   /ai/ask (JSON)               │   │  │  PostgreSQL │
                │   /ai/ask/stream (streamed)     │   │  │   (Neon)    │
                │   /ai/categorize                │   │  │             │
                │   /ai/agent/{group_id}          │   │  │  users      │
                └───────────────────────────────┐ │   │  │  groups     │
                                                 │ │   │  │  expenses   │
                ┌─────────────────────────────────▼┘   │  │  splits     │
                │      AI Layer (LangChain/LangGraph)   │  │  settlements│
                │                                       │  │  invites    │
                │  langchain_qa.py                      │  │  llm_calls  │
                │   ├── ask_expense_question()            └─────────────┘
                │   ├── ask_expense_question_stream()
                │   └── categorize_expense()
                │
                │  langgraph_agent.py (3-route agent)
                │   ├── analyze_state ── routes on
                │   │     expenses + balances
                │   ├── empty_group ── no LLM call
                │   ├── all_clear ── 1 LLM call
                │   └── reminders → report ── 1 LLM call
                │             │
                │             ▼
                │  observability.py ── ObservabilityCallback
                │   attached to every LLM-calling node/chain,
                │   logs to llm_calls via llm-observability's
                │   track_llm_call() — dynamic provider
                │   detection (groq/gemini) per call, since
                │   fallback means either can answer any call
                │             │
                │             ▼
                │  llm_provider.py
                │   groq_llm ──with_fallbacks──▶ gemini_llm
                │   (primary)                    (automatic fallback)
                │             │
                │             ▼
                │   extract_text() ── normalizes response.content
                │   across providers (Gemini 3.x returns a list of
                │   content blocks, not a plain string)
                └────────────────────────────────────────┘

        config.py (pydantic-settings) ── single source of truth for
        SECRET_KEY / GROQ_API_KEY / GEMINI_API_KEY / DATABASE_URL
```

---

## A FastAPI Project Demonstrating

- **JWT Auth** — register, login, refresh tokens, bcrypt password hashing
- **IDOR Protection** — UUID primary keys + per-endpoint authorization checks, verified by an 8-test security suite
- **Soft Deletes** — groups/expenses use `is_active`/`is_deleted` flags instead of hard deletes
- **Greedy Debt Minimization** — settle-up suggestions computed with the minimum number of transactions, not naive pairwise settlement
- **LangChain** — chains wrapping every Groq/Gemini call (Q&A, categorization, streaming Q&A)
- **LangGraph** — a real conditional-routing agent, not just a linear chain — 3 dynamic paths based on computed group state
- **Multi-Provider Fallback** — `with_fallbacks()`-based automatic Groq→Gemini failover, shared across the whole AI layer via one `llm_provider.py` module
- **LLM Observability** — every LLM call logged (provider, model, latency, prompt version, success/failure) via a custom LangChain callback bridging into a shared `llm-observability` package, reused across projects
- **Streaming Responses** — `/ai/ask/stream` streams model output as it's generated, alongside the original JSON `/ai/ask` for clients that want a single response
- **APScheduler** — background reminders for dues unsettled longer than 3 days
- **Rate Limiting** — slowapi per-IP limits on all AI endpoints (tightest on the heaviest, multi-call agent endpoint)
- **Alembic** — versioned schema migrations
- **pytest** — 58-test suite: CRUD, auth, security/IDOR, AI endpoints, and a dedicated fallback suite that mocks Groq to force a real Gemini failover

---

## What This Project Does — At A Glance

### AI Capabilities

| Feature | Endpoint | Limit | What It Does |
|---------|----------|-------|-------------|
| **Expense Q&A** | `POST /ai/ask` | 10/min | Ask plain-English questions about a group's expenses — answered only from that group's real data |
| **Streaming Q&A** | `POST /ai/ask/stream` | 10/min | Same as above, but streams the answer token-by-token instead of waiting for the full response |
| **Auto-Categorization** | `POST /ai/categorize` | 20/min | Classifies an expense description into Food/Transport/Accommodation/Entertainment/Shopping/Other |
| **Conditional Agent** | `POST /ai/agent/{group_id}` | 5/min | LangGraph agent — routes to a no-LLM message, a short congratulations, or a full analysis + reminders, based on actual group state |

### Core Infrastructure

| Feature | Technology | What It Does |
|---------|-----------|---------------|
| **Auth** | python-jose + bcrypt | Short-lived access tokens (30 min) + refresh tokens (7 days) |
| **DB Layer** | SQLAlchemy 2.0 async | Async engine + sessions throughout, no blocking DB calls |
| **Migrations** | Alembic | Versioned, reversible schema changes |
| **Rate Limiting** | slowapi | Per-IP limits scoped tightest on the most expensive AI endpoint |
| **Scheduler** | APScheduler | Background job for overdue-settlement reminders |
| **LLM Fallback** | LangChain `with_fallbacks()` | Groq primary, Gemini automatic failover — one shared `llm` instance for the whole AI layer |
| **LLM Observability** | `llm-observability` + custom callback | Every LLM call logged to `llm_calls` — project, feature, provider, model, latency, prompt version, success/failure |
| **Streaming** | LangChain `.astream()` + FastAPI `StreamingResponse` | Token-by-token response delivery on `/ai/ask/stream`, fallback-aware |
| **Content Normalization** | `extract_text()` helper | Handles both plain-string (Groq) and list-of-blocks (Gemini 3.x) response formats transparently |
| **Transport Security** | SSL/TLS (DB) + platform-terminated HTTPS (API) | DB connection enforces `ssl=require`; production HTTPS handled by the deployment platform |

---

## Project Structure

```
bill-splitter/
├── app/
│   ├── ai/
│   │   ├── langchain_qa.py      # LangChain Q&A + categorization + streaming Q&A
│   │   ├── langgraph_agent.py   # LangGraph conditional routing agent
│   │   ├── llm_provider.py      # Shared Groq->Gemini fallback-wired LLM + extract_text()
│   │   └── observability.py     # ObservabilityCallback — bridges LangChain callbacks into llm-observability
│   ├── core/
│   │   ├── config.py            # pydantic-settings — single source of truth for secrets/env
│   │   ├── database.py          # SQLAlchemy async engine + session factory
│   │   └── dependencies.py      # get_db, get_current_user (FastAPI dependency injection)
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
│   └── main.py
├── scripts/
│   ├── check_gemini_key.py      # Standalone diagnostic tool for Gemini API key/model issues
│   └── check_groq.py            # Standalone diagnostic tool for Groq API key/model issues
│                                 # (run scripts via `python -m scripts.<name>`, not `python scripts/<name>.py`
│                                 #  — the -m form resolves `app.core.*` imports from the project root correctly)
├── tests/
│   ├── conftest.py              # function-scoped db_engine fixture (see Known Issues Fixed #4)
│   ├── test_auth.py             # 10 tests
│   ├── test_groups.py           # 7 tests
│   ├── test_expenses.py         # 7 tests
│   ├── test_splits.py           # 3 tests
│   ├── test_settlements.py      # 4 tests
│   ├── test_invites.py          # 7 tests
│   ├── test_security.py         # 8 IDOR tests
│   ├── test_ai.py               # 8 AI tests
│   └── test_llm_fallback.py     # 4 provider-fallback tests
├── alembic/
│   └── versions/                # includes the llm_calls table migration
├── .env.example
├── requirements.txt
└── README.md
```

---

<details>
<summary><h2 style="display:inline">API Endpoints</h2></summary>

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
| POST | /ai/ask | 10/min | Natural language expense query (JSON response) |
| POST | /ai/ask/stream | 10/min | Same as /ai/ask, but streamed |
| POST | /ai/categorize | 20/min | Auto-categorize expense |
| POST | /ai/agent/{group_id} | 5/min | LangGraph conditional routing agent |

</details>

---

## LangGraph Agent — 3 Dynamic Routes

```
START
  ↓
[analyze_state] — checks expenses + balances
  ↓
  ├── empty     → No expenses → Direct message (no LLM call)
  ├── all_clear → All settled → Short congratulations (1 LLM call)
  └── analyze   → Unsettled dues → reminders → Full analysis report (1 LLM call)
```

---

## AI Provider Fallback

All LLM calls — Q&A, categorization, and both LLM-calling agent nodes — go through one shared,
fallback-wired instance in `app/ai/llm_provider.py`:

```python
llm = groq_llm.with_fallbacks([gemini_llm])
```

**Groq is primary.** If a Groq call fails for any reason (outage, rate limit, timeout),
LangChain automatically retries the same request against **Gemini** — no manual try/except at
any call site, and no code needs to know which provider actually answered. Covered by
`tests/test_llm_fallback.py`, which mocks Groq to force a failure and asserts the endpoint
still returns a valid, Gemini-sourced response.

---

## Observability

Every LLM call — regardless of which endpoint triggers it or which provider ends up serving it
— is logged via a shared, cross-project [`llm-observability`](https://github.com/sgr111/llm-observability)
package. A custom `ObservabilityCallback` (`app/ai/observability.py`) bridges LangChain's
callback hooks into the package's `track_llm_call()` function, capturing:

- **project** + **feature** — which endpoint/call-site triggered this
- **provider** — detected dynamically per call (`groq` or `gemini`), since fallback means either
  provider can answer any given request
- **model**, **prompt_name**/**prompt_version**
- **latency_ms** — real, accurate timing (not the near-zero time it'd take to re-wrap an
  already-resolved value)
- **success**/**error_message**

All of this lands in a `llm_calls` table in the same Postgres database, queryable directly:

```sql
SELECT provider, feature, latency_ms, success, created_at
FROM llm_calls
ORDER BY created_at DESC
LIMIT 10;
```

A single Groq failure followed by a successful Gemini fallback naturally produces **two** log
rows for one logical request — one failed (`provider=groq`), one succeeded (`provider=gemini`)
— giving full visibility into when and how often the fallback actually triggers in practice.

---

## Streaming

`POST /ai/ask/stream` streams the model's answer as it's generated, instead of waiting for the
full response like `/ai/ask` does. Backed by LangChain's `.astream()` and FastAPI's
`StreamingResponse`. Observability requires no special handling here — the callback's
`on_llm_end` hook fires once the full stream has been consumed, so latency and logging behave
identically to the non-streaming path. The original `/ai/ask` JSON endpoint is unchanged and
still available for clients that just want a single response.

---

<details>
<summary><h2 style="display:inline">Known Issues Fixed</h2></summary>

Real bugs found and fixed during development, documented here rather than left as invisible
history — because "it works" and "here's what broke and how it was diagnosed" are different,
more useful claims.

### 1. Instance-level mocking crashed on Pydantic model cleanup
Mocking `groq_llm.ainvoke` directly (instance-level) crashed during test teardown with
`AttributeError: 'ChatGroq' object has no attribute 'ainvoke'`. Pydantic models override
`__delattr__` to only allow deleting declared fields — `ainvoke` is an inherited method, not a
field, so cleanup's `delattr()` call was rejected. **Fixed** by mocking the `ChatGroq` class
itself instead of the instance — classes aren't subject to Pydantic's instance-level restriction.

### 2. Gemini 3.x returns `.content` as a list of blocks, not a string
After switching to a current-generation Gemini model (older models were quietly deprecated for
new API keys — see #3), `response.content.strip()` started raising
`AttributeError: 'list' object has no attribute 'strip'`. Gemini's 3.x models return content as
`[{"type": "text", "text": "...", ...}]` instead of a plain string. **Fixed** via a shared
`extract_text()` helper in `llm_provider.py`, used at every call site that reads
`response.content`, so the code no longer assumes a specific provider's response shape.

### 3. `gemini-2.0-flash-lite` / `gemini-2.5-flash` blocked for new API keys
Both models returned `429 RESOURCE_EXHAUSTED` (`limit: 0`) or `404 NOT_FOUND ("no longer
available to new users")` on a freshly created key/project — Google has been retiring older
Gemini generations ahead of full shutdown. **Fixed** by switching to `gemini-3.5-flash-lite`,
confirmed working via an isolated standalone diagnostic script before wiring it back into the app.

### 4. DB engine lifecycle vs. pytest-asyncio's per-test event loops
The original test fixture created and disposed a brand-new SQLAlchemy engine on *every*
DB-touching request (not just per test) — a real performance bug, not just a test artifact. A
naive single-global-engine fix crashed with `RuntimeError: Event loop is closed` / `attached to
a different loop`, because pytest-asyncio gives each test function its own event loop by
default, and an engine's connection pool can't outlive the loop it was created on. **Fixed**
with a function-scoped `db_engine` fixture — one engine per test function (not per request, not
shared globally), tied to that test's own event loop and disposed in teardown. Local suite
runtime dropped from 30m33s to 21m26s with all 58 tests passing.

### 5. Gemini responses sometimes omit `model_name` in observability logs
`response.llm_output` doesn't always report `model_name` for Gemini responses (a
`langchain_google_genai` quirk — Groq's `ChatGroq` always populates it), leaving the `model`
column empty on some `llm_calls` rows. **Fixed** by capturing a model-name hint from LangChain's
`serialized` construction kwargs at call-start time and falling back to it whenever the
end-of-call response doesn't report one.

</details>

---

<details>
<summary><h2 style="display:inline">Tech Stack</h2></summary>

```
FastAPI                — API framework
PostgreSQL (Neon)      — Primary database
SQLAlchemy 2.0 async   — ORM, async throughout
Alembic                — Schema version control
JWT + bcrypt           — Authentication
slowapi                — Per-IP rate limiting on AI endpoints
APScheduler            — Background settlement reminders
LangChain               — Chains wrapping Q&A, categorization, streaming
LangGraph                — 3-route conditional agent
Groq (llama-3.1-8b)      — Primary LLM provider
Gemini (3.5-flash-lite)  — Automatic fallback provider
llm-observability        — Shared cross-project LLM call logging package
SSL/TLS                  — Enforced on the DB connection; HTTPS terminated at the platform edge in production
pytest                   — 58-test suite (CRUD, auth, security/IDOR, AI, fallback)
GitHub Actions            — CI on every push
```

</details>

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (or Neon free tier)
- Groq API key (free at console.groq.com)
- Gemini API key (free at aistudio.google.com)

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

## Security

- **JWT tokens** — Short-lived access tokens (30 min) + long-lived refresh tokens (7 days)
- **bcrypt hashing** — Passwords never stored in plain text
- **UUID primary keys** — Prevents enumeration/IDOR attacks
- **Per-endpoint authorization** — Every endpoint verifies group membership
- **IDOR test suite** — 8 dedicated security tests verify data isolation
- **Rate limiting** — AI endpoints protected with slowapi
- **Encrypted DB connection** — the Postgres connection to Neon enforces SSL/TLS
  (`connect_args={"ssl": "require"}` in `app/core/database.py`); the connection simply won't
  establish without it
- **HTTPS in production** — the deployment platform (Render) terminates TLS at its edge and
  auto-manages certificates; the app itself never handles certificates directly
- **Secrets management** — All secrets in .env, never committed to git; `alembic.ini` never
  hardcodes a connection string — it's loaded dynamically from `settings.DATABASE_URL` in
  `alembic/env.py`

---

## Author

**Saurabh Sagar** — Backend Developer & QA Automation Engineer
Lucknow, Uttar Pradesh, India

- GitHub: [@sgr111](https://github.com/sgr111)
- Email: sgrsourabh111@gmail.com