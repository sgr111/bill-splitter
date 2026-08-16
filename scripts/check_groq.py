import asyncio
from langchain_groq import ChatGroq
from app.core.config import settings

async def test():
    llm = ChatGroq(model="openai/gpt-oss-20b", api_key=settings.GROQ_API_KEY)
    response = await llm.ainvoke("Say hello")
    print(response.content)

asyncio.run(test())