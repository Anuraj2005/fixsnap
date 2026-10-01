# FixSnap 🛠️ — AI Campus Issue Reporter

> **Snap it. Report it. Send it.**  
> An AI-powered vision and conversational web application that turns photos and descriptions of campus facility issues into structured maintenance reports dispatched directly to Telegram.

---

## 📌 Table of Contents
1. [Overview & Architecture](#-overview--architecture)
2. [Project Structure](#-project-structure)
3. [Prerequisites](#-prerequisites)
4. [API Keys & Credentials Setup](#-api-keys--credentials-setup)
   - [1. Google Gemini API Key](#1-google-gemini-api-key)
   - [2. Telegram Bot Token & Chat ID](#2-telegram-bot-token--chat-id)
5. [Local Installation & Setup](#-local-installation--setup)
6. [Operating Procedure (User Flow)](#-operating-procedure-user-flow)
7. [Deployment Guide (Streamlit Community Cloud)](#-deployment-guide-streamlit-community-cloud)
8. [Submission Checklist](#-submission-checklist)

---

## 🏗 Overview & Architecture

FixSnap follows a clean, single-purpose conversational vision pipeline:

```text
┌─────────────────────────────┐
│       User Onboarding       │  Name + Telegram Chat ID
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Streamlit App         │  Interactive Chat + Vision
│     Text + Image Input      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│        Gemini Client        │  gemini-2.5-flash
│      Gemini Vision + Chat   │  System-scoped prompt
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│    Conversation Session     │  st.session_state.chat
│                             │  st.session_state.messages
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│     Report Summary Prompt   │  One clear, actionable summary
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Telegram Bot API       │  python-telegram-bot
│      Send Final Report      │  Dispatched to user's chat ID
└─────────────────────────────┘
```

---

## 📂 Project Structure

```text
fixsnap/
├── app.py                         # Main Streamlit application
├── prompts.py                     # AI system prompts and message templates
├── requirements.txt               # Project dependencies
├── .gitignore                     # Git ignore rules (protects secrets & venv)
├── README.md                      # Operation & deployment manual
└── .streamlit/
    └── secrets.toml.example       # Template for API keys & credentials
```

---

## ⚙️ Prerequisites

- **Python 3.9+** (Tested on Python 3.12)
- **pip** package manager
- A **Google AI Studio** account (for Gemini API)
- A **Telegram** account (for bot alerts)

---

## 🔑 API Keys & Credentials Setup

FixSnap requires two credentials:

### 1. Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **Get API key** and generate a new key.
4. Copy the API key.

### 2. Telegram Bot Token & Chat ID
#### Step A: Create the Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start the chat and send:
   ```text
   /newbot
   ```
3. Enter a display name (e.g., `FixSnap Campus Bot`) and a unique username ending in `bot` (e.g., `FixSnapReporter_bot`).
4. BotFather will provide an **HTTP API Token** (e.g., `7123456789:AAH...`). Copy this token as your `TELEGRAM_BOT_TOKEN`.

#### Step B: Start Chatting with Your Bot (Important!)
> ⚠️ **CRITICAL:** Telegram prohibits bots from sending messages to users who have not interacted with them first. Open your newly created bot in Telegram and click **Start** (or send `/start`).

#### Step C: Find Your Telegram Chat ID
1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram and press **Start**.
2. It will reply with your numerical **Id** (e.g., `123456789`). This is your `telegram_chat_id`.

---

## 💻 Local Installation & Setup

### Step 1: Clone or Navigate to the Project
Ensure your terminal is in the project folder (`FixSnap`).
```bash
# If not already inside the directory:
cd C:\Users\anura\OneDrive\Desktop\FixSnap
```

### Step 2: Create and Activate a Virtual Environment

- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **Windows PowerShell:**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(If PowerShell policy restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **Windows Command Prompt:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Local Secrets
1. In the project root, create a `.streamlit` folder if it doesn't exist.
2. Create `.streamlit/secrets.toml` by copying from the example:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
3. Edit `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key"
   TELEGRAM_BOT_TOKEN = "your-actual-telegram-bot-token"
   # Optional: customize Gemini model (defaults to gemini-3.5-flash with auto-fallback)
   # GEMINI_MODEL = "gemini-3.5-flash"
   ```
> 🔒 **Security Notice:** `.streamlit/secrets.toml` is listed in `.gitignore` and must **never** be committed to GitHub.

---

## 🕹 Operating Procedure (User Flow)

### 1. Launch the Application
Run the Streamlit server:
```bash
streamlit run app.py
```
Your default browser will open automatically at:
```text
http://localhost:8501
```

### 2. Complete Onboarding (First-Time User Experience)
When a user opens FixSnap for the first time, the onboarding screen dynamically detects and displays the configured Telegram bot:
1. **Start the Bot:** The user clicks the direct link (e.g. `👉 Open @FixSnapReporter_bot on Telegram`) and taps **Start** (or sends `/start`). This authorizes the bot to deliver reports to them.
2. **Find Chat ID:** The user clicks the [@userinfobot](https://t.me/userinfobot) link on screen to view their numerical ID (e.g., `123456789`).
3. **Submit:** The user enters their **Name** and numerical **Telegram Chat ID** and clicks **Let's go 🚀**.
4. The system initializes the Gemini vision and chat session.

### 3. Report an Issue (Conversational Chat + Vision)
1. **With a photo:** Attach an image (`.jpg`, `.jpeg`, `.png`) of a campus problem (e.g., a leaking water pipe, broken desk, damaged tile) in the chat input. Optionally add a description or location (e.g., *“3rd floor Science building restroom”*).
2. **With text only:** Type a description of the facility issue.
3. FixSnap analyzes the visual details and responds conversationally, asking clarifying questions if needed.

### 4. Send Report to Telegram
1. Once at least one exchange has occurred, the **📤 Send Report** button in the header is enabled.
2. Click **📤 Send Report**.
3. FixSnap requests a clean, concise summary from Gemini using `SUMMARY_REQUEST_PROMPT`.
4. FixSnap dispatches the final report to your Telegram bot, which instantly delivers the notification to your Telegram chat.
5. A confirmation message and copy of the dispatched report will appear on screen.

### 5. Start a New Report
Click **🔄 Start New Report** in the sidebar to reset the session and start a new issue ticket.

---

## 🚀 Deployment Guide (Streamlit Community Cloud)

Follow these steps to deploy FixSnap to the web for free:

```text
Local Project ➔ GitHub Repository ➔ Streamlit Community Cloud ➔ Add Secrets ➔ Live URL
```

### Step 1: Push Code to GitHub
1. Initialize a git repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit of FixSnap"
   ```
2. Create a new repository on [GitHub](https://github.com/new) (e.g., `fixsnap`).
3. Link and push your code:
   ```bash
   git remote add origin https://github.com/<your-username>/fixsnap.git
   git branch -M main
   git push -u origin main
   ```
4. Verify that `.streamlit/secrets.toml` was **not** pushed to GitHub.

### Step 2: Deploy on Streamlit Community Cloud
1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with your GitHub account.
2. Click **Create app** (or **New app**).
3. Select your GitHub repository (`<your-username>/fixsnap`), branch (`main`), and set the main file path to:
   ```text
   app.py
   ```

### Step 3: Configure Cloud Secrets
1. Before or immediately after launching, click **Advanced settings...** or open the app's settings menu (three dots `⋮` ➔ **Settings** ➔ **Secrets**).
2. In the **Secrets** editor, paste your credentials:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key"
   TELEGRAM_BOT_TOKEN = "your-actual-telegram-bot-token"
   ```
3. Click **Save**.

### Step 4: Access Your Live Application
Streamlit Cloud will provision the container, install packages from `requirements.txt`, and boot the app. You will receive a public URL (e.g., `https://fixsnap.streamlit.app`).

---

## ✅ Submission Checklist

- [x] `app.py` created and structured per architecture specification
- [x] `prompts.py` containing `SYSTEM_PROMPT`, `WELCOME_MESSAGE_TEMPLATE`, and `SUMMARY_REQUEST_PROMPT`
- [x] `requirements.txt` listing `streamlit`, `google-genai`, and `python-telegram-bot`
- [x] `.gitignore` configured to exclude secrets, virtual environments, and caches
- [x] `.streamlit/secrets.toml.example` provided as a configuration blueprint
- [x] `.streamlit/secrets.toml` kept local and secret
- [x] End-to-end flow tested (Onboarding ➔ Photo/Text ➔ Gemini Vision/Chat ➔ Telegram Action)
- [x] Complete operation and deployment procedures documented in `README.md`
