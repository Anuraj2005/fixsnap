"""FixSnap — AI Campus Issue Reporter

Architecture & implementation strictly adhering to spec.md:
Onboard -> Streamlit Chat (Text + Vision) -> Gemini Session -> Report Summary -> Telegram Action Tool.
"""

import os
import asyncio
import concurrent.futures
import streamlit as st
from google import genai
from google.genai import types
from telegram import Bot

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)

# Page configuration
st.set_page_config(
    page_title="FixSnap — AI Campus Issue Reporter",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="auto",
)

# Model configuration - defaults to gemini-3.5-flash for reliable throughput
MODEL_NAME = "gemini-3.5-flash"

# Retrieve credentials from Streamlit secrets or environment variables
def get_secret(key: str, default: str = "") -> str:
    """Safely fetch a secret from st.secrets or os.environ."""
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.environ.get(key, default).strip()

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
MODEL_NAME = get_secret("GEMINI_MODEL", MODEL_NAME)


@st.cache_resource
def get_gemini_client(api_key: str):
    """Build and cache the Gemini client."""
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_bot_username(token: str) -> str:
    """Fetches the Telegram bot username dynamically using the token."""
    if not token:
        return ""
    try:
        bot = Bot(token=token)

        async def _get():
            me = await bot.get_me()
            return me.username

        try:
            return asyncio.run(_get())
        except RuntimeError:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(asyncio.run, _get()).result()
    except Exception:
        return ""

bot_username = get_bot_username(TELEGRAM_BOT_TOKEN)


def create_chat_session(client, model=MODEL_NAME):
    """Creates a Gemini chat session with fallback options."""
    models_to_try = [model, "gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]
    seen = set()
    deduped_models = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_err = None
    for m in deduped_models:
        try:
            return client.chats.create(
                model=m,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )
        except Exception as err:
            last_err = err
    raise last_err or RuntimeError("Failed to initialize chat session")


def render_message(message: dict):
    """Renders a single message in the Streamlit chat interface."""
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role: str, kind: str, content):
    """Appends a message to session history and renders it."""
    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )
    render_message(st.session_state.messages[-1])


def ask_gemini(parts) -> str:
    """Sends parts (text and/or image) to the persistent Gemini chat session with auto-recovery and fallback."""
    import time

    # Try current session first
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text
    except Exception:
        pass

    # Auto-recover across supported models if model is busy (503) or deprecated (404)
    fallback_models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
    last_err = None

    for attempt in range(2):
        for fallback_model in fallback_models:
            try:
                st.session_state.chat = create_chat_session(gemini_client, model=fallback_model)
                response = st.session_state.chat.send_message(parts)
                return response.text
            except Exception as e:
                last_err = e
        time.sleep(1.2)

    return f"Sorry, something went wrong: {last_err}"


