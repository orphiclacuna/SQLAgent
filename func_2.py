import sqlite3
import json
from mistralai import Mistral
from time import sleep
import functools

messages = []

def execute_command(conn, sql_list):
    results = []
    for sql in sql_list:
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            if sql.strip().lower().startswith("select"):
                db_result = [i[0] for i in cursor.fetchall()]
            else:
                conn.commit()
                db_result = []
            results.append(db_result)
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
    return results

def gen_sql_schema(conn):
    get_schema_sql = "SELECT sql FROM sqlite_master WHERE type='table';"
    db_schema = execute_command(conn, [get_schema_sql])
    return db_schema[0]

db_path = "userbase.db"  # input("Enter db path: ")

try:
    conn = sqlite3.connect(db_path)
    print(f"Connected to the database: {db_path}")


    while True:
        db_schema = gen_sql_schema(conn)

        user_input = input("------------------------\nEnter: ")

        sys_prompt = "You will be given the table schema of a database and a user question. Execute a SQL query based on the user question to answer it, if needed. Please respond with a function call to execute sql queries."
        user_prompt = f"SQL schema of SQLite3 database {db_schema}. Write a SQL query to get the response for this user question: {user_input}."

        messages = [
            {
                "role": "system",
                "content": sys_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql_query",
                    "description": "Executes a list of SQL queries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_list": {
                                "type": "array",
                                "description": "List of SQL queries to execute.",
                            }
                        },
                        "required": ["sql_list"],
                    },
                },
            },
        ]

        names_to_functions = {
            'execute_sql_query': functools.partial(execute_command, conn), 
        }
        """
        functools.partial creates a new function (execute_sql_query) that freeze the original function (execute_command) with the `conn` parameter already set.
        It is in the form of a dictionary where the key is the function name and the value is the original function with freezed parameter. 
        Before using functools.partial, calling `execute_command` required both `conn` and `sql_list`
        After using functools.partial, the new function execute_sql_query only requires sql_list
        `names_to_functions` is a dictionary that maps function names to function calls
        """

        if user_input.lower() == 'exit':
            break

        model = "mistral-large-latest"
        client = Mistral(api_key="<>")

        chat_response = client.chat.complete(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="any",
        )

        print(chat_response)
        print(chat_response.choices[0].message.content)

        tool_call = chat_response.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        function_params = json.loads(tool_call.function.arguments)

        print("\nFunction_name: ", function_name, "\nFunction_params: ", function_params)

        results = names_to_functions[function_name](function_params['sql_list'])
        print("\nResults: ", results)

except sqlite3.Error as e:
    print(f"An error occurred while connecting to the database: {e}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    if conn:
        conn.close()
        print("Connection closed.")
