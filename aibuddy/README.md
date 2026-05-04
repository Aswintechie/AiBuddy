# AiBuddy 🤖

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A production-ready Microsoft Teams bot powered by **Llama 3** via the [Groq](https://console.groq.com) API.  
AiBuddy brings fast, contextual AI conversations directly into Teams — personal chats, group chats, and channels.

---

## ✨ Features

- 🚀 **Ultra-fast responses** — Groq's inference engine delivers near-instant replies
- 🧠 **Contextual memory** — remembers the last 10 messages per user
- 💬 **Markdown support** — rich formatting in Teams messages
- 🔧 **Built-in commands** — `help`, `about`, `clear`
- 🏥 **Health check endpoint** — Koyeb-ready liveness probe
- 🔒 **Zero hardcoded secrets** — everything from environment variables
- 📋 **Production logging** — structured logs with configurable levels

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Bot Framework | Microsoft Bot Framework SDK v4 (`botbuilder-core`) |
| AI / LLM | Llama 3.3 70B via [Groq](https://groq.com) |
| Web Server | aiohttp (async) |
| Hosting | Koyeb free tier |

---

## 📋 Prerequisites

- **Python 3.11+**
- **Groq API key** — [Get one free](https://console.groq.com)
- **Azure Bot registration** — [Step-by-step guide](https://learn.microsoft.com/en-us/azure/bot-service/bot-service-quickstart-registration)
- **Koyeb account** — [Sign up free](https://app.koyeb.com)

---

## 🚀 Local Development

```bash
# 1. Clone and enter the project directory
git clone https://github.com/Aswintechie/AiBuddy.git
cd AiBuddy/aibuddy

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD, and GROQ_API_KEY

# 5. Start the bot server
python app.py
```

The server starts on `http://localhost:8080`.  
Use [ngrok](https://ngrok.com) or [Bot Framework Emulator](https://github.com/microsoft/BotFramework-Emulator) to test locally.

---

## ☁️ Deployment to Koyeb

1. **Push your code** to a GitHub repository (secrets excluded via `.gitignore`).
2. **Create a new Koyeb service**:
   - Source: GitHub repository
   - Builder: Buildpack
   - Run command: `python app.py` (or rely on `Procfile`)
3. **Set environment variables** in the Koyeb dashboard:

   | Variable | Description |
   |----------|-------------|
   | `MICROSOFT_APP_ID` | Azure Bot App ID |
   | `MICROSOFT_APP_PASSWORD` | Azure Bot App Password |
   | `GROQ_API_KEY` | Your Groq API key |
   | `GROQ_MODEL` | `llama-3.3-70b-versatile` (default) |
   | `PORT` | `8080` (Koyeb default) |
   | `LOG_LEVEL` | `INFO` |

4. **Note the public URL** Koyeb assigns (e.g. `https://aibuddy-xxxx.koyeb.app`).
5. **Update your Azure Bot** messaging endpoint to:
   ```
   https://aibuddy-xxxx.koyeb.app/api/messages
   ```

---

## 🔧 Microsoft Teams Setup

### 1. Register an Azure Bot

1. Go to [Azure Portal](https://portal.azure.com) → **Create a resource** → **Azure Bot**
2. Choose **Multi Tenant** and note the **App ID** and **App Password**
3. Set the messaging endpoint to your Koyeb URL: `https://<your-app>.koyeb.app/api/messages`

### 2. Configure the Teams channel

In your Azure Bot resource, go to **Channels** → **Microsoft Teams** → enable it.

### 3. Prepare the Teams manifest

1. **Generate a GUID** for the app ID (PowerShell: `New-Guid`, or use [guidgenerator.com](https://guidgenerator.com)):
   ```
   e.g. 3d1a6b9c-4f2e-4a8b-8c3d-1e2f3a4b5c6d
   ```
2. Open `manifest/manifest.json` and replace:
   - `{{REPLACE_WITH_GUID}}` — the GUID you just generated
   - `{{REPLACE_WITH_BOT_ID}}` — your Azure Bot **App ID**

3. **Add icon files** (required for Teams submission):
   - `manifest/color.png` — **192 × 192 px** full-colour icon
   - `manifest/outline.png` — **32 × 32 px** monochrome outline icon  
   *(The placeholder files in the repository must be replaced with real PNG images before submitting to the Marketplace.)*

4. **Create the app package**:
   ```bash
   cd manifest
   zip AiBuddy.zip manifest.json color.png outline.png
   ```

5. **Sideload in Teams** (for testing):
   - Teams → Apps → Manage your apps → Upload an app → Upload a custom app
   - Select `AiBuddy.zip`

---

## 🗂 Project Structure

```
aibuddy/
├── app.py              # aiohttp server & route handlers
├── bot.py              # AiBuddyBot activity handler
├── config.py           # Environment variable management
├── requirements.txt    # Python dependencies
├── Procfile            # Koyeb run command
├── runtime.txt         # Python version hint
├── .gitignore          # Files excluded from git
├── .env.example        # Environment variable template
├── README.md           # This file
└── manifest/
    ├── manifest.json   # Teams app manifest (v1.16)
    ├── color.png       # 192×192 app icon (replace with real PNG)
    └── outline.png     # 32×32 outline icon (replace with real PNG)
```

---

## 🌐 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/messages` | Microsoft Bot Framework message endpoint |
| `GET` | `/health` | Liveness probe — returns `{"status":"ok"}` |
| `GET` | `/` | Alias for `/health` |

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MICROSOFT_APP_ID` | ✅ | — | Azure Bot registration App ID |
| `MICROSOFT_APP_PASSWORD` | ✅ | — | Azure Bot registration App Password |
| `GROQ_API_KEY` | ✅ | — | Groq API key (starts with `gsk_`) |
| `GROQ_MODEL` | ❌ | `llama-3.3-70b-versatile` | Groq model to use |
| `PORT` | ❌ | `8080` | Server listen port |
| `LOG_LEVEL` | ❌ | `INFO` | Python log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ValueError: Required environment variable … is not set` | Copy `.env.example` to `.env` and fill in all required values |
| Bot not responding in Teams | Check the messaging endpoint URL in Azure Bot; verify Koyeb app is running |
| `401 Unauthorized` from Bot Framework | Ensure `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` match your Azure Bot registration |
| Groq API errors | Verify `GROQ_API_KEY` is valid and the model name is correct |
| Teams manifest upload fails | Ensure both `color.png` (192×192) and `outline.png` (32×32) are real PNG files |

---

## 🔒 Privacy & Support

- [Privacy Policy](https://aswintechie.github.io/AiBuddy/privacy)
- [Support](https://aswintechie.github.io/AiBuddy/support)

---

## 📄 License

MIT License — see [LICENSE](../LICENSE) for details.
