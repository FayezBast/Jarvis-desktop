import os
import logging
import time
from dotenv import load_dotenv
import speech_recognition as sr
from langchain_ollama import ChatOllama, OllamaLLM

# Import enhanced speech system
from tools.jarvis_speech import speak_text, get_speech_status


# from langchain_openai import ChatOpenAI # if you want to use openai
from langchain_core.messages import HumanMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# Import web_search tool
from tools.web_search import web_search
from tools.arp_scan import arp_scan_terminal

from tools.matrix import matrix_mode
from tools.screenshot import take_screenshot
from tools.OCR import read_text_from_latest_image
from tools.open_app import open_app, list_available_apps, refresh_app_database
from tools.notes import take_note, read_recent_notes
from tools.youtube import youtube_search, play_youtube_video
from tools.email_tool import send_email, get_email_setup_instructions, send_email_to_contact
from tools.facetime_tool import call_contact, make_phone_call, check_facetime_status

load_dotenv()

MIC_INDEX = None
TRIGGER_WORD = "jarvis"
CONVERSATION_TIMEOUT = 30  # seconds of inactivity before exiting conversation mode

logging.basicConfig(level=logging.DEBUG)  # logging

# api_key = os.getenv("OPENAI_API_KEY") removed because it's not needed for ollama
# org_id = os.getenv("OPENAI_ORG_ID") removed because it's not needed for ollama

recognizer = sr.Recognizer()
mic = sr.Microphone(device_index=MIC_INDEX)

# Initialize LLM
llm = ChatOllama(model="qwen3:1.7b", reasoning=False)

# llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, organization=org_id) for openai

# Tool list
tools = [
    arp_scan_terminal,
    web_search,
    matrix_mode,
    take_screenshot,
    read_text_from_latest_image,
    open_app,
    list_available_apps,
    refresh_app_database,
    take_note,
    read_recent_notes,
    youtube_search,
    play_youtube_video,
    send_email,
    send_email_to_contact,
    get_email_setup_instructions,
    call_contact,
    make_phone_call,
    check_facetime_status
]

# Tool-calling prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are Jarvis, an intelligent, conversational AI assistant. Your goal is to be helpful, friendly, and informative. 

POWERFUL WEB RESEARCH CAPABILITIES:
- I can answer ANY question by intelligently scraping the web for accurate information
- I go beyond search snippets - I actually read and analyze full web page content
- I synthesize information from multiple sources to provide comprehensive answers
- I can research any topic in depth and provide detailed, well-sourced responses
- I automatically format answers based on the type of question (weather, definitions, how-to, etc.)

WEB RESEARCH TOOLS:
- web_search: For any question you don't know - provides comprehensive answers from multiple sources
- web_search_with_sources: Same as web_search but includes source links for verification
- quick_answer: For simple factual questions that need direct, concise answers
- research_topic: For deep research on complex topics with comprehensive analysis  
- get_latest_news: For latest news and current events on any topic

USE CASES:
- General knowledge: "What is quantum computing?" → Detailed explanation from multiple sources
- Current information: "What's the weather in Tokyo?" → Real-time weather data
- How-to guides: "How to change a tire?" → Step-by-step instructions from expert sources
- Factual queries: "Who is the current CEO of Apple?" → Up-to-date factual information
- Definitions: "What does blockchain mean?" → Clear definitions with examples
- News/events: "Latest AI developments" → Recent news with multiple perspectives
- Research: "Climate change effects" → Comprehensive analysis from multiple sources

APPLICATION LAUNCHING CAPABILITIES:
- I have comprehensive knowledge of ALL applications installed on this Mac
- I can open any app by name, nickname, or partial match (e.g., "chrome", "code", "calc", "spotify")
- I know about browsers, development tools, communication apps, media players, productivity apps, games, etc.
- I can list available applications organized by category
- I can refresh my app database when new applications are installed

IMPORTANT COMMUNICATION INSTRUCTIONS:
- For emails to contact names: use send_email_to_contact tool
- For FaceTime/video calls: use call_contact tool  
- For phone calls: use make_phone_call tool
- For opening applications: use open_app tool with any app name or nickname
- For ANY question you don't know: use web_search to research and provide accurate answers
- For deep research: use research_topic for comprehensive information
- For current events: use get_latest_news
- For quick facts: use quick_answer for concise responses
- For answers with sources: use web_search_with_sources when verification is needed
- NEVER ask for phone numbers or email addresses when user mentions contact names
- NEVER say you don't know something - always use answer_question to research it

Examples:
- "What's the weather in Paris?" → use web_search for real-time weather
- "Who is Elon Musk?" → use web_search for comprehensive biography
- "How do I make pasta?" → use web_search for detailed cooking instructions
- "What is artificial intelligence?" → use web_search for clear definitions
- "Latest tech news" → use get_latest_news for recent technology developments
- "Research climate change" → use research_topic for in-depth analysis
- "Call mom" → use call_contact with contact_name="mom"
- "Open Chrome" → use open_app with app_name="chrome"

I am your intelligent research assistant. I can find accurate, up-to-date information about anything by scraping and analyzing web content from multiple sources. Always use my research tools to provide comprehensive, well-sourced answers.""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


# Agent + executor
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# Main interaction loop
def write():
    conversation_mode = False
    last_interaction_time = None

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    if not conversation_mode:
                        logging.info("🎤 Listening for wake word...")
                        audio = recognizer.listen(source, timeout=10)
                        transcript = recognizer.recognize_google(audio)
                        logging.info(f"🗣 Heard: {transcript}")

                        if TRIGGER_WORD.lower() in transcript.lower():
                            logging.info(f"🗣 Triggered by: {transcript}")
                            speak_text("Yes sir?")
                            conversation_mode = True
                            last_interaction_time = time.time()
                        else:
                            logging.debug("Wake word not detected, continuing...")
                    else:
                        logging.info("🎤 Listening for next command...")
                        audio = recognizer.listen(source, timeout=10)
                        command = recognizer.recognize_google(audio)
                        logging.info(f"📥 Command: {command}")

                        logging.info("🤖 Sending command to agent...")
                        response = executor.invoke({"input": command})
                        content = response["output"]
                        logging.info(f"✅ Agent responded: {content}")

                        print("Jarvis:", content)
                        speak_text(content)
                        last_interaction_time = time.time()

                        if time.time() - last_interaction_time > CONVERSATION_TIMEOUT:
                            logging.info("⌛ Timeout: Returning to wake word mode.")
                            conversation_mode = False

                except sr.WaitTimeoutError:
                    logging.warning("⚠️ Timeout waiting for audio.")
                    if (
                        conversation_mode
                        and time.time() - last_interaction_time > CONVERSATION_TIMEOUT
                    ):
                        logging.info(
                            "⌛ No input in conversation mode. Returning to wake word mode."
                        )
                        conversation_mode = False
                except sr.UnknownValueError:
                    logging.warning("⚠️ Could not understand audio.")
                except Exception as e:
                    logging.error(f"❌ Error during recognition or tool call: {e}")
                    time.sleep(1)

    except Exception as e:
        logging.critical(f"❌ Critical error in main loop: {e}")


if __name__ == "__main__":
    write()
