from langchain.tools import tool
import subprocess
import json
import os

@tool("call_contact", return_direct=True)
def call_contact(contact_name: str) -> str:
    """
    Make a FaceTime call to a contact by name. Use this when the user says:
    - "Call mom"
    - "FaceTime dad" 
    - "Video call john"
    - "Call mama"
    """
    try:
        # First check our custom contacts.json
        contacts_file = os.path.join(os.path.dirname(__file__), 'contacts.json')
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
            
            contact_name_lower = contact_name.lower()
            
            # Look for exact or partial match in our contacts
            for name, email in contacts.items():
                if name.lower() == contact_name_lower or contact_name_lower in name.lower():
                    return facetime_call_simple(email, name)
        
        # If not found in our contacts, try with the name directly
        return facetime_call_simple(contact_name, contact_name)
        
    except Exception as e:
        return f"Failed to initiate call: {str(e)}"

def facetime_call_simple(contact_info: str, display_name: str) -> str:
    """Make a FaceTime call using the simple facetime:// URL scheme"""
    try:
        # Method 1: Use facetime:// URL scheme (most reliable)
        facetime_url = f"facetime://{contact_info}"
        
        # Open the FaceTime URL
        subprocess.run(["open", facetime_url], check=True)
        
        return f"Opening FaceTime to call {display_name} ({contact_info})..."
        
    except subprocess.CalledProcessError:
        # Fallback method: Use AppleScript but much simpler
        return facetime_call_applescript(contact_info, display_name)

def facetime_call_applescript(contact_info: str, display_name: str) -> str:
    """Fallback method using simplified AppleScript"""
    try:
        # Much simpler AppleScript that just opens FaceTime with the contact
        applescript = f'''
        tell application "FaceTime"
            activate
        end tell
        
        delay 2
        
        tell application "System Events"
            tell process "FaceTime"
                -- Use keyboard shortcut to start new call
                keystroke "n" using command down
                delay 1
                
                -- Type the contact info
                keystroke "{contact_info}"
                delay 1
                
                -- Press return to call
                keystroke return
            end tell
        end tell
        '''
        
        subprocess.run(["osascript", "-e", applescript], check=True)
        return f"Calling {display_name} via FaceTime..."
        
    except Exception as e:
        return f"Failed to call {display_name}: {str(e)}"

@tool("make_phone_call", return_direct=True) 
def make_phone_call(contact_name: str) -> str:
    """
    Make a regular phone call to a contact. Uses tel:// URL scheme.
    Use when user specifically asks for a phone call or audio call.
    """
    try:
        # Check our contacts for phone number
        contacts_file = os.path.join(os.path.dirname(__file__), 'contacts.json')
        phone_number = None
        
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
            
            contact_name_lower = contact_name.lower()
            for name, info in contacts.items():
                if name.lower() == contact_name_lower or contact_name_lower in name.lower():
                    # If it's a phone number (contains digits), use tel://
                    if any(char.isdigit() for char in str(info)):
                        phone_number = str(info).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                        break
        
        if phone_number:
            tel_url = f"tel://{phone_number}"
            subprocess.run(["open", tel_url], check=True)
            return f"Calling {contact_name} at {phone_number}..."
        else:
            # Fallback to FaceTime audio call
            return facetime_audio_call(contact_name)
        
    except Exception as e:
        return f"Phone calling failed: {str(e)}"

def facetime_audio_call(contact_name: str) -> str:
    """Make a FaceTime audio call"""
    try:
        # Check contacts for email
        contacts_file = os.path.join(os.path.dirname(__file__), 'contacts.json')
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
            
            contact_name_lower = contact_name.lower()
            for name, email in contacts.items():
                if name.lower() == contact_name_lower or contact_name_lower in name.lower():
                    facetime_audio_url = f"facetime-audio://{email}"
                    subprocess.run(["open", facetime_audio_url], check=True)
                    return f"Starting FaceTime audio call to {contact_name}..."
        
        return f"Could not find contact {contact_name} for audio call"
        
    except Exception as e:
        return f"FaceTime audio call failed: {str(e)}"

@tool("check_facetime_status")
def check_facetime_status() -> str:
    """Check if FaceTime is available and working"""
    try:
        # Check if FaceTime app exists
        result = subprocess.run(
            ["mdfind", "kMDItemCFBundleIdentifier = 'com.apple.FaceTime'"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            return "✅ FaceTime is available on this Mac"
        else:
            return "❌ FaceTime app not found on this Mac"
            
    except Exception as e:
        return f"Could not check FaceTime status: {str(e)}"