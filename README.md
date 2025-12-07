# 📈 AI Investment Memo Generator

> **"Democratizing Wall Street-grade research for the individual investor."**

![Status](https://img.shields.io/badge/Status-Prototype-orange)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Powered By](https://img.shields.io/badge/Powered%20By-Llama%203%20%28Groq%29-purple)

## 🧐 The Vision (My Intent)
The goal of this project is ambitious: **To build an autonomous AI financial analyst that rivals human equity research.** Institutional investors have access to armies of analysts and expensive terminals. Retail investors often rely on gut feeling. This tool aims to bridge that gap by using AI Agents to:
1.  Gather real-time market data.
2.  Synthesize news and financials.
3.  Structure a professional "Investment Memo" (Buy/Sell/Hold thesis).
4.  Export it as a clean, corporate-style PDF.

---

## 🚧 The Reality (Current State & Flaws)
**This project is currently a PROOF OF CONCEPT.** It works, but it is far from perfect. I am releasing it now because I believe in building in public.

**Current Limitations / Known Flaws:**
* **Simple UI:** The frontend is a basic Cyberpunk-terminal style interface. It looks cool but lacks advanced charting.
* **Single-Agent Logic:** Currently, one agent does everything. In the future, I want a "Team of Agents" (Fundamental Analyst, Technical Analyst, Risk Manager) debating each other.
* **Data Reliance:** It relies on free APIs (Yahoo Finance, DuckDuckGo). If they rate-limit us, the analysis fails.
* **Hallucinations:** Like all LLMs, the analyst can sometimes be confident but wrong. **Always verify the numbers.**

---

## ✨ Features
- **⚡ Blazing Fast Analysis:** Uses **Groq's LPU** (Llama 3.3 70B) for near-instant inference.
- **📊 Real-Time Data:** Fetches live prices, P/E ratios, and market cap via `yfinance`.
- **🌐 Web Research:** Scrapes the latest news to find catalysts and risks using `duckduckgo-search`.
- **📄 PDF Export:** Generates a downloadable, formatted PDF report automatically.
- **🐳 Dockerized:** Runs anywhere with a single container command.

---

## 🛠️ Tech Stack
* **Core Logic:** Python 3.11, [Phidata](https://www.phidata.com/) (Agent Framework)
* **LLM Engine:** Groq API (Llama 3.3 70B)
* **Backend:** FastAPI, Uvicorn
* **Frontend:** HTML5, CSS3 (Cyberpunk/Terminal Theme), Vanilla JS
* **Tools:** YFinance, DuckDuckGo Search, ReportLab (PDF)

---

## 🚀 Quick Start

### Prerequisites
* Docker Desktop installed.
* A free API Key from [Groq Console](https://console.groq.com/).

### 1. Clone the Repo
```bash
git clone [https://github.com/YOUR_USERNAME/investment-memo-generator.git](https://github.com/YOUR_USERNAME/investment-memo-generator.git)
cd investment-memo-generator
