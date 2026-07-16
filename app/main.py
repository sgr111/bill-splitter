from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routers import auth, groups, expenses, splits, settlements, invites, ai
from app.services.reminder_service import check_unsettled_splits

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(check_unsettled_splits, "interval", hours=24, id="reminder_job")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Bill Splitter API",
    description="Splitwise-style bill splitting API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(splits.router)
app.include_router(settlements.router)
app.include_router(invites.router)
app.include_router(ai.router)


@app.get("/")
async def root():
    return {"message": "Bill Splitter API is running!"}