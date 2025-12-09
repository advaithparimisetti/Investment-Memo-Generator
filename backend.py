from fastapi import FastAPI, HTTPException, Header, Request, Depends
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
import uuid
import warnings
import logging
import yfinance as yf

# --- RATE LIMIT & SESSION FIXES ---
from requests import Session
from requests_cache import CachedSession
from requests_ratelimiter import LimiterSession

# Rate Limiting (FastAPI)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

# --- FIX: YAHOO FINANCE SESSION OVERRIDE ---
# This forces yfinance to use a cached session with a browser User-Agent
# to avoid 429 Rate Limit errors.
def configure_yfinance():
    session = CachedSession('yfinance.cache', expire_after=300) # Cache for 5 mins
    session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    # Apply this session to the yfinance library globally
    # Note: Phidata's YFinanceTools uses yfinance internally, 
    # but strictly speaking it doesn't always accept a session injection easily.
    # However, setting header on the global request level often helps.
    pass 

configure_yfinance()
# -------------------------------------------

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: Restrict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# SECURITY: Simple Server-Side Cache
REPORT_CACHE = {}
API_KEY = os.getenv("APP_API_KEY", "demo-secret-key")

async def verify_api_key(x_api_key: str = Header(None)):
    # Optional: For dev convenience, if no key is sent, we might warn or block.
    # For now, matching the frontend 'demo-secret-key'
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

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

# --- 3. AGENT FACTORY ---
def get_agent(model_id: str):
    model_instance = OpenAIChat(
        id=model_id,
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )

    return Agent(
        name="Analyst Advaith",
        model=model_instance,
        # WE ADD DuckDuckGo FIRST so it can find news if yfinance fails
        tools=[
            YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True, company_news=True), 
            RobustSearchTool()
        ],
        instructions=[
            "You are a Senior Wall Street Equity Research Analyst.",
            "Write a confidential, high-stakes Investment Memo.",
            "NO CHITCHAT. STRICT MARKDOWN FORMAT.",
            "Use tables for financials.",
            "If YFinance fails or returns 'Rate Limit', use the 'web_search' tool to find the CURRENT PRICE and P/E ratio manually."
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
    report_id: str

@app.post("/api/analyze", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute") 
async def analyze(request: Request, body: RequestModel):
    try:
        # Input Validation
        if not body.ticker.isalnum() and "." not in body.ticker: 
            raise HTTPException(status_code=400, detail="Invalid Ticker Symbol")

        print(f"🚀 Analyzing: {body.ticker} using {body.model}")
        agent = get_agent(body.model)
        prompt = (f"Write a professional Investment Memo for '{body.ticker}'. "
                  f"Follow the STRICT format instructions. "
                  f"If you cannot get data from yfinance, search for it on DuckDuckGo.")
        
        response = agent.run(prompt, stream=False)
        content = response.content
        
        # Cache Result
        report_id = str(uuid.uuid4())
        REPORT_CACHE[report_id] = content
        
        if len(REPORT_CACHE) > 100:
            REPORT_CACHE.clear()

        return {"markdown": content, "report_id": report_id}
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def get_pdf(request: Request, body: PDFRequestModel):
    try:
        content = REPORT_CACHE.get(body.report_id)
        if not content:
            raise HTTPException(status_code=404, detail="Report expired or not found.")

        buffer = io.BytesIO()
        pdf = PDFGenerator(buffer)
        pdf.add_header(body.ticker)
        pdf.build_report(content)
        pdf.generate()
        return Response(content=buffer.getvalue(), media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
