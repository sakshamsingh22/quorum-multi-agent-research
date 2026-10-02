# Quorum: Multi-Agent AI Research Assistant

Quorum is a multi-agent AI research pipeline powered by LangChain and LangGraph, with a modern Streamlit frontend. It coordinates a team of four specialized AI agents to automate end-to-end web research, analysis, and report generation.

## Agent Team

1. **Search Agent**: Finds recent, reliable sources on the web using the Tavily API.
2. **Reader Agent**: Picks the most relevant source and extracts its detailed content.
3. **Writer Agent**: Drafts a comprehensive research report using all gathered information.
4. **Critic Agent**: Reviews the draft and provides constructive feedback.

## Setup Instructions

1. Clone the repository
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY=your_key_here
   TAVILY_API_KEY=your_key_here
   MISTRAL_API_KEY=your_key_here
   ```

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
```
