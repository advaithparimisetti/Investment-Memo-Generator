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

# Rate Limiting
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

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: Restrict CORS to specific frontend domain (or localhost for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# SECURITY: Simple Server-Side Cache for Reports (Prevents Reflected PDF Attacks)
# In production, use Redis or a Database.
REPORT_CACHE = {}

# SECURITY: API Key Dependency
API_KEY = os.getenv("APP_API_KEY", "demo-secret-key") # Set this in .env

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
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
        tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True, company_news=True), RobustSearchTool()],
        instructions=[
            "You are a Senior Wall Street Equity Research Analyst.",
            "Write a confidential, high-stakes Investment Memo.",
            "NO CHITCHAT. STRICT MARKDOWN FORMAT.",
            "Use tables for financials."
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
    report_id: str # Changed from 'content' to 'report_id'

@app.post("/api/analyze", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute") # Rate Limit: 5 requests per minute per IP
async def analyze(request: Request, body: RequestModel):
    try:
        # Input Validation
        if not body.ticker.isalnum() and "." not in body.ticker: 
            raise HTTPException(status_code=400, detail="Invalid Ticker Symbol")

        print(f"🚀 Analyzing: {body.ticker} using {body.model}")
        agent = get_agent(body.model)
        prompt = (f"Write a professional Investment Memo for '{body.ticker}'. "
                  f"Follow the STRICT format in your instructions.")
        
        response = agent.run(prompt, stream=False)
        content = response.content
        
        # Cache Result
        report_id = str(uuid.uuid4())
        REPORT_CACHE[report_id] = content
        
        # Clean cache if too big (Basic Memory Management)
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
        # Retrieve content from server-side cache
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
