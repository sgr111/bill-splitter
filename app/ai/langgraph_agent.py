from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from app.config import settings

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=settings.GROQ_API_KEY,
    temperature=0.3,
)


class AgentState(TypedDict):
    group_id: str
    expenses: list
    balances: dict
    summary: str
    reminders: list
    final_report: str


def summarize_expenses(state: AgentState) -> AgentState:
    expenses = state["expenses"]
    if not expenses:
        state["summary"] = "No expenses found in this group."
        return state

    total = sum(e["total_amount"] for e in expenses)
    count = len(expenses)
    descriptions = [e["description"] for e in expenses]
    state["summary"] = (
        f"Group has {count} expenses totaling Rs.{total:.2f}. "
        f"Expenses: {', '.join(descriptions[:5])}{'...' if count > 5 else ''}."
    )
    return state


def calculate_reminders(state: AgentState) -> AgentState:
    balances = state["balances"]
    reminders = []
    for user_id, balance in balances.items():
        if balance < -10:
            reminders.append({
                "user_id": str(user_id),
                "amount_owed": round(abs(balance), 2),
                "message": f"Reminder: You owe Rs.{abs(balance):.2f} in this group.",
            })
    state["reminders"] = reminders
    return state


async def generate_final_report(state: AgentState) -> AgentState:
    balances_text = "\n".join(
        [f"User {uid}: Rs.{bal:.2f} ({'owes' if bal < 0 else 'is owed'})"
         for uid, bal in state["balances"].items()]
    )
    reminders_text = "\n".join(
        [r["message"] for r in state["reminders"]]
    ) or "No overdue reminders."

    prompt = f"""You are a financial assistant for a group expense app.

Group Summary: {state['summary']}

Net Balances:
{balances_text}

Pending Reminders:
{reminders_text}

Write a friendly, concise report (3-4 sentences) summarizing the group's financial status 
and what actions are needed to settle up."""

    response = await llm.ainvoke(prompt)
    state["final_report"] = response.content
    return state


def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("summarize", summarize_expenses)
    workflow.add_node("reminders", calculate_reminders)
    workflow.add_node("report", generate_final_report)

    workflow.set_entry_point("summarize")
    workflow.add_edge("summarize", "reminders")
    workflow.add_edge("reminders", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


agent = build_agent()


async def run_agent(group_id: str, expenses: list, balances: dict) -> dict:
    result = await agent.ainvoke({
        "group_id": group_id,
        "expenses": expenses,
        "balances": balances,
        "summary": "",
        "reminders": [],
        "final_report": "",
    })
    return result