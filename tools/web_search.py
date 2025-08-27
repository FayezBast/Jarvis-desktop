
# Simple, reliable web search tool using DuckDuckGo (ddgs)

from langchain.tools import tool
from ddgs import DDGS

import subprocess
from urllib.parse import quote_plus

@tool
def web_search(query: str) -> str:
    """
    Open Safari and search Google for the requested information.
    """
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        # AppleScript to open Safari and search
        script = f'''osascript -e 'tell application "Safari"
            activate
            open location "{search_url}"
        end tell'
        '''
        subprocess.run(script, shell=True)
        return f"Opened Safari and searched for: {query}"
    except Exception as e:
        return f"Failed to open Safari: {str(e)}"
