from langchain.tools import tool
import subprocess
import platform

@tool("matrix_mode", return_direct=True)
def matrix_mode() -> str:
    """
    Opens a new terminal window and runs the cmatrix command to enter 'Matrix Mode'.
    Use this tool when the user says something like:
    - "Enter matrix mode"
    - "Activate matrix mode"
    - "Go into matrix mode"
    """
    system = platform.system()

    try:
        if system == "Linux":
            # Replace 'gnome-terminal' if you're using xterm, konsole, etc.
            subprocess.Popen(["gnome-terminal", "--", "cmatrix"])
            return "Matrix mode activated! Enjoy the rain neo."

        elif system == "Darwin":
            # macOS version
            subprocess.Popen([
                "osascript", "-e",
                'tell application "Terminal" to do script "cmatrix"',
                "-e", 'tell application "Terminal" to activate'
            ])
            return "Matrix mode has been activated sir!"

        else:
            return f"Matrix mode is not supported on {system}."
    except Exception as e:
        return f"Failed to activate matrix mode: {str(e)}"
