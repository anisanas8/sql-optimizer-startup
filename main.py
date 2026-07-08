from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlparse

app = FastAPI(title="SQL Optimizer & Global Search API")

class QueryInput(BaseModel):
    sql: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TechHub: SQL Optimizer & Global Search</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; }
            .navbar { background-color: #1e293b; padding: 15px; text-align: center; }
            .navbar button { background: none; border: none; color: white; font-size: 16px; margin: 0 15px; cursor: pointer; padding: 5px 10px; font-weight: 600; }
            .navbar button.active { border-bottom: 2px solid #3b82f6; color: #3b82f6; }
            .container { max-width: 800px; margin: 40px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1 { color: #1e293b; text-align: center; }
            textarea { width: 100%; height: 120px; padding: 15px; border: 2px solid #e2e8f0; border-radius: 8px; font-family: monospace; font-size: 14px; box-sizing: border-box; }
            button.main-btn { background-color: #2563eb; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 10px; }
            .result-box { margin-top: 25px; padding: 20px; border-radius: 8px; display: none; }
            .needs-opt { background-color: #fef2f2; border: 1px solid #fee2e2; }
            .perfect { background-color: #f0fdf4; border: 1px solid #dcfce7; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            /* Google Search Styling */
            .google-box { text-align: center; margin-top: 50px; }
            .google-logo { font-size: 40px; font-weight: bold; margin-bottom: 20px; }
            .google-logo span:nth-child(1) { color: #4285F4; }
            .google-logo span:nth-child(2) { color: #EA4335; }
            .google-logo span:nth-child(3) { color: #FBBC05; }
            .google-logo span:nth-child(4) { color: #4285F4; }
            .google-logo span:nth-child(5) { color: #34A853; }
            .google-logo span:nth-child(6) { color: #EA4335; }
            .search-results { margin-top: 30px; text-align: left; }
        </style>
    </head>
    <body>

        <div class="navbar">
            <button id="optTabBtn" class="active" onclick="switchTab('optimizer')">SQL Optimizer</button>
            <button id="searchTabBtn" onclick="switchTab('search')">Global Web Search</button>
        </div>

        <div id="optimizerTab" class="container tab-content active">
            <h1>⚡ AI SQL Optimizer</h1>
            <textarea id="sqlQuery" placeholder="SELECT * FROM users WHERE name LIKE '%ANAS';"></textarea>
            <button class="main-btn" onclick="optimizeQuery()">Analyze Query</button>
            <div id="resultBox" class="result-box">
                <div id="resultTitle" style="font-weight:bold; font-size:18px;"></div>
                <ul id="suggestionsList" style="padding-left:20px; margin-top:10px;"></ul>
            </div>
        </div>

        <div id="searchTab" class="container tab-content">
            <div class="google-box">
                <div class="google-logo">
                    <span>G</span><span>o</span><span>o</span><span>g</span><span>l</span><span>e</span> Search
                </div>
                <script async src="https://cse.google.com/cse.js?cx=partner-pub-2698861878625466:9903901768"></script>
                <div class="gcse-search"></div>
            </div>
        </div>

        <script>
            function switchTab(tabName) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.navbar button').forEach(el => el.classList.remove('active'));
                
                if(tabName === 'optimizer') {
                    document.getElementById('optimizerTab').classList.add('active');
                    document.getElementById('optTabBtn').classList.add('active');
                } else {
                    document.getElementById('searchTab').classList.add('active');
                    document.getElementById('searchTabBtn').classList.add('active');
                }
            }

            async function optimizeQuery() {
                const sqlText = document.getElementById('sqlQuery').value;
                const resultBox = document.getElementById('resultBox');
                const resultTitle = document.getElementById('resultTitle');
                const suggestionsList = document.getElementById('suggestionsList');
                if(!sqlText.trim()) return alert("Please type code first!");

                const response = await fetch('/optimize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql: sqlText })
                });
                const data = await response.json();
                resultBox.style.display = "block";
                suggestionsList.innerHTML = "";
                
                if(data.status === "Needs Optimization") {
                    resultBox.className = "result-box needs-opt";
                    resultTitle.innerHTML = "⚠️ Optimization Warnings Found!";
                    resultTitle.style.color = "#dc2626";
                    data.suggestions.forEach(item => {
                        const li = document.createElement('li');
                        li.innerText = item;
                        suggestionsList.appendChild(li);
                    });
                } else {
                    resultBox.className = "result-box perfect";
                    resultTitle.innerHTML = "✅ Structure looks clean and optimized!";
                    resultTitle.style.color = "#16a34a";
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/optimize")
def optimize_endpoint(input_data: QueryInput):
    sql_query = input_data.sql
    parsed = sqlparse.parse(sql_query)
    if not parsed: return {"error": "Invalid query"}
    statement = parsed[0]
    suggestions = []
    is_optimized = True
    query_upper = sql_query.upper()

    # Rule 1
    for token in statement.tokens:
        if token.ttype is sqlparse.tokens.Wildcard and token.value == '*':
            is_optimized = False
            suggestions.append("❌ Anti-Pattern: 'SELECT *' found. Explicitly list required columns.")
            break

    # Rule 2
    bad_where_functions = ["UPPER(", "LOWER(", "DATE("]
    if "WHERE" in query_upper:
        where_part = query_upper.split("WHERE")[1]
        for func in bad_where_functions:
            if func in where_part:
                is_optimized = False
                suggestions.append(f"❌ Anti-Pattern: Found function '{func}' in WHERE clause. Breaks table indexes.")

    return {
        "status": "Perfect" if is_optimized else "Needs Optimization",
        "suggestions": suggestions
    }