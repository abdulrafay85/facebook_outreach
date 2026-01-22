# Facebook Outreach

**Automating targeted outreach on Facebook for marketing and sales.**

This project provides a set of tools to automate the process of finding and contacting potential customers on Facebook. It uses Apify for scraping Facebook pages and provides a simple web interface to manage outreach campaigns.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/abdulrafay85/facebook_outreach.git
    cd facebook_outreach
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    pip install -r requirements.txt 
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root directory and add the following:
    ```
    APIFY_API_TOKEN=your_apify_api_token
    ```

## Usage

1.  **Run the application:**
    ```bash
    uvicorn src.fb_outreach.app:app --reload
    ```

2.  **Access the web interface:**
    Open your browser and navigate to `http://12f7.0.0.1:8000`.

3.  **Start an outreach campaign:**
    -   Go to the "Pages" section to find Facebook pages based on a search query.
    -   Select the pages you want to target.
    -   Go to the "Ads" section to create and manage your outreach campaigns.
