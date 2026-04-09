<div align="center">
<h1>AI Facebook Outreach Automation</h1>
<p>An end-to-end workflow for B2B lead generation and personalized outreach.</p>
</div>

---

## Overview

Facebook Outreach Automation is a Python-based backend service designed to streamline the sales and marketing workflow for agencies, B2B services, and real estate professionals.

It automates the entire prospecting process — from discovering businesses running targeted Facebook Ads, extracting relevant business data, generating personalized email pitches using AI, and sending those emails automatically.

---

## Core Features

### Targeted Lead Discovery

Integrates with the Facebook Ads API to identify active ad campaigns based on location, date range, and specific industry keywords (e.g., "real estate", "digital marketing").

### Deep Data Extraction

Uses Apify's Facebook Pages Scraper to collect structured business data such as page descriptions, follower counts, emails, website links, and company information.

### AI-Driven Pitch Generation

Generates concise, personalized outreach emails using Google Gemini. The system uses real business context to avoid generic or spam-like messaging.

### Automated Email Dispatching

Supports integration with email services (e.g., Resend API) to automatically send generated pitches to verified leads.

### High-Performance Backend

Built with FastAPI using modern asynchronous Python, strong data validation (Pydantic), and secure authentication practices.

---

## Tech Stack & Dependencies

* **Language:** Python 3.11+
* **Framework:** FastAPI, Uvicorn
* **AI / LLM Orchestration:** openai-agents with Google Gemini
* **Web Scraping:** Apify Client (`apify-client`)
* **Email Delivery:** Resend API (`resend`)
* **Security:** passlib, bcrypt, JWT Tokens
* **Environment Management:** uv, hatchling

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/abdulrafay85/facebook_outreach.git
cd facebook_outreach
```

### 2. Environment Setup

It is recommended to use a virtual environment.

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
source .venv/bin/activate      # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. API Keys Configuration

Create a `.env` file in the root directory and add the following:

```env
FB_ACCESS_TOKEN="your_facebook_ads_api_token"
APIFY_API_KEY="your_apify_api_token"
GEMINI_API_KEY="your_google_gemini_api_key"
RESEND_API_KEY="your_resend_api_key"
```

---

## Usage & Execution

### 1. Start the API Server

```bash
uvicorn src.fb_outreach.app:app --reload
```

* Server: http://127.0.0.1:8000
* API Docs: http://127.0.0.1:8000/docs

---

### 2. Core Pipeline Flow

#### Fetch

Provide parameters such as `search_terms` and `limit`. The system queries the Facebook Ads API.

#### Contextualize

Relevant Facebook Pages are identified and processed using Apify to extract detailed business information.

#### Draft & Send

The extracted data is structured and passed to the AI Pitch Agent, which generates a personalized email. The system can then send the email using the configured email service.

---

## Disclaimer

This tool interacts with external APIs (Meta/Facebook) and uses automated scraping. Ensure compliance with platform policies, anti-spam regulations (e.g., CAN-SPAM, GDPR), and Apify usage guidelines.

Use responsibly.

---

## Summary

Built for scalable and automated B2B outreach.


