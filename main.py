import re
from typing import List, Optional
 
import sqlparse
from sqlparse.sql import Where
from sqlparse.tokens import Keyword, DML
 
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
 
app = FastAPI(title="AI SQL Performance Optimizer")
 
 
class QueryInput(BaseModel):
    sql: str = Field(..., min_length=1, description="Raw SQL query to analyze")
 
 
# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
 
CLAUSE_STOP_KEYWORDS = {
    "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "UNION",
    "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN",
    "LEFT OUTER JOIN", "RIGHT OUTER JOIN",
}
 
 
def split_top_level(text: str, sep: str = ",") -> List[str]:
    """Split `text` on `sep`, but only at paren-depth 0, so commas inside
    function calls / subqueries / IN (...) lists are not treated as
    top-level separators."""
    parts, current, depth = [], "", 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    parts.append(current)
    return [p.strip() for p in parts if p.strip()]
 
 
def get_where_clause(statement) -> Optional[str]:
    """Return the text of the top-level WHERE clause (including the WHERE
    keyword), or None if there isn't one. Uses sqlparse's grouping, so it
    won't get confused by WHERE keywords inside subqueries."""
    for token in statement.tokens:
        if isinstance(token, Where):
            return str(token)
    return None
 
 
def get_from_clause(statement) -> Optional[str]:
    """Return the text between the top-level FROM keyword and the next
    clause boundary (WHERE / JOIN / GROUP BY / ... / end of statement)."""
    tokens = [t for t in statement.flatten()] if False else list(statement.tokens)
    collecting = False
    collected = []
    for token in tokens:
        val_upper = token.value.strip().upper() if token.value else ""
        if not collecting:
            if token.ttype is Keyword and val_upper == "FROM":
                collecting = True
            continue
        # Stop at the next clause-level keyword (JOIN, WHERE, GROUP BY, ...)
        if (token.ttype is Keyword or isinstance(token, Where)) and any(
            val_upper == kw or val_upper.startswith(kw + " ") for kw in CLAUSE_STOP_KEYWORDS
        ):
            break
        if isinstance(token, Where):
            break
        collected.append(str(token))
    if not collecting:
        return None
    return "".join(collected).strip() or None
 
 
