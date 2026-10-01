FixSnap — AI Campus Issue Reporter

Architecture and Build Guide

Source basis: This guide adapts the architecture, implementation pattern, setup, deployment, and submission guidance from the uploaded Build Your AI Vision ChatBot — MacroSnap PDF. The PDF explicitly describes reusing the same building blocks and changing the use case rather than the overall structure.

1. Project Overview

FixSnap

FixSnap is an adaptation of the MacroSnap architecture for a campus maintenance/reporting use case.

The user:

Enters their name and Telegram chat ID once.

Chats with an AI through a Streamlit interface.

Uploads a photo of a campus issue or types a description.

Gemini analyzes the image/text and continues the conversation.

Gemini creates a concise report from the conversation.

One action button sends the report through Telegram.

Core pattern

Onboarding
    ↓
Streamlit Chat
    ↓
Text + Image Input
    ↓
Gemini Vision + Chat
    ↓
Conversation History
    ↓
Report Summary
    ↓
Telegram Bot

The PDF describes the same reusable structure as an onboard → chat → action-tool send pattern. For FixSnap, Telegram is the selected action tool.

2. System Architecture

┌─────────────────────────────┐
│       User Onboarding       │
│  Name + Telegram chat ID    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Streamlit App         │
│      Chat Interface         │
│     Text + Image Input      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│        Gemini Client        │
│      Gemini Vision + Chat   │
│    System Instruction       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│    Conversation Session     │
│     st.session_state.chat   │
│  st.session_state.messages  │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│     Report Summary Prompt   │
│  Generate one clean report  │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│        Telegram Bot         │
│      Send Final Report      │
└─────────────────────────────┘

3. Technology Stack

Use the same core technologies used by MacroSnap, with Telegram selected as the action tool:

Python 3.9 or newer

Streamlit

Google Gemini

Gemini chat

Gemini vision

Telegram Bot

python-telegram-bot

The MacroSnap PDF describes Gemini as the chat + vision component and the messaging service as the action tool. It also provides Telegram as a free alternative action tool using python-telegram-bot.

4. Project Structure

Use the same project organization as MacroSnap, with the project name changed:

fixsnap/
├── app.py
├── prompts.py
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml.example

File purpose

File

Purpose

app.py

Main Streamlit application

prompts.py

AI personality and report prompts

requirements.txt

Python dependencies

.gitignore

Prevents secrets and local files from being committed

.streamlit/secrets.toml.example

Template for API keys and credentials

Keeping prompts in prompts.py separates the AI's personality from the application logic.

5. Environment Setup

Step 1 — Create the project

Create a project folder:

mkdir fixsnap
cd fixsnap

Step 2 — Create a virtual environment

python -m venv venv

macOS / Linux

source venv/bin/activate

Windows PowerShell

.\venv\Scripts\Activate.ps1

If PowerShell blocks activation:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Windows Command Prompt

venv\Scripts\activate.bat

Step 3 — Install dependencies

pip install -r requirements.txt

6. requirements.txt

For the Telegram version:

streamlit
google-genai
python-telegram-bot

The PDF specifically says to add python-telegram-bot when Telegram is selected.

7. API Keys and Credentials

Gemini

Get a Gemini API key from Google AI Studio.

The application reads it from Streamlit secrets:

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

Telegram

The PDF's Telegram option uses:

Telegram bot token

Recipient chat ID

Create the bot through Telegram's @BotFather:

@BotFather
    ↓
/newbot
    ↓
Follow the prompts
    ↓
Receive bot token

The recipient must send any message to the new bot once before the bot is allowed to message them.

The PDF notes that the recipient's chat_id can be obtained through the getUpdates API or a library helper.

8. prompts.py Architecture

MacroSnap keeps three prompt components:

SYSTEM_PROMPT
WELCOME_MESSAGE_TEMPLATE
SUMMARY_REQUEST_PROMPT

FixSnap follows the same structure.

8.1 SYSTEM_PROMPT

Purpose

Define the AI's personality and keep Gemini focused on the single purpose of the application.

FixSnap adaptation

SYSTEM_PROMPT = """
You are FixSnap, a friendly AI campus issue reporting assistant.

Your ONLY job is to help the user understand and describe a campus
maintenance or facility issue from a photo or text description.

If the user asks about anything unrelated to campus issues or reporting,
politely decline and steer the conversation back to the issue.

When analyzing a photo or description, identify the visible issue and
help collect the information needed for a clear report.

Keep replies short, friendly, and conversational - no markdown formatting.
"""

This follows the PDF's principle that the system prompt should keep Gemini scoped to one job.

9. Welcome Message

MacroSnap creates the first message using a template with the user's name. FixSnap uses the same pattern:

WELCOME_MESSAGE_TEMPLATE = (
    "Hey {name}! I'm FixSnap 🛠️ - your AI campus issue reporting assistant.\n\n"
    "Upload a photo of a campus problem, or describe the issue, and I'll "
    "help turn it into a clear report.\n\n"
    "When you're done, use the Send Report button to send the report to Telegram."
)

The {name} value is filled in after onboarding.

10. Report Summary Prompt

