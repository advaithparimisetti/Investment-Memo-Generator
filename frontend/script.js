let currentMarkdown = "";
let currentTicker = "";

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
    const modelSelect = document.getElementById('modelSelect'); // NEW
    const btn = document.getElementById('execBtn');
    const ticker = input.value.trim().toUpperCase();
    const model = modelSelect.value; // NEW

    if (!ticker) return;

    // LOCK UI
    input.disabled = true;
    modelSelect.disabled = true; // NEW
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
        // SEND MODEL IN REQUEST
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker, model: model })
        });

        if (!response.ok) throw new Error("Connection Refused / Quota Exceeded");

        const data = await response.json();
        currentMarkdown = data.markdown;

        // RENDER
        document.getElementById('assetTag').innerText = `// ${ticker}`;
        document.getElementById('reportContent').innerHTML = marked.parse(currentMarkdown);
        
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
        modelSelect.disabled = false; // NEW
        input.value = "";
        input.focus();
        btn.disabled = false;
        btn.innerHTML = "INITIALIZE SEQUENCE";
    }
}

async function downloadPDF() {
    const btn = document.querySelector('.download-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = "DL_IN_PROGRESS...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: currentTicker, content: currentMarkdown })
        });

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentTicker}_CLASSIFIED_MEMO.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (e) {
        alert("DOWNLOAD FAILED");
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}