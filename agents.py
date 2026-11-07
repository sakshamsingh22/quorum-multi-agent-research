"""LLM and prompt-chain construction for Quorum.

Model clients are created only when a live operation is invoked, allowing
unit tests and documentation tooling to import the application without API keys.
"""
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_mistralai import ChatMistralAI

from tools import web_search, scrape_url

load_dotenv()


def get_llm():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not configured. Add it to .env.")
    return ChatMistralAI(model="open-mistral-nemo", temperature=0, api_key=api_key)


def build_search_agent():
    return create_agent(model=get_llm(), tools=[web_search])


def build_reader_agent():
    return create_agent(model=get_llm(), tools=[scrape_url])


writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])


def _run_writer(inputs):
    return (writer_prompt | get_llm() | StrOutputParser()).invoke(inputs)


def _run_critic(inputs):
    return (critic_prompt | get_llm() | StrOutputParser()).invoke(inputs)


# Keep the Runnable interface used by both the CLI pipeline and Streamlit UI.
writer_chain = RunnableLambda(_run_writer)
critic_chain = RunnableLambda(_run_critic)
