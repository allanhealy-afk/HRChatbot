import os
import re
import requests as r
import sqlite3
from dotenv import load_dotenv
import json
import runpy
from pathlib import Path

# Load environment variables once
load_dotenv()

provider = 'gpt-4o-mini'

# Function to check API keys
def check_api_key(api_key, key_name):
    if not api_key:
        raise ValueError(f"{key_name} not found. Ensure {key_name} is set as an environment variable.")
    if api_key.strip() != api_key:
        raise ValueError(f"{key_name} has extra spaces. Remove any spaces or tabs from the key.")

cai_api_key = os.getenv('CALYPSO_API_KEY')
check_api_key(cai_api_key, 'CALYPSO_API_KEY')

DB_PATH = Path(__file__).resolve().with_name("database.db")

def ensure_db(db_path: Path = DB_PATH) -> Path:
    """Create the SQLite database by running createdb.py if it's missing.
    Runs the script from its own directory so relative paths inside it work.
    """
    if db_path.exists():
        return db_path

    import os

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "createdb.py",
        script_dir / "scripts" / "createdb.py",
    ]

    last_err = None
    for script in candidates:
        if not script.exists():
            continue
        prev_cwd = os.getcwd()
        try:
            os.chdir(script.parent)
            # Execute as if running "python createdb.py"
            runpy.run_path(str(script), run_name="__main__")
        except Exception as e:
            last_err = e
        finally:
            os.chdir(prev_cwd)
        break
    else:
        # Fallback: try as an importable module name if file not found in candidates
        try:
            runpy.run_module("createdb", run_name="__main__")
        except Exception as e:
            last_err = e

    if not db_path.exists():
        raise RuntimeError(
            f"createdb.py ran but did not produce {db_path.name}. "
            "Update DB_PATH to the filename/location your script writes, or modify createdb.py to write "
            f"'{db_path.name}' next to app.py."
        ) from last_err

    return db_path

def get_schema_info(db_path):
    """Retrieve schema information from the database for RAG."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema_info = {}
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        schema_info[table_name] = columns
    
    conn.close()
    return schema_info

def extract_sql_query_from_response(response):
    """Extract the SQL query from a response containing markdown and extra text."""
    # Use regex to find the SQL query inside the ```sql ... ``` block
    match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
    
    if match:
        # Return the cleaned SQL query
        return match.group(1).strip()
    else:
        raise ValueError("No valid SQL query found in the response.")

def generate_sql(natural_query, schema_info):
    """Use LLM to generate SQL from natural language."""
    schema_text = "\n".join([f"Table {table}: {', '.join(columns)}" for table, columns in schema_info.items()])
    system_prompt = "You generate SQL queries."
    prompt = f"""
    You are an AI assistant that converts natural language into SQL queries.

    Database Schema:
    {schema_text}

    User Query: "{natural_query}"

    Provide a SQL query that matches the user's request. If it is not clear how to convert it to an SQL query than say "not possible".
    """
    response = send_prompt_to_calypso(prompt, provider)

    if 'SELECT' not in response:
        return 'Not and SQL command'
    
    return extract_sql_query_from_response(response.strip())

def execute_sql(db_path, sql_query):
    """Execute a SQL query against the database and return the results."""
    
    # Ensure the query does not contain Markdown formatting (```sql ... ```)
    sql_query = sql_query.strip("```sql").strip("```").strip()
    
    conn = sqlite3.connect(db_path)  # Connect to SQLite database
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)  # Execute the SQL query
        
        # If it's a SELECT statement, fetch results
        if sql_query.lower().startswith("select"):
            results = cursor.fetchall()
        else:
            conn.commit()  # Commit changes for INSERT/UPDATE/DELETE
            results = "Query executed successfully."
    
    except sqlite3.Error as e:
        results = f"Error: {str(e)}"
    
    finally:
        conn.close()  # Ensure the database connection is closed
    
    return results

# Function to send prompt to CalypsoAI
def send_prompt_to_calypso(prompt: str, provider: str):
    # Set request headers for authorization and content type
    headers = {
        'Authorization': f'Bearer {cai_api_key}',
        'Content-Type': 'application/json',
    }
    base_url = "https://www.us1.calypsoai.app/backend/v1"
    # Prepare the JSON payload including the prompt and provider
    payload = {
        "input": prompt,
        "provider": provider,
        "verify": False,
        "verbose": "true",
        "externalMetadata": {"any_data": "testing testing 123", "user_id": "1234"}
    }

    # Send the POST request to the PromptAPI endpoint
    response = r.post(f"{base_url}/prompts", headers=headers, json=payload)
    if response.status_code == 200:
        print("Prompt sent successfully")
    else:
        print("Error:", response.status_code, response.text)

    # Pull data from response received from CalypsoAI with Provider output if it was not blocked
    response_data = response.json()

    if response_data["result"]["outcome"] == 'cleared':
        return response_data["result"]["response"]
    else: 
        return 'That type of question is not allowed'

def run_SQL(db_path, sql_query, user_input):
    # Step 4: Execute the SQL
    results = execute_sql(db_path, sql_query)
    print(f"DEBUG: SQL Results -> {results}")

    # Edge case: SQLite returns str for errors
    if isinstance(results, str) and results.lower().startswith("error"):
        return f"**Generated SQL:**\n```sql\n{sql_query}\n```\n\n❌ **Error executing SQL:**\n{results}"
    
    # System Prompt For SQL
    summary_prompt = f"""
You are a helpful assistant.

The user asked: "{user_input}".

This was the SQL query executed:
{sql_query}

This is the result of the SQL query as a list of tuples:
{json.dumps(results)}

Based on the user's question and the result, write a clear, human-readable response.

If the result contains employee names and salaries, return something like:
- Diana Prince earns $85,000
- Clark Kent earns $95,000
- Bruce Wayne earns $150,000

Avoid combining names/salaries in a sentence. Format cleanly, one item per line.
"""
    
    return summary_prompt


def chatbot_response(user_input, db_path=str(DB_PATH)):
    # Scan the input from the user

    # Step 1: Extract schema
    schema_info = get_schema_info(db_path)

    # Step 2: Check if natural language question is safe
    if send_prompt_to_calypso(user_input, provider) == 'That type of question is not allowed':
        return 'That type of question is not allowed'

    # Step 3: Generate SQL from user input
    sql_query = generate_sql(user_input, schema_info)
    print(f"DEBUG: Generated SQL -> {sql_query}")

    # Step 4: Execute the SQL is SQL Query generated
    if sql_query != 'Not and SQL command':
        prompt = run_SQL(db_path, sql_query, user_input)
        summary = send_prompt_to_calypso(prompt, provider)
        return f"**Generated SQL:**\n```sql\n{sql_query}\n```\n\n**Answer:**\n{summary}"
    # Step 5: Share non SQL
    else:
        prompt = user_input
        summary = send_prompt_to_calypso(prompt, provider)
        return f"**Not an SQL Query type question:**\n```sql\n{user_input}\n```\n\n**Answer:**\n{summary}"


# Streamlit UI
import streamlit as st

st.set_page_config(page_title="SQL Chatbot with Streamlit")
st.title("Acme HR Assistant")

@st.cache_resource
def init_db_once():
    return str(ensure_db())

# Ensure the SQLite file exists before any queries run
init_db_once()

user_input = st.text_input("Enter your natural language query:", placeholder="e.g. Get me the list of tables you have access to")

if user_input:
    with st.spinner("Generating SQL and running query..."):
        try:
            response = chatbot_response(user_input)
            st.markdown(response)
        except Exception as e:
            st.error(f"An error occurred: {e}")