# postgresql_mcp_lite
Small MCP server to access postgresql - not for production 

by Marc Alier

# PostgreSQL MCP Server

FastMCP server for executing SQL queries on PostgreSQL databases. Designed for evaluating student database projects.

## Features

- **SSE Transport**: Server-Sent Events for MCP communication
- **Multi-Database Support**: Execute queries on different student databases
- **Read-Only Mode**: Optional restriction to SELECT queries only
- **Query Timeout**: Automatic timeout for long-running queries
- **Row Limiting**: Prevents returning too many rows

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create configuration file:
```bash
cp config.json.example config.json
```

3. Edit `config.json` with your PostgreSQL credentials:
```json
{
  "host": "localhost",
  "port": 5432,
  "user": "evaluator",
  "password": "your_password",
  "read_only": true,
  "query_timeout": 30,
  "max_rows": 1000
}
```

## Configuration Options

- `host`: PostgreSQL server hostname
- `port`: PostgreSQL server port (default: 5432)
- `user`: Database user for connections
- `password`: Database password
- `read_only`: If `true`, only SELECT queries are allowed (default: true)
- `query_timeout`: Maximum query execution time in seconds (default: 30)
- `max_rows`: Maximum number of rows to return (default: 1000)

## Running the Server

```bash
python server.py
```

The server will start with SSE transport, ready to accept MCP connections.

## Available Tools

### 1. list_databases()

Lists all available databases on the PostgreSQL server.

**Returns:**
```json
{
  "status": "success",
  "databases": ["postgres", "student_db1", "student_db2"],
  "count": 3
}
```

### 2. execute_sql(database, query)

Execute a SQL query on a specific database.

**Parameters:**
- `database` (str): Name of the database to connect to
- `query` (str): SQL query to execute

**Returns:**
```json
{
  "status": "success",
  "rows": [...],
  "row_count": 10,
  "columns": ["id", "name", "email"],
  "message": "Query executed successfully. Returned 10 rows."
}
```

## Example Queries

### List all tables in a database:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
```

### Describe a table structure:
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'users'
```

### Query data:
```sql
SELECT * FROM students WHERE grade >= 90
```

## Security Notes

⚠️ **This server is intended for educational/evaluation purposes only, not for production use.**

- Set `read_only: true` to prevent data modifications
- Use a dedicated PostgreSQL user with limited privileges
- Consider network restrictions (firewall, localhost-only access)
- Review queries in logs for suspicious activity

## Connecting with MCP Clients

Configure your MCP client (like Claude Desktop) to connect to this server via SSE transport. The server exposes two tools that can be used to explore and query student databases.

## Troubleshooting

**Connection refused:**
- Check PostgreSQL is running: `pg_isready`
- Verify host/port in config.json
- Check PostgreSQL accepts connections (pg_hba.conf)

**Authentication failed:**
- Verify username/password in config.json
- Check user has CONNECT privilege on databases

**Permission denied:**
- Ensure user has SELECT (and other) permissions on target databases
- Grant necessary privileges: `GRANT CONNECT ON DATABASE student_db TO evaluator;`

## License

For educational use.