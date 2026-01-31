# SQL Agent

A natural language to SQL query agent that allows users to ask questions about SQLite databases in plain English. The agent uses Groq's API to generate and execute SQL queries iteratively, providing human-readable answers.

## Features

- **Natural Language Queries**: Ask questions about your database in plain English
- **Iterative SQL Generation**: The agent can execute multiple SQL queries to build up to a final answer
- **Web Interface**: User-friendly Gradio web interface for easy interaction
- **Command Line Interface**: Terminal-based interface for developers
- **SQLite Support**: Works with any SQLite database
- **Schema Awareness**: Automatically retrieves and uses database schema information
- **Error Handling**: Robust error handling for SQL execution and API calls

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd SQLAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Copy `.env.example` to `.env` (if it exists) or create a new `.env` file
   - Add your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

### Web Interface

Run the Gradio web application:

```bash
python app.py
```

This will start a local web server. Open the provided URL in your browser to access the chat interface.

### Command Line Interface

Run the agent in terminal mode:

```bash
python sql_agent.py
```

Type your questions and get answers directly in the terminal.

## Configuration

The agent uses the following default configuration (defined in `sql_agent.py`):

- **Base URL**: `https://api.groq.com/openai/v1`
- **Model**: `openai/gpt-oss-120b`

You can modify these constants in the code or make them configurable via environment variables.

## Database Setup

To use your own database:
1. Place your SQLite database file in the project directory
2. Update the `DB_PATH` variable in `sql_agent.py`

## How It Works

1. **Schema Retrieval**: The agent first retrieves the database schema (table structures)
2. **Natural Language Processing**: User questions are sent to Groq's API with schema context
3. **SQL Generation**: The AI generates appropriate SQL queries based on the question
4. **Execution**: Queries are executed against the database
5. **Iteration**: If needed, the agent can perform follow-up queries based on results
6. **Final Answer**: Human-readable answers are provided to the user

## Dependencies

Key dependencies include:
- `gradio`: Web interface
- `openai`: Groq API client
- `python-dotenv`: Environment variable management
- `sqlite3`: Database operations (built-in)

See `requirements.txt` for complete list.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request