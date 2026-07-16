from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate
from app.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3,
)

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


async def ask_expense_question(expense_data: str, question: str) -> str:
    response = await qa_chain.ainvoke({
        "expense_data": expense_data,
        "question": question,
    })
    return response.content


async def categorize_expense(description: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expense categorizer. 
Given an expense description, return ONLY one category from this exact list:
Food, Transport, Accommodation, Entertainment, Shopping, Other
Return only the category word, nothing else."""),
        ("human", "Expense description: {description}"),
    ])
    chain = prompt | llm
    response = await chain.ainvoke({"description": description})
    category = response.content.strip()
    valid = ["Food", "Transport", "Accommodation", "Entertainment", "Shopping", "Other"]
    return category if category in valid else "Other"