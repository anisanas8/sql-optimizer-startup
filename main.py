from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlparse

app = FastAPI(title="SQL Optimizer Startup API")

class QueryInput(BaseModel):
    sql: str

# 1. NEW: This serves a beautiful, clean webpage directly to the browser
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <head>
        <meta charset="UTF-8">
        <meta name="google-site-verification" content="TdDLxgeU7UAdSM2IaMOAznO2yIV9S9i1VzbuTidmcGk" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SQL Performance Optimizer</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 40px; color: #333; }
            .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1 { color: #1e293b; margin-top: 0; font-size: 28px; }
            p { color: #64748b; }
            textarea { width: 100%; height: 150px; padding: 15px; border: 2px solid #e2e8f0; border-radius: 8px; font-family: 'Courier New', Courier, monospace; font-size: 14px; box-sizing: border-box; resize: vertical; }
            textarea:focus { border-color: #3b82f6; outline: none; }
            button { background-color: #2563eb; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; margin-top: 15px; width: 100%; transition: background 0.2s; }
            button:hover { background-color: #1d4ed8; }
            .result-box { margin-top: 25px; padding: 20px; border-radius: 8px; display: none; }
            .needs-opt { background-color: #fef2f2; border: 1px solid #fee2e2; }
            .perfect { background-color: #f0fdf4; border: 1px solid #dcfce7; }
            .result-title { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
            ul { padding-left: 20px; margin: 0; }
            li { margin-bottom: 8px; line-height: 1.5; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ AI-Powered SQL Optimizer</h1>
            <p>Paste your slow-running SQL query below to instantly check for performance bottlenecks and indexing issues.</p>
            <textarea id="sqlQuery" placeholder="SELECT * FROM table WHERE column LIKE '%value'"></textarea>
            <button onclick="optimizeQuery()">Analyze Query</button>
            
            <div id="resultBox" class="result-box">
                <div id="resultTitle" class="result-title"></div>
                <ul id="suggestionsList"></ul>
            </div>
        </div>

        <script>
            async function optimizeQuery() {
                const sqlText = document.getElementById('sqlQuery').value;
                const resultBox = document.getElementById('resultBox');
                const resultTitle = document.getElementById('resultTitle');
                const suggestionsList = document.getElementById('suggestionsList');
                
                if(!sqlText.trim()) return alert("Please enter a query first!");

                // Make a live call to your background optimization API endpoint
                const response = await fetch('/optimize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql: sqlText })
                });
                
                const data = await response.json();
                
                // Render the results instantly on the web screen
                resultBox.style.display = "block";
                suggestionsList.innerHTML = "";
                
                if(data.status === "Needs Optimization") {
                    resultBox.className = "result-box needs-opt";
                    resultTitle.innerHTML = "⚠️ Status: Issues Found!";
                    resultTitle.style.color = "#dc2626";
                    data.suggestions.forEach(item => {
                        const li = document.createElement('li');
                        li.innerText = item;
                        suggestionsList.appendChild(li);
                    });
                } else {
                    resultBox.className = "result-box perfect";
                    resultTitle.innerHTML = "✅ Status: Excellent Architecture!";
                    resultTitle.style.color = "#16a34a";
                    const li = document.createElement('li');
                    li.innerText = data.suggestions[0];
                    suggestionsList.appendChild(li);
                }
            }
        </script>
    </body>
    </html>
    """

# 2. Your core operational analysis API engine remains rock solid underneath
@app.post("/optimize")
def optimize_endpoint(input_data: QueryInput):
    sql_query = input_data.sql
    parsed = sqlparse.parse(sql_query)
    
    if not parsed:
        return {"error": "Invalid SQL query"}
    
    statement = parsed[0]
    suggestions = []
    is_optimized = True
    query_upper = sql_query.upper()

    # Rule 1: SELECT *
    for token in statement.tokens:
        if token.ttype is sqlparse.tokens.Wildcard and token.value == '*':
            is_optimized = False
            suggestions.append("❌ Anti-Pattern: 'SELECT *' found. Explicitly name your columns to optimize network memory bandwidth.")
            break

    # Rule 2: Non-Sargable Functions
    bad_where_functions = ["UPPER(", "LOWER(", "DATE(", "YEAR(", "MONTH("]
    if "WHERE" in query_upper:
        where_part = query_upper.split("WHERE")[1]
        for func in bad_where_functions:
            if func in where_part:
                is_optimized = False
                suggestions.append(f"❌ Anti-Pattern: Found function '{func}' inside the WHERE clause. This forces full-table scans by breaking index lookups.")

    # Rule 3: Robust Leading Wildcard Check
    if "LIKE" in query_upper:
        like_parts = query_upper.split("LIKE")[1:]
        for part in like_parts:
            clean_part = part.strip().replace("'", "").replace('"', "")
            if clean_part.startswith("%"):
                is_optimized = False
                suggestions.append("❌ Anti-Pattern: Leading wildcard ('%value') detected in LIKE clause. The database engine cannot use standard B-Tree indexes. Suggestion: Use full-text search indexing.")

    return {
        "status": "Perfect" if is_optimized else "Needs Optimization",
        "suggestions": suggestions if suggestions else ["Your query looks optimized against standard anti-patterns!"]
    }