# --------------------------------------------------------------------------
# Frontend (unchanged design, only the JS/CSS from the original)
# --------------------------------------------------------------------------
 
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
            .header h1 { margin: 0; font-size: 2.5rem; font-weight: 800; }
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
            .btn:disabled { opacity: 0.6; cursor: not-allowed; }
            .btn:hover:not(:disabled) { background-color: var(--accent-hover); }
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
            .status-error { background-color: rgba(239,68,68,0.25); color: #fecaca; border: 1px solid rgba(239,68,68,0.5); }
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
                <button class="btn" id="optimizeBtn" onclick="processQuery()">Optimize Architecture</button>
            </div>
 
            <div class="card" id="resultsCard" style="opacity: 0.4; pointer-events: none;">
                <div class="card-title">🔍 Optimization Intelligence</div>
                <div id="statusIndicator"></div>
 
                <div style="margin-bottom: 20px;">
                    <div style="font-weight: 600; margin-bottom: 8px; font-size: 0.9rem; color: var(--text-muted);">ANALYSIS REPORT:</div>
                    <ul id="warningsDisplay" class="warnings-list"></ul>
                </div>
 
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <div style="font-weight: 600; margin-bottom: 8px; font-size: 0.9rem; color: var(--text-muted);">RECOMMENDED REWRITE:</div>
                    <div id="fixedQueryDisplay" class="output-pane">Your clean query layout will compile here...</div>
                </div>
            </div>
        </div>
 
        <script>
            async function processQuery() {
                const sqlText = document.getElementById('sqlQuery').value;
                if(!sqlText.trim()) return alert("Please type an SQL query first!");
 
                const btn = document.getElementById('optimizeBtn');
                btn.disabled = true;
                btn.innerText = "Analyzing...";
 
                const resultsCard = document.getElementById('resultsCard');
                const statusIndicator = document.getElementById('statusIndicator');
                const warningsDisplay = document.getElementById('warningsDisplay');
                const fixedQueryDisplay = document.getElementById('fixedQueryDisplay');
 
                try {
                    const response = await fetch('/optimize', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sql: sqlText })
                    });
 
                    resultsCard.style.opacity = "1";
                    resultsCard.style.pointerEvents = "auto";
                    warningsDisplay.innerHTML = "";
 
                    if (!response.ok) {
                        const err = await response.json().catch(() => ({detail: "Unknown error"}));
                        statusIndicator.className = "status-badge status-error";
                        statusIndicator.innerText = "❌ COULD NOT PARSE QUERY";
                        const li = document.createElement('li');
                        li.innerText = err.detail || "The query could not be analyzed.";
                        warningsDisplay.appendChild(li);
                        fixedQueryDisplay.innerText = "";
                        return;
                    }
 
                    const data = await response.json();
 
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
                        statusIndicator.innerText = "✅ NO ANTI-PATTERNS DETECTED";
 
                        const li = document.createElement('li');
                        li.innerText = "No anti-patterns matched by current rule set.";
                        warningsDisplay.appendChild(li);
 
                        fixedQueryDisplay.innerText = sqlText;
                        fixedQueryDisplay.style.color = "#38bdf8";
                    }
                } catch (e) {
                    statusIndicator.className = "status-badge status-error";
                    statusIndicator.innerText = "❌ REQUEST FAILED";
                    warningsDisplay.innerHTML = "<li>Network or server error. Please try again.</li>";
                } finally {
                    btn.disabled = false;
                    btn.innerText = "Optimize Architecture";
                }
            }
        </script>
    </body>
    </html>
    """
 
 
# --------------------------------------------------------------------------
# Optimization endpoint
# --------------------------------------------------------------------------
 
@app.post("/optimize")
def optimize_endpoint(input_data: QueryInput):
    raw_sql = input_data.sql.strip()
    if not raw_sql:
        raise HTTPException(status_code=400, detail="Empty query provided.")
 
    try:
        statements = sqlparse.parse(raw_sql)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse SQL query.")
 
    if not statements or not any(str(s).strip() for s in statements):
        raise HTTPException(status_code=400, detail="Invalid or empty SQL query.")
 
    suggestions: List[str] = []
    is_optimized = True
    fixed_sql = raw_sql
 
    if len(statements) > 1:
        suggestions.append(
            "Multiple statements detected — only the first statement was analyzed."
        )
 
    statement = statements[0]
    stmt_type = statement.get_type()  # e.g. SELECT, UPDATE, DELETE, UNKNOWN
    query_upper = str(statement).upper()
 
    where_clause = get_where_clause(statement)
    from_clause = get_from_clause(statement)
 
    # --- Rule 1: SELECT * -------------------------------------------------
    if re.search(r"SELECT\s+\*", query_upper) and "COUNT(*)" not in query_upper.replace(" ", ""):
        is_optimized = False
        suggestions.append(
            "Anti-Pattern: 'SELECT *' wildcard detected. Forces the database to read and "
            "transfer every column, even ones the application doesn't use, and prevents "
            "covering-index optimizations."
        )
        fixed_sql = re.sub(
            r"SELECT(\s+)\*",
            r"SELECT\1/* TODO: replace * with only the columns you actually need */ *",
            fixed_sql,
            count=1,
            flags=re.IGNORECASE,
        )
 
    # --- Rule 2: LOWER()/UPPER() wrapped around a WHERE-clause column -----
    if where_clause:
        for func in ("LOWER(", "UPPER("):
            if func in where_clause.upper():
                is_optimized = False
                suggestions.append(
                    f"Anti-Pattern: '{func.rstrip('(')}' wraps a column inside the WHERE clause. "
                    "This prevents the database from using a standard B-tree index on that column "
                    "(a functional/expression index would be required instead)."
                )
                # Scope the fix to the WHERE clause text only, then splice it
                # back into fixed_sql, so a same-named function used in the
                # SELECT list is left untouched.
                pattern = re.compile(re.escape(func[:-1]) + r"\((.*?)\)", re.IGNORECASE)
                fixed_where = pattern.sub(r"\1", where_clause)
                fixed_sql = fixed_sql.replace(where_clause, fixed_where, 1)
 
    # --- Rule 3: legacy comma joins in FROM --------------------------------
    if from_clause and "," in split_top_level(from_clause, ",")[0] + "," if False else False:
        pass  # placeholder to keep linters happy; real check below
 
    if from_clause:
        top_level_tables = split_top_level(from_clause, ",")
        if len(top_level_tables) >= 2:
            is_optimized = False
            suggestions.append(
                "Anti-Pattern: legacy comma-separated table list in FROM. This creates an "
                "implicit CROSS JOIN and relies entirely on the WHERE clause to filter the "
                "resulting cartesian product — easy to get wrong and harder for the query "
                "planner to optimize than an explicit JOIN."
            )
            join_syntax = top_level_tables[0]
            for tbl in top_level_tables[1:]:
                join_syntax += f" INNER JOIN {tbl} ON [join_condition]"
            fixed_sql = fixed_sql.replace(from_clause, join_syntax, 1)
 
    # --- Rule 4: leading wildcard LIKE ('%...') ---------------------------
    if where_clause and re.search(r"LIKE\s+'%", where_clause, re.IGNORECASE):
        is_optimized = False
        suggestions.append(
            "Anti-Pattern: LIKE pattern starts with a leading '%'. A leading wildcard "
            "cannot use a standard B-tree index and forces a full table/index scan. "
            "Consider a trailing-wildcard pattern, full-text search, or a trigram index."
        )
 
    # --- Rule 5: ORDER BY RAND()/NEWID() -----------------------------------
    if re.search(r"ORDER BY\s+(RAND|RANDOM|NEWID)\s*\(", query_upper):
        is_optimized = False
        suggestions.append(
            "Anti-Pattern: 'ORDER BY RAND()' (or equivalent) forces the database to "
            "generate a random value for and sort every matching row before returning "
            "any results — extremely expensive on large tables."
        )
 
    # --- Rule 6: JOIN without any ON/USING/WHERE filter (possible cartesian) --
    if stmt_type == "SELECT" and re.search(r"\bJOIN\b", query_upper) and not where_clause \
            and " ON " not in query_upper and " USING" not in query_upper:
        is_optimized = False
        suggestions.append(
            "Warning: a JOIN was found with no ON/USING condition and no WHERE clause — "
            "double-check this isn't producing an unintended cartesian product."
        )
 
    return {
        "status": "Perfect" if is_optimized else "Needs Optimization",
        "suggestions": suggestions,
        "fixed_sql": fixed_sql,
    }