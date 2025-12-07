from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from phi.agent import Agent
from phi.model.openai import OpenAIChat 
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools import Toolkit
from duckduckgo_search import DDGS
from dotenv import load_dotenv
import os
import io
import re
import warnings
import logging

# ReportLab Imports
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# --- CONFIGURATION ---
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.getLogger("duckduckgo_search").setLevel(logging.ERROR)
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. SEARCH TOOL ---
class RobustSearchTool(Toolkit):
    def __init__(self):
        super().__init__(name="web_search")
        self.register(self.search)

    def search(self, query: str, max_results: int = 5) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return str(results) if results else "No results found."
        except Exception as e:
            return f"Search Error: {e}"

# --- 2. PDF ENGINE ---
class PDFGenerator:
    def __init__(self, buffer):
        self.buffer = buffer
        self.styles = getSampleStyleSheet()
        self.story = []
        self.styles.add(ParagraphStyle(name='MemoTitle', parent=self.styles['Title'], fontSize=24, spaceAfter=20, alignment=TA_CENTER, textColor=colors.darkblue))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10, textColor=colors.black))
        self.styles.add(ParagraphStyle(name='TableCell', parent=self.styles['Normal'], fontSize=9, leading=11))

    def add_header(self, ticker):
        self.story.append(Paragraph(f"Investment Memo: {ticker}", self.styles['MemoTitle']))
        self.story.append(Paragraph("CONFIDENTIAL REPORT", self.styles['Normal']))
        self.story.append(Spacer(1, 12))

    def clean_text(self, text):
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    def build_report(self, markdown_content):
        lines = markdown_content.split('\n')
        for line in lines:
            if not line.strip(): continue
            if line.startswith('###') or line.startswith('##'):
                self.story.append(Paragraph(self.clean_text(line.replace('#', '').strip()), self.styles['SectionHeader']))
            else:
                self.story.append(Paragraph(self.clean_text(line), self.styles['BodyText']))
                self.story.append(Spacer(1, 6))

    def generate(self):
        doc = SimpleDocTemplate(self.buffer, pagesize=LETTER)
        doc.build(self.story)

# --- 3. AGENT FACTORY (STRICT FORMATTING) ---
def get_agent(model_id: str):
    print(f"🤖 Initializing Agent with Model: {model_id}")
    print("⚡ Using Groq Acceleration (Llama 3)...")
    
    model_instance = OpenAIChat(
        id=model_id,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )

    return Agent(
        name="Analyst Advaith",
        model=model_instance,
        tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True, company_news=True), RobustSearchTool()],
        instructions=[
           "You are a Senior Wall Street Equity Research Analyst.",
            "You are writing a confidential, high-stakes Investment Memo.",
            "",
            "### CRITICAL INSTRUCTIONS:",
            "1. **NO CHITCHAT:** Do not start with 'Here is the report' or 'I have analyzed...'. Start directly with the first header.",
            "2. **USE TOOLS:** You MUST use the 'YFinanceTools' or 'web_search' to find the CURRENT stock price, P/E ratio, and recent news. Do not hallucinate numbers.",
            "3. **STRICT FORMAT:** Follow the markdown structure below EXACTLY.",
            "",
            "### REPORT FORMAT:",
            "## 1. Executive Summary",
            "- **Recommendation:** [BUY / SELL / HOLD]",
            "- **Current Price:** [Insert Real Price] | **Target Price:** [Insert Prediction]",
            "- **Thesis:** [Professional summary of why this trade makes sense]",
            "",
            "## 2. Company Overview",
            "[Concise description of the business model and primary revenue streams]",
            "",
            "## 3. Financial Analysis",
            "| Metric | Value | Comment |",
            "| :--- | :--- | :--- |",
            "| **Revenue Growth** | [Value] | [YoY trend] |",
            "| **Profit Margin** | [Value] | [Efficiency check] |",
            "| **P/E Ratio** | [Value] | [vs Industry Avg] |",
            "*(Narrative analysis of the company's financial health)*",
            "",
            "## 4. Key Catalysts",
            "- [Specific upcoming event/product launch]",
            "- [Macro factor helping the company]",
            "",
            "## 5. Investment Risks",
            "- [Risk 1]",
            "- [Risk 2]",
            "",
            "## 6. Conclusion",
            "[Final verdict: Position size suggestion and time horizon]",
            "",
            "### DATA RULES:",
            "- If the ticker is OTC (e.g. MAHMF), assume USD currency.",
            "- If the user implies a foreign market (e.g. Reliance), use the local ticker (RELIANCE.NS) to get INR prices."
            "### CRUCIAL RULES:",
            "1. **CURRENCY CHECK**: If the ticker is OTC (e.g., MAHMF), the price is USD. If the user wants local (e.g., INR), find the domestic ticker (e.g., M_M.NS).",
            "2. **NO HALLUCINATIONS**: If financial data is missing, explicitly state 'Data Unavailable'."
        ],
        show_tool_calls=False,
        markdown=True,
    )

# --- 4. API ENDPOINTS ---
class RequestModel(BaseModel):
    ticker: str
    model: str = "llama-3.3-70b-versatile" 

class PDFRequestModel(BaseModel):
    ticker: str
    content: str

@app.post("/api/analyze")
async def analyze(request: RequestModel):
    try:
        print(f"🚀 Analyzing: {request.ticker} using {request.model}")
        agent = get_agent(request.model)
        prompt = (f"Write a professional Investment Memo for '{request.ticker}'. "
                  f"Follow the STRICT format in your instructions.")
        response = agent.run(prompt, stream=False)
        return {"markdown": response.content}
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf")
async def get_pdf(request: PDFRequestModel):
    try:
        buffer = io.BytesIO()
        pdf = PDFGenerator(buffer)
        pdf.add_header(request.ticker)
        pdf.build_report(request.content)
        pdf.generate()
        return Response(content=buffer.getvalue(), media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")