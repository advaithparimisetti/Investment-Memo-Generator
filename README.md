# 📈 AI Investment Memo Generator (Alpha)

> **"Democratizing Wall Street-grade research for the individual investor."**

![Status](https://img.shields.io/badge/Status-Proof_of_Concept-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Powered By](https://img.shields.io/badge/Powered%20By-Groq_%26_Llama_3-purple)

https://investment-memo-generator.onrender.com/

## 🧐 The Vision
Wall Street hedge funds have armies of analysts, Bloomberg terminals, and proprietary data. The average retail investor has... gut feelings and Reddit.

**The goal of this project is to build an autonomous AI Financial Analyst.**
We want to create a system that can:
1.  **Research:** Scrape the web for the latest news and catalysts.
2.  **Analyze:** Crunch live financial numbers (P/E, Revenue Growth, Margins).
3.  **Synthesize:** Write a professional-grade "Investment Memo" (Buy/Sell/Hold thesis).
4.  **Debate:** Eventually, we want multiple AI agents (a "Bear" and a "Bull") to argue over the stock before giving a final verdict.

---

## 🚧 The Reality (Current State)
This project is currently a **Proof of Concept**. It is functional but raw. I am releasing it early to build in public.

**Known Limitations & Flaws:**
* **Single-Agent View:** Currently, one LLM plays the role of the analyst. It can sometimes be biased or hallucinate numbers.
* **Data Dependency:** We rely on free APIs (Yahoo Finance, DuckDuckGo). If they change their structure or rate-limit us, the analysis might fail.
* **Simple UI:** The interface is a basic HTML/JS dashboard. It looks cool (Cyberpunk style), but lacks interactive charts.
* **No Persistence:** Reports are not saved to a database yet. If you refresh, they are gone.

---

## ✨ Key Features
* **⚡ Blazing Fast:** Powered by **Groq LPU** (Llama 3.3 70B) for near-instant text generation.
* **📊 Live Data:** Fetches real-time stock prices, market cap, and valuation metrics via `yfinance`.
* **🌐 Web Browsing:** Uses `duckduckgo-search` to find recent news, lawsuits, and earnings reports.
* **📄 PDF Export:** automatically formats and downloads a clean, corporate-style PDF memo.
* **🐳 Dockerized:** Runs anywhere with a single command. Zero "it works on my machine" issues.

---

## 🛠️ Tech Stack
* **AI Engine:** [Groq](https://groq.com) (Llama 3.3 70B Versatile)
* **Agent Framework:** [Phidata](https://www.phidata.com)
* **Backend:** Python 3.11, FastAPI, Uvicorn
* **Frontend:** Vanilla HTML/JS (No complex frameworks like React/Vue yet)
* **Tools:** YFinance, DuckDuckGo, ReportLab

---

## 🚀 Getting Started

### Prerequisites
1.  **Docker Desktop** installed on your machine.
2.  A free API Key from **[Groq Console](https://console.groq.com/)**.

### Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/investment-memo-generator.git](https://github.com/YOUR_USERNAME/investment-memo-generator.git)
    cd investment-memo-generator
    ```

2.  **Set up Environment**
    Create a `.env` file in the root directory:
    ```bash
    GROQ_API_KEY=gsk_your_key_here
    ```

3.  **Build & Run (Docker)**
    We use Docker to handle all dependencies automatically.
    ```bash
    # Build the image (use --no-cache to ensure fresh install)
    docker build --no-cache -t investment-memo-generator .

    # Run the app on port 3000
    docker run -p 3000:8000 --env-file .env investment-memo-generator
    ```

4.  **Access the App**
    Open your browser and go to: **[http://localhost:3000](http://localhost:3000)**

---

## 📸 Usage Guide
1.  **Enter Ticker:** Type a valid stock symbol (e.g., `NVDA`, `AAPL`, `RELIANCE.NS`).
2.  **Select Model:** Choose **Llama 3.3 70B** for the best depth, or **Llama 3.1 8B** for speed.
3.  **Initialize Sequence:** Click the button and watch the logs. The AI is searching the web and analyzing data.
4.  **Read & Export:** Once the report loads, click **"EXPORT_MEMO.PDF"** to save it.

---

## 🤝 Contributing
I cannot build this alone. If you are interested in **AI Agents, Finance, or Python**, your help is welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for ideas on what to build next (like technical analysis charts or multi-agent debates).

## 📜 License
MIT License. **Disclaimer:** This tool is for educational purposes only. Do not make financial decisions solely based on AI outputs.
