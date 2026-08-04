import sqlparse
from sqlparse.tokens import Wildcard, Keyword

def analyze_and_optimize_query(sql_query: str):
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {"error": "Invalid SQL query"}
    
    statement = parsed[0]
    suggestions = []
    is_optimized = True
    
    # Convert query to uppercase just for text scanning rules
    query_upper = sql_query.upper()

    # RULE 1: Check for SELECT *
    for token in statement.tokens:
        if token.ttype is Wildcard and token.value == '*':
            is_optimized = False
            suggestions.append("❌ Anti-Pattern: 'SELECT *' found. Suggestion: Explicitly name your columns to save memory and network bandwidth.")
            break

    # RULE 2: Check for Non-Sargable functions in WHERE clause
    # Common performance-killing functions used inside WHERE clauses
    bad_where_functions = ["UPPER(", "LOWER(", "DATE(", "YEAR("]
    
    if "WHERE" in query_upper:
        where_part = query_upper.split("WHERE")[1]
        for func in bad_where_functions:
            if func in where_part:
                is_optimized = False
                suggestions.append(f"❌ Anti-Pattern: Found function '{func}' inside the WHERE clause. This destroys database index performance. Suggestion: Rewrite the query to isolate the raw column.")

    return {
        "status": "Needs Optimization" if not is_optimized else "Perfect",
        "suggestions": suggestions
    }

if __name__ == "__main__":
    # Let's test a brutally slow query written by a developer
    bad_developer_query = "SELECT * FROM employees WHERE UPPER(first_name) = 'ANAS';"
    
    print("\n--- Testing Upgraded Startup Engine ---")
    result = analyze_and_optimize_query(bad_developer_query)
    print(f"Product Status: {result['status']}\n")
    for hint in result['suggestions']:
        print(hint)