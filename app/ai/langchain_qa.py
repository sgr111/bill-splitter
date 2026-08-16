from typing import AsyncGenerator

from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm_provider import llm, extract_text
from app.ai.observability import ObservabilityCallback

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful expense assistant for a bill splitting app.
You will be given group expense data and must answer the user's question accurately.
Always be concise and friendly. Use the data provided only — do not make up numbers.
If data is insufficient, say so clearly."""),
    ("human", """Group Expense Data:
{expense_data}

User Question: {question}

Answer:"""),
])

qa_chain = qa_prompt | llm


async def ask_expense_question(expense_data: str, question: str, db_session=None) -> str:
    obs_cb = ObservabilityCallback(
        feature="ask_expense_question",
        prompt_name="expense_qa",
        prompt_version="v1",
        db_session=db_session,
    )
    response = await qa_chain.ainvoke(
        {
            "expense_data": expense_data,
            "question": question,
        },
        config={"callbacks": [obs_cb]},
    )
    return extract_text(response.content)


async def ask_expense_question_stream(
    expense_data: str, question: str, db_session=None
) -> AsyncGenerator[str, None]:
    """
    Streaming variant of ask_expense_question — yields text chunks as the
    model generates them instead of waiting for the full response.

    Observability still works transparently here: ObservabilityCallback's
    on_llm_end fires once the FULL stream has been consumed (with the
    complete aggregated response), so latency covers the whole stream and
    logging behaves identically to the non-streaming path — no changes
    needed in observability.py for this to work.

    Fallback behavior: with_fallbacks() supports streaming too. If Groq
    fails before yielding any chunk (the common case — auth/rate-limit
    errors happen immediately, not mid-stream), it transparently retries
    the stream against Gemini. If Groq fails PARTWAY through an
    already-started stream (rare), any chunks already yielded to the
    caller can't be un-sent — this is an inherent tradeoff of streaming
    with fallback, not something this function can fully guard against.
    """
    obs_cb = ObservabilityCallback(
        feature="ask_expense_question_stream",
        prompt_name="expense_qa",
        prompt_version="v1",
        db_session=db_session,
    )
    async for chunk in qa_chain.astream(
        {
            "expense_data": expense_data,
            "question": question,
        },
        config={"callbacks": [obs_cb]},
    ):
        text = extract_text(chunk.content)
        if text:
            yield text


async def categorize_expense(description: str, db_session=None) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expense categorizer.
Given an expense description, return ONLY one category from this exact list:
Food, Transport, Accommodation, Entertainment, Shopping, Other
Return only the category word, nothing else."""),
        ("human", "Expense description: {description}"),
    ])
    chain = prompt | llm

    obs_cb = ObservabilityCallback(
        feature="categorize_expense",
        prompt_name="expense_categorizer",
        prompt_version="v1",
        db_session=db_session,
    )
    response = await chain.ainvoke(
        {"description": description},
        config={"callbacks": [obs_cb]},
    )
    category = extract_text(response.content).strip()
    valid = ["Food", "Transport", "Accommodation", "Entertainment", "Shopping", "Other"]
    return category if category in valid else "Other"
