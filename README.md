# NORMA — AI Readiness Framework
NORMA is a tool for assessing dataset compliance with the AI Act (Art. 10). The app UI supports English and Italian (switchable at runtime); LLM prompts are always sent in English.

## Requirements

- Python 3.9+
- An [OpenRouter](https://openrouter.ai/) API key (used for the LLM-powered suggestions/comments; can also be entered from the app sidebar at runtime)

## Setup

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Provide your OpenRouter API key, either via a `.env` file in the project root:

   ```
   OPENROUTER_API_KEY=your-key-here
   ```

## Run the app

```bash
streamlit run app.py
```

This starts a local Streamlit server and opens the app in your browser (default: http://localhost:8501).