MacroSnap sends a hidden summary prompt to Gemini when the action button is clicked.

FixSnap uses the same mechanism:

SUMMARY_REQUEST_PROMPT = (
    "Summarize the campus issue discussed in this conversation into one "
    "clear, concise report. Include the issue, location or other details "
    "provided by the user, and the relevant information needed for the "
    "report. Keep it short, plain text and ready to send."
)

The summary prompt is sent to Gemini when the Send Report button is clicked.

11. Connecting to Gemini

Build the Gemini client once and cache it:

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

gemini_client = get_gemini_client()

The PDF highlights that Streamlit re-executes the script on interactions. @st.cache_resource lets the Gemini client persist and be reused.

12. Onboarding Screen

FixSnap collects:

Name
+
Telegram chat ID

Use the same onboarding architecture as MacroSnap:

if "onboarded" not in st.session_state:
    st.title("🛠️ FixSnap")
    st.caption("Snap it. Report it. Send it.")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        telegram_chat_id = st.text_input("Telegram chat ID")

        submitted = st.form_submit_button("Let's go 🚀")

        if submitted:
            if not name.strip() or not telegram_chat_id.strip():
                st.warning(
                    "Please fill in both your name and Telegram chat ID."
                )
            else:
                st.session_state.name = name.strip()
                st.session_state.telegram_chat_id = telegram_chat_id.strip()

                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    ),
                )

                st.session_state.messages = []
                st.session_state.onboarded = True
                st.rerun()

    st.stop()

The MacroSnap flow uses onboarding to save user details, create the Gemini chat session, initialize message history, mark the session as onboarded, and rerun the app.

13. Gemini Conversation Session

Create the Gemini chat during onboarding:

st.session_state.chat = gemini_client.chats.create(
    model=MODEL_NAME,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT
    ),
)

All later messages reuse the same conversation session.

Photo → AI response
       ↓
User follow-up
       ↓
Same conversation
       ↓
More details
       ↓
Final report

14. Message Storage

Use the same message structure as MacroSnap:

{
    "role": "user" or "assistant",
    "kind": "text" or "image",
    "content": ...
}

Rendering messages

def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])

Adding messages

def add_message(role, kind, content):
    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content
        }
    )
    render_message(st.session_state.messages[-1])

This allows both text and images to be stored and rendered from the same conversation history.

15. Handling Text and Photos

Use Streamlit's combined chat input:

user_input = st.chat_input(
    "Describe the issue, or attach a photo",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

The MacroSnap pattern is:

st.chat_input(...)
       ↓
photo + text
       ↓
build parts
       ↓
send parts to Gemini

Handling the image

photo_bytes = photo.getvalue()

parts.append(
    types.Part.from_bytes(
        data=photo_bytes,
        mime_type=photo.type
    )
)

This is the vision step: the image bytes and MIME type are passed to Gemini.

If the user sends only a photo, provide an instruction so the request still works:

parts.append(
    "Analyze this campus issue and help me create a clear maintenance report."
)

16. Asking Gemini

Reuse the same helper pattern:

def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"

Every normal user interaction goes through:

ask_gemini(parts)

and the response is stored in the same conversation.

17. FixSnap Chat Flow

User enters name + Telegram chat ID
              ↓
      Create Gemini chat
              ↓
     Display welcome message
              ↓
       User uploads photo
              ↓
     Store image in history
              ↓
       Send image to Gemini
              ↓
       Gemini analyzes issue
              ↓
     User adds more details
              ↓
       Gemini continues chat
              ↓
      User clicks Send Report
              ↓
     SUMMARY_REQUEST_PROMPT
              ↓
       Gemini creates report
              ↓
        Telegram Bot sends

18. Display the Welcome Message

When the conversation is empty, show the welcome message. Otherwise, replay message history:

if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        )
    )
else:
    for message in st.session_state.messages:
        render_message(message)

The PDF uses this pattern so the welcome message appears only on the first empty conversation.

19. Send Report Button

The PDF places the action button beside the title using:

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center"
)

For FixSnap:

with header_col:
    st.title("🛠️ FixSnap")

