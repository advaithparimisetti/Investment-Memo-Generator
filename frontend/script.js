let currentMarkdown = "";
let currentTicker = "";
let currentReportId = ""; // NEW: For secure PDF retrieval

// Initialize Clock
setInterval(() => {
    const now = new Date();
    document.getElementById('clock').innerText = now.toISOString().split('T')[1].split('.')[0] + " UTC";
}, 1000);

function handleEnter(e) {
    if (e.key === 'Enter') runAnalysis();
}

async function runAnalysis() {
    const input = document.getElementById('tickerInput');
    const modelSelect = document.getElementById('modelSelect');
    const btn = document.getElementById('execBtn');
    const ticker = input.value.trim().toUpperCase();
    const model = modelSelect.value;

    // Sanitize Input (Basic client-side check)
    if (!ticker || !/^[A-Z0-9\.\-_]+$/.test(ticker)) {
        alert("INVALID TICKER FORMAT");
        return;
    }

    // LOCK UI
    input.disabled = true;
    modelSelect.disabled = true;
    btn.disabled = true;
    btn.innerHTML = "PROCESSING <span class='blink'>...</span>";
    
    // SWITCH SCREENS
    document.getElementById('idleState').classList.add('hidden');
    document.getElementById('resultArea').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');
    
    // UPDATE LOGS
    const logText = document.getElementById('loadingText');
    const logs = ["INITIALIZING " + model + "...", "QUERYING MARKET DATA...", "RUNNING RISK SIMULATIONS...", "SYNTHESIZING MEMO..."];
    let logIdx = 0;
    const logInterval = setInterval(() => {
        logText.innerText = logs[logIdx % logs.length];
        logIdx++;
    }, 1500);

    try {
        currentTicker = ticker;
        
        // 1. ADD API KEY HEADER (Ideally this comes from a secure env or login)
        // For this demo, we assume the backend allows a public 'demo-key' or similar
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'x-api-key': 'demo-secret-key' // Example key
            },
            body: JSON.stringify({ ticker: ticker, model: model })
        });

        if (response.status === 429) throw new Error("Rate Limit Exceeded. Try again later.");
        if (!response.ok) throw new Error("Connection Refused / Error");

        const data = await response.json();
        currentMarkdown = data.markdown;
        currentReportId = data.report_id; // Capture ID for PDF

        // RENDER
        document.getElementById('assetTag').innerText = `// ${ticker}`;
        
        // SECURITY FIX: Sanitize HTML before insertion
        const rawHtml = marked.parse(currentMarkdown);
        const cleanHtml = DOMPurify.sanitize(rawHtml);
        document.getElementById('reportContent').innerHTML = cleanHtml;
        
        clearInterval(logInterval);
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('resultArea').classList.remove('hidden');

    } catch (e) {
        clearInterval(logInterval);
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('idleState').classList.remove('hidden');
        alert("SYSTEM ERROR: " + e.message);
    } finally {
        // UNLOCK UI
        input.disabled = false;
        modelSelect.disabled = false;
        input.value = "";
        input.focus();
        btn.disabled = false;
        btn.innerHTML = "INITIALIZE SEQUENCE";
    }
}

async function downloadPDF() {
    if (!currentReportId) return;

    const btn = document.querySelector('.download-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = "DL_IN_PROGRESS...";
    btn.disabled = true;

    try {
        // SECURITY FIX: Request PDF by ID, not by sending content back
        const response = await fetch('/api/pdf', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'x-api-key': 'demo-secret-key'
            },
            body: JSON.stringify({ ticker: currentTicker, report_id: currentReportId })
        });

        if (!response.ok) throw new Error("PDF Generation Failed");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentTicker}_CLASSIFIED_MEMO.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (e) {
        alert("DOWNLOAD FAILED: " + e.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
