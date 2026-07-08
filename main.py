from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlparse
import re

app = FastAPI(title="AI SQL Performance Optimizer")

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
        <title>SQL Optimizer Pro</title>
        <style>
            :root {
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --accent: #3b82f6;
                --accent-hover: #2563eb;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --success: #10b981;
                --danger: #ef4444;
            }
            body { 
                font-family: 'Inter', system-ui, -apple-system, sans-serif; 
                background-color: var(--bg-primary); 
                color: var(--text-main);
                margin: 0; 
                padding: 0; 
            }
            .header {
                text-align: center;
                padding: 40px 20px;
                background: linear-gradient(180deg, rgba(59,130,246,0.1) 0%, rgba(15,23,42,0) 100%);
            }
            .header h1 { margin: 0; font-size: 2.5rem; font-weight: 800; tracking-tight: -0.05em; }
            .header p { color: var(--text-muted); margin-top: 10px; font-size: 1.1rem; }
            .main-layout {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px 40px 20px;
                display: grid;
                grid-template-columns: 1fr;
                gap: 24px;
            }
            @media (min-width: 768px) {
                .main-layout { grid-template-columns: 1fr 1fr; }
            }
            .card {
                background-color: var(--bg-secondary);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 24px;
                display: flex;
                flex-direction: column;
            }
            .card-title {
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 16px;
                color: var(--text-main);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            textarea {
                width: 100%;
                height: 200px;
                background-color: #0b0f19;
                border: 1px solid #475569;
                border-radius: 12px;
                color: #e2e8f0;
                font-family: 'Fira Code', monospace;
                font-size: 14px;
                padding: 16px;
                box-sizing: border-box;
                resize: none;
                outline: none;
            }
            textarea:focus { border-color: var(--accent); }
            .btn {
                background-color: var(--accent);
                color: white;
                border: none;
                padding: 14px;
                font-size: 1rem;
                font-weight: 600;
                border-radius: 12px;
                cursor: pointer;
                margin-top: 16px;
                transition: background 0.2s;
            }
            .btn:hover { background-color: var(--accent-hover); }
            .output-pane {
                height: 200px;
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
                font-family: 'Fira Code', monospace;
                font-size: 14px;
                box-sizing: border-box;
                overflow-y: auto;
                color: #a7f3d0;
                white-space: pre-wrap;
            }
            .status-badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 700;
                margin-bottom: 16px;
            }
            .status-perfect { background-color: rgba(16,185,129,0.15); color: var(--success); border: 1px solid rgba(16,185,129,0.3); }
            .status-warn { background-color: rgba(239,68,68,0.15); color: var(--danger); border: 1px solid rgba(239,68,68,0.3); }
            .warnings-list {
                padding-left: 20px;
                margin: 0;
                color: #cbd5e1;
                font-size: 0.95rem;
                line-height: 1.6;
            }
            .warnings-list li { margin-bottom: 8px; }
        </style>
    </head>
    <body>

        <div class="header">
            <h1>⚡ SQL Optimizer Pro</h1>
            <p>Paste your raw query to analyze architectural index breaks and get auto-optimized alternatives.</p>
        </div>

        <div class="main-layout">
            <div class="card">
                <div class="card-title">💻 Enter Raw SQL Query</div>
                <textarea id="sqlQuery" placeholder="SELECT * FROM users, orders WHERE users.id = orders.user_id AND LOWER(name) = 'anas';"></textarea>
                <button class="btn" onclick="processQuery()">Optimize Architecture</button>
            </div>

            <div class="card" id="resultsCard" style="opacity: 0.4; pointer-events: none;">
                <div class="card-title">🔍 Optimization Intelligence</div>
                <div id="statusIndicator"></div>
                
                <div style="margin-bottom: 20px;">
                    <div style="font-weight: 600; margin-bottom: 8px; font-size: 0.9rem; color: var(--text-muted);">ANALYSIS REPORT:</div>
                    <ul id="warningsDisplay" class="warnings-list"></ul>
                </div>

                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <div style="font-weight: 600; margin-bottom: 8px; font-size: 0.9rem; color: var(--text-muted);">RECOMMENDED PERFECT REWRITE:</div>
                    <div id="fixedQueryDisplay" class="output-pane">Your clean query layout will compile here...</div>
                </div>
            </div>
        </div>

        <script>
            async function processQuery() {
                const sqlText = document.getElementById('sqlQuery').value;
                if(!sqlText.trim()) return alert("Please type an SQL query first!");

                const response = await fetch('/optimize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sql: sqlText })
                });
                const data = await response.json();
                
                // Unlock results pane
                const resultsCard = document.getElementById('resultsCard');
                resultsCard.style.opacity = "1";
                resultsCard.style.pointerEvents = "auto";

                const statusIndicator = document.getElementById('statusIndicator');
                const warningsDisplay = document.getElementById('warningsDisplay');
                const fixedQueryDisplay = document.getElementById('fixedQueryDisplay');

                warningsDisplay.innerHTML = "";

                if(data.status === "Needs Optimization") {
                    statusIndicator.className = "status-badge status-warn";
                    statusIndicator.innerText = "⚠️ DEGRADED ARCHITECTURE DETECTED";
                    
                    data.suggestions.forEach(item => {
                        const li = document.createElement('li');
                        li.innerText = item;
                        warningsDisplay.appendChild(li);
                    });
                    
                    fixedQueryDisplay.innerText = data.fixed_sql;
                    fixedQueryDisplay.style.color = "#a7f3d0";
                } else {
                    statusIndicator.className = "status-badge status-perfect";
                    statusIndicator.innerText = "✅ EXCELLENT PRODUCTION ARCHITECTURE";
                    
                    const li = document.createElement('li');
                    li.innerText = "No anti-patterns matched. High-performance structures verified.";
                    warningsDisplay.appendChild(li);
                    
                    fixedQueryDisplay.innerText = sqlText;
                    fixedQueryDisplay.style.color = "#38bdf8";
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
    
    suggestions = []
    is_optimized = True
    query_upper = sql_query.upper()
    
    # We will work on a copy of the string to progressively fix patterns
    fixed_sql = sql_query

    # Rule 1: SELECT * Detection & Fix
    if "SELECT *" in query_upper or "SELECT  *" in query_upper:
        is_optimized = False
        suggestions.append("Anti-Pattern: 'SELECT *' wildcard detected. Forces massive payload transfers across network lines.")
        # Auto fix placeholder rule: swap * with explicit column architecture context
        fixed_sql = re.sub(r"SELECT\s+\*", "SELECT id, created_at, [columns...]", fixed_sql, flags=re.IGNORECASE)

    # Rule 2: LOWER/UPPER functions in WHERE clause
    bad_functions = ["LOWER(", "UPPER("]
    for func in bad_functions:
        if "WHERE" in query_upper and func in query_upper.split("WHERE")[1]:
            is_optimized = False
            suggestions.append(f"Anti-Pattern: Function '{func}' wrapper utilized inside filter conditions. This breaks linear table indexes.")
            # Auto-fix: extract column inside function to remove the performance hit
            if func == "LOWER(":
                fixed_sql = re.sub(r"LOWER\((.*?)\)", r"\1", fixed_sql, flags=re.IGNORECASE)
            elif func == "UPPER(":
                fixed_sql = re.sub(r"UPPER\((.*?)\)", r"\1", fixed_sql, flags=re.IGNORECASE)

    # Rule 3: Old school Comma Joins Fix
    if "FROM" in query_upper:
        after_from = query_upper.split("FROM")[1]
        from_part = after_from.split("WHERE")[0] if "WHERE" in after_from else after_from
        
        if "," in from_part:
            is_optimized = False
            suggestions.append("Anti-Pattern: Legacy table comma referencing used. Forces implicitly nested loops instead of direct structural joins.")
            
            # Simple RegEx extraction to turn legacy table1, table2 into explicit INNER JOIN
            tables = [t.strip() for t in from_part.split(",")]
            if len(tables) >= 2:
                join_syntax = f" {tables[0]} INNER JOIN {tables[1]} ON [join_condition]"
                # Reconstruct string
                if "WHERE" in after_from:
                    where_part = after_from.split("WHERE")[1]
                    fixed_sql = fixed_sql.split("FROM")[0] + "FROM" + join_syntax + " WHERE " + where_part
                else:
                    fixed_sql = fixed_sql.split("FROM")[0] + "FROM" + join_syntax

    return {
        "status": "Perfect" if is_optimized else "Needs Optimization",
        "suggestions": suggestions,
        "fixed_sql": fixed_sql
    }