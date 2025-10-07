import json
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from typing import Any
import logging
from fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("config.json not found. Please create it from config.json.example")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config.json: {e}")
        raise

config = load_config()

# Initialize FastMCP server
mcp = FastMCP("PostgreSQL MCP Server")

def get_connection(database: str):
    """Create a database connection"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=database,
            user=config['user'],
            password=config['password'],
            connect_timeout=config.get('query_timeout', 30)
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def is_read_only_query(query: str) -> bool:
    """Check if query is a SELECT statement"""
    query_upper = query.strip().upper()
    # Allow SELECT, SHOW, DESCRIBE, EXPLAIN
    safe_starts = ('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN', 'WITH')
    return query_upper.startswith(safe_starts)

@mcp.tool()
def list_databases() -> dict[str, Any]:
    """
    List all available databases in PostgreSQL server.
    
    Returns a list of database names that can be used with execute_sql.
    """
    try:
        conn = get_connection('postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT datname as database_name 
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        databases = [row['database_name'] for row in results]
        
        return {
            "status": "success",
            "databases": databases,
            "count": len(databases)
        }
        
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return {
            "status": "error",
            "message": str(e),
            "databases": []
        }

@mcp.tool()
def execute_sql(database: str, query: str) -> dict[str, Any]:
    """
    Execute a SQL query on the specified PostgreSQL database.
    
    Args:
        database: Name of the database to connect to (e.g., 'student_exercise_1')
        query: SQL query to execute
    
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - rows: List of result rows (for SELECT queries)
        - row_count: Number of rows affected/returned
        - columns: List of column names
        - message: Status or error message
    
    Examples:
        - List tables: execute_sql('mydb', 'SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\'')
        - Describe table: execute_sql('mydb', 'SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \\'users\\'')
        - Query data: execute_sql('mydb', 'SELECT * FROM users LIMIT 10')
    """
    try:
        # Check read-only mode
        if config.get('read_only', False) and not is_read_only_query(query):
            return {
                "status": "error",
                "message": "Server is in read-only mode. Only SELECT queries are allowed.",
                "rows": [],
                "row_count": 0,
                "columns": []
            }
        
        conn = get_connection(database)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Set statement timeout
        timeout_ms = config.get('query_timeout', 30) * 1000
        cursor.execute(f"SET statement_timeout = {timeout_ms}")
        
        # Execute query
        cursor.execute(query)
        
        # Handle SELECT queries
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            max_rows = config.get('max_rows', 1000)
            rows = cursor.fetchmany(max_rows)
            
            # Convert to list of dicts
            results = [dict(row) for row in rows]
            
            row_count = len(results)
            message = f"Query executed successfully. Returned {row_count} rows."
            
            if cursor.rowcount > max_rows:
                message += f" (Limited to {max_rows} rows)"
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "rows": results,
                "row_count": row_count,
                "columns": columns,
                "message": message
            }
        else:
            # Handle INSERT/UPDATE/DELETE/etc
            conn.commit()
            row_count = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "rows": [],
                "row_count": row_count,
                "columns": [],
                "message": f"Query executed successfully. {row_count} rows affected."
            }
            
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {
            "status": "error",
            "message": f"Database error: {str(e)}",
            "rows": [],
            "row_count": 0,
            "columns": []
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "rows": [],
            "row_count": 0,
            "columns": []
        }

if __name__ == "__main__":
    # Run with SSE transport
    mcp.run(transport='sse')