import os
import json
from typing import Iterator, List, Dict, Any
from openai import OpenAI
from sql_paraser import list_tables, run_sql
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b" 
DB_PATH = "chinook.db"

class SQLAgent:
    def __init__(self, api_key: str, base_url: str, model: str, db_path: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.db_path = db_path

        if not os.path.exists(self.db_path):
            print(f"Warning: Database file not found at {self.db_path}")

    def get_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def get_schema_context(self) -> str:
        tables = list_tables(self.db_path)
        schema_desc = ""
        # tables is a list of dicts: {"table_name": name, "table_sql": cleaned}
        if isinstance(tables, list):
             for table in tables:
                schema_desc += f"Table: {table.get('table_name')}\n{table.get('table_sql')}\n\n"
        return schema_desc

    def get_completion(self, messages: List[Dict[str, Any]], json_mode: bool = False) -> str:
        client = self.get_client()
        extra_args = {}
        if json_mode:
            extra_args['response_format'] = {"type": "json_object"}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **extra_args
                )
                return response.choices[0].message.content
            except Exception as e:
                # Groq specific JSON validation error often returns 400
                if "json_validate_failed" in str(e).lower() or "400" in str(e):
                    if attempt < max_retries - 1:
                        # Append a reminder to the messages for the retry
                        if messages[-1]["role"] != "system":
                            messages.append({"role": "system", "content": "IMPORTANT: You must respond ONLY with a valid JSON object. No conversational text before or after."})
                        continue
                print(f"Error calling API (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return ""
        return ""

    def process_message(self, user_input: str) -> Iterator[str]:
        """
        Process a user message and yield intermediate steps and final answer.
        """
        schema_context = self.get_schema_context()
        if not schema_context:
            yield "Error: Could not retrieve schema."
            return

        system_prompt = f"""You are a SQL agent. You have access to a SQLite database.
Schema:
{schema_context}

You interact with the database to answer the user's question.
You can iteratively execute SQL queries to investigate data.
You will query the database to get the answers, NEVER guess.
If a query returns too many rows, you will see a truncated result, and you should refine your query (e.g., using aggregations or limits).

RESPONSE FORMAT:
You must respond with a JSON object. Ensure the entire response is a single JSON object.

Example for SQL:
{{
    "type": "sql",
    "sql": "SELECT ...",
    "thought": "Brief logic"
}}

Example for Answer:
{{
    "type": "answer",
    "content": "Final human-readable answer",
    "thought": "How I got here"
}}

Strictly NO markdown blocks, NO preamble, and NO text outside the JSON.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        max_steps = 10
        step = 0

        while step < max_steps:
            step += 1

            response_text = self.get_completion(messages, json_mode=True)

            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                yield f"Debug: Failed to parse JSON response: {response_text}"
                messages.append({"role": "user", "content": "Error: Invalid JSON response. Please respond with valid JSON."})
                continue

            response_type = response_data.get("type")
            thought = response_data.get("thought")

            if thought:
                yield f"Thought: {thought}"

            if response_type == "sql":
                sql_query = response_data.get("sql")
                yield f"Executing SQL: {sql_query}"

                result = run_sql(self.db_path, sql_query)

                if result.get("status") == "ok":
                    rows = result.get("rows", [])
                    total_rows = len(rows)

                    MAX_PREVIEW_ROWS = 10

                    if total_rows > MAX_PREVIEW_ROWS:
                        preview_rows = rows[:MAX_PREVIEW_ROWS]
                        data_str = json.dumps(preview_rows, default=str)
                        result_message = f"Query returned {total_rows} rows. This is too many to show. Here are the first {MAX_PREVIEW_ROWS} rows:\n{data_str}\n\nPlease refine your query if you need more specific data, or use this sample to answer."
                    else:
                        data_str = json.dumps(rows, default=str)
                        result_message = f"Query returned {total_rows} rows:\n{data_str}"

                    yield f"SQL Result ({total_rows} rows)"
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": result_message})

                else:
                    error_msg = result.get("error", "Unknown error")
                    yield f"SQL Error: {error_msg}"
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({"role": "user", "content": f"SQL Error: {error_msg}"})

            elif response_type == "answer":
                answer_content = response_data.get("content")
                yield f"Final Answer: {answer_content}"
                return

            else:
                yield f"Debug: Unknown response type: {response_type}"
                messages.append({"role": "user", "content": "Error: Unknown response type. Use 'sql' or 'answer'."})

        if step >= max_steps:
            yield "Error: Agent reached maximum steps without a final answer."

    def run(self):
        print(f"SQL Agent started. Using DB: {self.db_path}")
        print("Type 'exit' to quit.")

        schema_context = self.get_schema_context()
        if not schema_context:
            print("Could not retrieve schema. Exiting.")
            return

        # System prompt for the agentic loop
        system_prompt = f"""You are a SQL agent. You have access to a SQLite database.
Schema:
{schema_context}

You interact with the database to answer the user's question.
You can iteratively execute SQL queries to investigate data.
You will query the database to get the answers, NEVER guess.
If a query returns too many rows, you will see a truncated result, and you should refine your query (e.g., using aggregations or limits).

RESPONSE FORMAT:
You must respond with a JSON object. Ensure the entire response is a single JSON object.

Example for SQL:
{{
    "type": "sql",
    "sql": "SELECT ...",
    "thought": "Brief logic"
}}

Example for Answer:
{{
    "type": "answer",
    "content": "Final human-readable answer",
    "thought": "How I got here"
}}

Strictly NO markdown blocks, NO preamble, and NO text outside the JSON.
"""

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                # Initialize conversation history with system prompt and user input
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]

                # Agent loop
                max_steps = 10
                step = 0

                while step < max_steps:
                    step += 1

                    response_text = self.get_completion(messages, json_mode=True)

                    try:
                        response_data = json.loads(response_text)
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON response: {response_text}")
                        # Feed the error back to the model so it can correct itself
                        messages.append({"role": "user", "content": "Error: Invalid JSON response. Please respond with valid JSON."})
                        continue

                    response_type = response_data.get("type")
                    thought = response_data.get("thought")

                    if thought:
                        print(f"Agent Thought: {thought}")

                    if response_type == "sql":
                        sql_query = response_data.get("sql")
                        print(f"Executing SQL: {sql_query}")

                        result = run_sql(self.db_path, sql_query)

                        if result.get("status") == "ok":
                            rows = result.get("rows", [])
                            total_rows = len(rows)

                            MAX_PREVIEW_ROWS = 10

                            if total_rows > MAX_PREVIEW_ROWS:
                                preview_rows = rows[:MAX_PREVIEW_ROWS]
                                data_str = json.dumps(preview_rows, default=str)
                                result_message = f"Query returned {total_rows} rows. This is too many to show. Here are the first {MAX_PREVIEW_ROWS} rows:\n{data_str}\n\nPlease refine your query if you need more specific data, or use this sample to answer."
                            else:
                                data_str = json.dumps(rows, default=str)
                                result_message = f"Query returned {total_rows} rows:\n{data_str}"

                            print(f"SQL Result: {total_rows} rows found.")
                            messages.append({"role": "assistant", "content": response_text})
                            messages.append({"role": "user", "content": result_message})

                        else:
                            error_msg = result.get("error", "Unknown error")
                            print(f"SQL Error: {error_msg}")
                            messages.append({"role": "assistant", "content": response_text})
                            messages.append({"role": "user", "content": f"SQL Error: {error_msg}"})

                    elif response_type == "answer":
                        answer_content = response_data.get("content")
                        print(f"\nAgent: {answer_content}")
                        break

                    else:
                        print(f"Unknown response type: {response_type}")
                        messages.append({"role": "user", "content": "Error: Unknown response type. Use 'sql' or 'answer'."})

                if step >= max_steps:
                    print("Agent reached maximum steps without a final answer.")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":

    api_key_env = os.getenv("GROQ_API_KEY")

    agent = SQLAgent(
        api_key=api_key_env,
        base_url=BASE_URL,
        model=MODEL,
        db_path=DB_PATH
    )
    agent.run()