def send_telegram(chat_id: str, text: str):
    """Dispatches the final report to the specified Telegram chat via Telegram Bot API."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    async def _send():
        await bot.send_message(chat_id=chat_id, text=text)

    try:
        asyncio.run(_send())
    except RuntimeError:
        # Handles running within an existing event loop
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(asyncio.run, _send()).result()


# Check credentials readiness
missing_secrets = []
if not GEMINI_API_KEY:
    missing_secrets.append("GEMINI_API_KEY")
if not TELEGRAM_BOT_TOKEN:
    missing_secrets.append("TELEGRAM_BOT_TOKEN")

if missing_secrets:
    st.error(
        f"⚠️ **Missing Configuration**: The following secret(s) are missing: "
        f"`{', '.join(missing_secrets)}`.\n\n"
        "Please create `.streamlit/secrets.toml` or configure secrets in Streamlit Cloud Settings."
    )
    with st.expander("ℹ️ How to set up secrets"):
        st.markdown(
            """
            Create a file named `.streamlit/secrets.toml` in your project root with the following content:
            ```toml
            GEMINI_API_KEY = "your-actual-gemini-api-key"
            TELEGRAM_BOT_TOKEN = "your-actual-telegram-bot-token"
            ```
            - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/).
            - Create a Telegram bot and get your token from [@BotFather](https://t.me/BotFather).
            """
        )

# Initialize Gemini Client
gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = get_gemini_client(GEMINI_API_KEY)
    except Exception as err:
        st.error(f"Failed to initialize Gemini client: {err}")


# --- Onboarding Screen ---
if "onboarded" not in st.session_state:
    st.title("🛠️ FixSnap")
    st.caption("Snap it. Report it. Send it.")

    st.markdown(
        """
        Welcome to **FixSnap**, your AI campus maintenance assistant!
        Quickly report broken fixtures, leaks, electrical hazards, or facility issues.
        """
    )

    # Dynamic Bot Information Box
    bot_link = f"https://t.me/{bot_username}" if bot_username else "https://t.me/BotFather"
    bot_label = f"@{bot_username}" if bot_username else "Telegram Bot"

    st.info(
        f"📱 **First time here? Follow these 2 quick setup steps:**\n\n"
        f"1. **Start the Bot:** Open [{bot_label}]({bot_link}) on Telegram and press **Start** (or send `/start`).\n"
        f"2. **Get your Chat ID:** Message [@userinfobot](https://t.me/userinfobot) to get your numeric ID (e.g. `123456789`), then paste it below."
    )

    with st.form("onboarding_form"):
        name = st.text_input("Your name", placeholder="e.g. Alex Rivera")
        telegram_chat_id = st.text_input(
            "Telegram chat ID (numbers only)",
            placeholder="e.g. 123456789",
            help="Your numeric user ID. You can find it by messaging @userinfobot on Telegram.",
        )

        submitted = st.form_submit_button("Let's go 🚀", use_container_width=True)

        if submitted:
            clean_name = name.strip()
            clean_chat_id = telegram_chat_id.strip()

            if not clean_name or not clean_chat_id:
                st.warning("Please fill in both your name and Telegram chat ID.")
            elif clean_chat_id.startswith("@"):
                st.warning("⚠️ Please enter your **numerical** Chat ID (e.g. `123456789`), not your @username. You can find it from [@userinfobot](https://t.me/userinfobot).")
            elif not gemini_client:
                st.error("Cannot proceed: Gemini API key is missing or invalid. Please check secrets.")
            else:
                st.session_state.name = clean_name
                st.session_state.telegram_chat_id = clean_chat_id

                try:
                    st.session_state.chat = create_chat_session(gemini_client)
                    st.session_state.messages = []
                    st.session_state.onboarded = True
                    st.rerun()
                except Exception as err:
                    st.error(f"Failed to initialize Gemini chat session: {err}")

    st.stop()


# --- Main Chat Screen ---
# Only execute if onboarded
user_name = st.session_state.get("name", "Reporter")
user_chat_id = st.session_state.get("telegram_chat_id", "")

# Sidebar with user details and session controls
with st.sidebar:
    st.header("👤 Reporter Profile")
    st.write(f"**Name:** {user_name}")
    st.write(f"**Telegram ID:** `{user_chat_id}`")
    if bot_username:
        st.write(f"**Telegram Bot:** [{bot_label}]({bot_link})")
    st.divider()

    st.subheader("💡 Quick Tips")
    st.markdown(
        f"""
        1. **Take a clear photo** of the issue.
        2. Mention the **location** (building, floor, room).
        3. Clarify any questions from FixSnap.
        4. Click **Send Report** to dispatch the report to your Telegram.
        """
    )
    st.divider()

    st.info(
        f"⚠️ **Note:** Ensure you have clicked **Start** on [{bot_label}]({bot_link}) "
        "before dispatching a report so Telegram permits bot delivery."
    )

    if st.button("🔄 Start New Report", use_container_width=True):
        for key in ["onboarded", "name", "telegram_chat_id", "chat", "messages"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Header row with title and action button
header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🛠️ FixSnap")
    st.caption("Snap it. Report it. Send it.")

with button_col:
    messages_history = st.session_state.get("messages", [])
    send_disabled = len(messages_history) <= 2

    if st.button(
        "📤 Send Report",
        disabled=send_disabled,
        use_container_width=True,
    ):
        with st.spinner("Preparing report..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])

            if not TELEGRAM_BOT_TOKEN:
                st.error("Cannot send report: TELEGRAM_BOT_TOKEN is not configured.")
            else:
                try:
                    send_telegram(user_chat_id, summary)
                    st.success("Report successfully sent to Telegram! 🎉")
                    st.toast("Report dispatched to Telegram!", icon="📨")
                except Exception as send_error:
                    st.error(f"Failed to send via Telegram: {send_error}")
                    err_lower = str(send_error).lower()
                    if "chat not found" in err_lower or "forbidden" in err_lower:
                        st.warning(
                            "👉 **Telegram Requirement:**\n"
                            "1. Open Telegram and search for your bot (`@FixSnapReporter_bot`).\n"
                            "2. Click **Start** (or send any message like `/start`).\n"
                            "3. Make sure your Telegram Chat ID is your **numeric ID** (e.g., `123456789`), which you can check by messaging `@userinfobot` on Telegram."
                        )

            with st.expander("📋 View Generated Report Summary", expanded=True):
                st.write(summary)

# Ensure messages list exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Welcome Message or Replay History
if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=user_name
        ),
    )
else:
    for message in st.session_state.messages:
        render_message(message)

# Handle text and photo input
user_input = st.chat_input(
    "Describe the issue, or attach a photo",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    # Support both mapping/ChatInputValue and raw string inputs
    text_content = ""
    uploaded_files = []

    if isinstance(user_input, dict) or hasattr(user_input, "__getitem__"):
        try:
            text_content = user_input.get("text", "") or ""
            uploaded_files = user_input.get("files", []) or []
        except Exception:
            text_content = str(user_input)
    elif hasattr(user_input, "text"):
        text_content = getattr(user_input, "text", "") or ""
        uploaded_files = getattr(user_input, "files", []) or []
    else:
        text_content = str(user_input)

    # Normalize to list if a single file object is returned
    if uploaded_files and not isinstance(uploaded_files, (list, tuple)):
        uploaded_files = [uploaded_files]

    text_content = text_content.strip()

    # Process and record user submissions
    parts = []

    for photo in uploaded_files:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )

    if text_content:
        add_message("user", "text", text_content)
        parts.append(text_content)
    elif uploaded_files and not text_content:
        # Fallback prompt when only photo is provided
        parts.append(
            "Analyze this campus issue and help me create a clear maintenance report."
        )

    if parts:
        with st.spinner("FixSnap is analyzing..."):
            response_text = ask_gemini(parts)
            add_message("assistant", "text", response_text)
            st.rerun()
