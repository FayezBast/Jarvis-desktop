from langchain.tools import tool

@tool
def force_app_opening(app_name: str) -> str:
    """EMERGENCY TOOL: Forces app opening when agent tries to say 'I'll open' instead of using tools."""
    from tools.open_app import open_app
    result = open_app.invoke({'app_name': app_name})
    return f"🔧 FORCED EXECUTION: {result}"

@tool
def catch_lazy_responses(response_text: str) -> str:
    """Catches when agent tries to say it will do something instead of doing it."""
    banned_phrases = ["i'll open", "i will open", "let me open", "i'll send", "i will call"]
    
    if any(phrase in response_text.lower() for phrase in banned_phrases):
        return "❌ ERROR: You said you would do something instead of actually doing it! Use the appropriate tool NOW!"
    
    return "✅ Response is acceptable."
