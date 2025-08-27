from langchain.tools import tool

@tool
def debug_command(command: str) -> str:
    """Debug tool to log what command was received. Use this to verify speech recognition."""
    return f"🐛 DEBUG: Received command '{command}'. This confirms speech recognition is working."

@tool  
def list_all_tools() -> str:
    """List all available tools that Jarvis can use."""
    tools_list = """
🛠️ Available Tools:

📱 App Management:
- open_app: Open applications
- list_available_apps: Show available apps

📧 Communication:
- send_email_to_contact: Send emails to contacts
- call_contact: Make FaceTime calls
- make_phone_call: Make phone calls

📝 Productivity:
- take_note: Save notes
- read_recent_notes: Read saved notes
- add_calendar_event: Add calendar events
- check_calendar_events: Check calendar

🔍 Search & Info:
- duckduckgo_search_tool: Web search
- youtube_search: Search YouTube
- get_time: Get current time

📸 Media:
- take_screenshot: Capture screen
- read_text_from_latest_image: OCR text from images

🎮 Fun:
- matrix_mode: Enter Matrix mode
- arp_scan_terminal: Network scanning

Say "use [tool name]" to test any tool!
"""
    return tools_list