with button_col:
    send_disabled = len(st.session_state.messages) <= 2

    if st.button(
        "📤 Send Report",
        disabled=send_disabled,
        use_container_width=True
    ):
        with st.spinner("Preparing report..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])

            # Send summary using Telegram

The disabled state keeps the button unavailable until there is an actual logged exchange.

20. Telegram Action

Telegram is the only action tool used by FixSnap.

The PDF provides this pattern:

import asyncio
from telegram import Bot

TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

def send_telegram(chat_id, text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    asyncio.run(
        bot.send_message(
            chat_id=chat_id,
            text=text
        )
    )

The recipient must first send a message to the bot once before the bot is allowed to message them.

21. Telegram Action-Tool Architecture

                 Gemini Summary
                       ↓
                ┌──────────────┐
                │ Send Function│
                └──────┬───────┘
                       ↓
                send_telegram()
                       ↓
                 Telegram Bot
                       ↓
                 Final Report

The PDF's reusable rule is to keep the onboarding, chat, prompts, and summary flow structurally the same while changing the action tool details.

22. .streamlit/secrets.toml.example

Use the Telegram configuration:

GEMINI_API_KEY = "your-gemini-api-key-here"
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token-here"

Create the real local secrets file as:

.streamlit/secrets.toml

Never commit the real secrets.toml.

Only commit:

.streamlit/secrets.toml.example

23. .gitignore

The PDF specifies excluding:

.streamlit/secrets.toml
venv/
__pycache__/

Example:

.streamlit/secrets.toml
venv/
__pycache__/

24. Complete Architecture of app.py

Imports
  ↓
Configuration
  ↓
Read Streamlit secrets
  ↓
Cache Gemini client
  ↓
Telegram token
  ↓
render_message()
  ↓
add_message()
  ↓
ask_gemini()
  ↓
Telegram send function
  ↓
Onboarding
  ↓
Create Gemini chat
  ↓
Initialize message history
  ↓
Chat interface
  ↓
Render conversation
  ↓
Accept text/photo
  ↓
Build Gemini parts
  ↓
Call Gemini
  ↓
Store AI response
  ↓
Send Report button
  ↓
Generate summary
  ↓
Send summary to Telegram

25. Local Execution

Run:

streamlit run app.py

The PDF states that this opens the application at:

http://localhost:8501

Then test the complete flow:

Onboard
  ↓
Try a text issue
  ↓
Try a photo
  ↓
Continue with a follow-up question
  ↓
Click Send Report
  ↓
Check the Telegram bot

26. Deployment

The PDF uses Streamlit Community Cloud.

Deployment flow

Local Project
     ↓
GitHub Repository
     ↓
Streamlit Community Cloud
     ↓
Select repository
     ↓
Select branch
     ↓
Select app.py
     ↓
Add Secrets
     ↓
Deploy
     ↓
Public App URL

Steps

Push the project to a GitHub repository.

Do not commit .streamlit/secrets.toml.

Sign in to Streamlit Community Cloud with GitHub.

Create a new app.

Select the repository, branch, and app.py.

Open the application's Settings → Secrets.

Paste the same secret values used locally.

Deploy.

27. Submission Requirements

The PDF specifies two submission items:

1. Public or shared GitHub repository link
2. Live deployed Streamlit Community Cloud app link

Repository contents

app.py
prompts.py
requirements.txt
.streamlit/secrets.toml.example
.gitignore
README

The real secrets file must not be committed.

28. Evaluation Mapping

The PDF uses these evaluation categories:

Criterion

Weight

FixSnap implementation

Functionality

40%

Input → Gemini response → report → Telegram

Prompt design

20%

Clearly scoped campus issue system prompt

Code quality

20%

Organized files and protected secrets

Creativity / polish

20%

Thoughtful extensions and user experience

29. What Changes from MacroSnap to FixSnap?

The architecture does not need to be redesigned.

Keep the same

Streamlit
Gemini client
Gemini chat session
Session state
Message history
Text + image input
Image bytes → Gemini
Summary prompt
Action button
Telegram
Secrets
GitHub
Streamlit deployment

Change only

Project name
        ↓
FixSnap

AI personality
        ↓
Campus issue reporting

Image subject
        ↓
Campus problem

AI response
        ↓
Issue identification + conversational clarification

Summary
        ↓
Maintenance / issue report

Button
        ↓
Send Report

Action tool
        ↓
Telegram Bot

The PDF's own project-idea section says the same structure should be reused and the chat topic changed rather than rebuilding the structure.

30. Suggested FixSnap User Flow

┌───────────────┐
│    START      │
└───────┬───────┘
        ↓
┌──────────────────────┐
│ Enter Name + Telegram│
│       Chat ID        │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Upload Problem Photo │
│   or Type Description│
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│    Gemini Vision     │
│    + Gemini Chat     │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Ask / Answer Follow- │
│ up Questions         │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Generate Final Report│
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│    Send Report       │
└──────────┬───────────┘
           ↓
      Telegram Bot

31. Implementation Checklist

Files

app.py

prompts.py

requirements.txt

.gitignore

.streamlit/secrets.toml.example

README

Core functionality

Onboarding works once per session

Gemini client is cached

Gemini chat session is stored in session state

Message history is stored in session state

Text input works

Image upload works

Image bytes are passed to Gemini

Follow-up questions use the same chat session

Summary prompt reads the conversation

Send button stays disabled until a real exchange exists

Telegram bot sends the summary

Errors are handled

Real secrets are excluded from Git

Deployment

GitHub repository created

secrets.toml not committed

Streamlit Cloud app created

Secrets added in Streamlit settings

Live app tested end to end

32. Final Architecture Principle

The key idea from the MacroSnap guide is architectural reuse:

              ┌─────────────────┐
              │  PHOTO / TEXT   │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ GEMINI VISION   │
              │      + CHAT     │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ CONVERSATION    │
              │    MEMORY       │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ CLEAN SUMMARY   │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ TELEGRAM BOT    │
              └─────────────────┘

For FixSnap, the domain-specific prompts, user-facing wording, and final report content are adapted while the underlying MacroSnap architecture remains the foundation.