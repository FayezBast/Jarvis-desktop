import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@tool
def send_email_to_contact(contact_name: str, subject: str, message: str) -> str:
    """Send an email to a saved contact by name from contacts.json. Use this tool when the user mentions sending email to a person's name like 'mom', 'dad', 'john', etc. This is the preferred method for sending emails to avoid dictating email addresses."""
    try:
        contacts_file = os.path.join(os.path.dirname(__file__), 'contacts.json')
        with open(contacts_file, 'r') as f:
            contacts = json.load(f)
        
        contact_name_lower = contact_name.lower()
        
        # First try exact match
        if contact_name_lower in contacts:
            return send_email.invoke({'to_email': contacts[contact_name_lower], 'subject': subject, 'message': message})
        
        # Then try partial match
        for name, email in contacts.items():
            if contact_name_lower in name.lower() or name.lower() in contact_name_lower:
                return send_email.invoke({'to_email': email, 'subject': subject, 'message': message})
        
        # If no match found
        available_contacts = ", ".join(contacts.keys())
        return f"Contact '{contact_name}' not found. Available contacts: {available_contacts}"
    except Exception as e:
        return f"Failed to send email to contact: {str(e)}"

@tool
def send_email(to_email: str, subject: str, message: str) -> str:
    """Send an email. Requires EMAIL_ADDRESS and EMAIL_PASSWORD in .env file."""
    try:
        # Get email credentials from environment variables
        from_email = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        
        if not from_email or not password:
            return "Email credentials not found. Please set EMAIL_ADDRESS and EMAIL_PASSWORD in your .env file."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable encryption
        server.login(from_email, password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        return f"Email sent successfully to {to_email}"
        
    except Exception as e:
        return f"Failed to send email: {str(e)}. Make sure you have EMAIL_ADDRESS and EMAIL_PASSWORD set in .env file, and use an app password for Gmail."

@tool
def get_email_setup_instructions() -> str:
    """Get instructions for setting up email credentials."""
    instructions = """
To use the email feature, add these to your .env file:

EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

For Gmail:
1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate an "App Password" 
4. Use that app password (not your regular password)

For other email providers, you may need to adjust the SMTP settings in the send_email function.
"""
    return instructions
