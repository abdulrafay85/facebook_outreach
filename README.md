<div align="center">
  <h1>🚀 AI Facebook Outreach Automation</h1>
  <p><strong>An End-to-End Autonomous Workflow for B2B Lead Generation and Hyper-Personalized Outreach</strong></p>
</div>

---

## 📌 Overview

**Facebook Outreach Automation** is a powerful Python-based backend service designed to streamline the sales and marketing process for agencies, B2B services, and real estate professionals. 

It completely automates the heavy-lifting of prospecting: discovering potential leads running targeted Facebook Ads, deep-scraping their business profiles, utilizing AI to forge highly personalized email pitches, and dispatching those emails autonomously.

## ✨ Core Features

- 🎯 **Targeted Lead Discovery:** Integrates directly with the **Facebook Ads API** to search for active ad campaigns based on location, dates, and highly specific industry keywords (e.g., "real estate", "digital marketing").
- 🕵️ **Deep Data Extraction:** Under the hood, utilizes **Apify's Facebook Pages Scraper** to intelligently visit lead pages, pulling rich context like bios, follower counts, verified emails, website URLs, and company intros.
- 🤖 **AI-Driven Pitch Generation:** Employs the cutting-edge **Google Gemini (2.5 Flash)** to analyze lead context and generate hyper-personalized, non-spammy email copy referencing the lead's exact business details or current ad topics.
- 📧 **Automated Dispatching:** Built-in integration with the **Resend API** allows the system to fire emails directly to the prospects from your company domains the moment a pitch is verified.
- ⚡ **High-Performance Backend:** Built entirely on **FastAPI** utilizing modern asynchronous Python, robust type validation (`Pydantic`), and secure JWT based authentication for API security.

---

## 🛠️ Tech Stack & Dependencies

- **Language:** Python 3.11+
- **Framework:** FastAPI, Uvicorn
- **AI / LLM Orchestration:** `openai-agents` wrapper over Google Gemini
- **Web Scraping:** Apify Client (`apify-client`)
- **Email Delivery:** Resend API (`resend`)
- **Security:** `passlib`, `bcrypt`, JWT Tokens
- **Environment Management:** `uv`, `hatchling`

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/abdulrafay85/facebook_outreach.git
cd facebook_outreach
```

### 2. Environment Setup
It is highly recommended to use `uv` or standard `venv` for dependency management.
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (If using pip)
pip install -r requirements.txt 
```

### 3. API Keys Configuration
Create a `.env` file in the root directory. You will need API credentials for the services that power this automation.
```ini
FB_ACCESS_TOKEN="your_facebook_ads_api_token"
APIFY_API_KEY="your_apify_api_token"
GEMINI_API_KEY="your_google_gemini_api_key"
RESEND_API_KEY="your_resend_api_key"
```

---

## 💻 Usage & Execution

### 1. Start the API Server
Trigger the robust FastAPI backend with live reloading:
```bash
uvicorn src.fb_outreach.app:app --reload
```
The server will boot up at `http://127.0.0.1:8000`. You can visit `http://127.0.0.1:8000/docs` to view the auto-generated Swagger UI.

### 2. The Core Pipeline Flow
The primary endpoint automates the entire sequence. Through the API or custom front-end dashboard:
1. **Fetch:** Provide a set of parameters (e.g., `search_terms="health"`, `limit=5`). The script calls the Facebook Ads API.
2. **Contextualize:** The system identifies valid Facebook Pages and hands them off to Apify.
3. **Draft & Send:** The scraped data (including verified emails) is bundled into a `UserData` object. The *Pitch Agent* processes this context, creates the perfect subject line and copy, and natively interacts with Resend to drop it into the lead's inbox.

---

## ⚠️ Disclaimer
This tool interacts with live API endpoints (Meta/Facebook) and uses automated web scraping. Please ensure your use of this software strictly adheres to Meta's Terms of Service, anti-spam laws (like CAN-SPAM and GDPR), and Apify's acceptable use policies. Use responsibly.

<div align="center">
  <i>Built to revolutionize B2B prospecting.</i>
</div>
