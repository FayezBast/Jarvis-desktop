import os
import datetime
from langchain.tools import tool

@tool
def take_note(content: str, title: str = "") -> str:
    """Take a quick note and save it to a file. Provide content and optional title."""
    try:
        # Create notes directory if it doesn't exist
        notes_dir = os.path.expanduser("~/Documents/Jarvis_Notes")
        os.makedirs(notes_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if title:
            filename = f"{timestamp}_{title.replace(' ', '_')}.txt"
        else:
            filename = f"{timestamp}_note.txt"
        
        filepath = os.path.join(notes_dir, filename)
        
        # Write the note
        with open(filepath, 'w') as f:
            if title:
                f.write(f"Title: {title}\\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"\\nContent:\\n{content}\\n")
        
        return f"Note saved to {filepath}"
    except Exception as e:
        return f"Failed to save note: {str(e)}"

@tool
def read_recent_notes(count: int = 5) -> str:
    """Read the most recent notes. Specify how many notes to read (default 5)."""
    try:
        notes_dir = os.path.expanduser("~/Documents/Jarvis_Notes")
        if not os.path.exists(notes_dir):
            return "No notes directory found. Take a note first!"
        
        # Get all note files sorted by modification time
        notes = []
        for file in os.listdir(notes_dir):
            if file.endswith('.txt'):
                filepath = os.path.join(notes_dir, file)
                notes.append((filepath, os.path.getmtime(filepath)))
        
        notes.sort(key=lambda x: x[1], reverse=True)
        
        if not notes:
            return "No notes found."
        
        result = f"Recent {min(count, len(notes))} notes:\\n\\n"
        for i, (filepath, _) in enumerate(notes[:count]):
            filename = os.path.basename(filepath)
            with open(filepath, 'r') as f:
                content = f.read()[:200]  # First 200 chars
                if len(f.read()) > 200:
                    content += "..."
            result += f"{i+1}. {filename}:\\n{content}\\n\\n"
        
        return result
    except Exception as e:
        return f"Failed to read notes: {str(e)}"
