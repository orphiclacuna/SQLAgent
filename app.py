import os
import gradio as gr
from dotenv import load_dotenv
from sql_agent import SQLAgent, BASE_URL, MODEL, DB_PATH

load_dotenv()

api_key_env = os.getenv("GROQ_API_KEY")

agent = SQLAgent(
    api_key=api_key_env,
    base_url=BASE_URL,
    model=MODEL,
    db_path=DB_PATH
)

def respond(message, history):
    """
    Generator function for Gradio ChatInterface.
    """
    # History is list of [user_msg, bot_msg]
    # We don't necessarily need to pass history to the agent because 
    # the agent currently treats each run mostly independently (though with the same DB).
    # If we wanted multi-turn context, we'd need to update process_message to accept history.
    # For now, let's just process the current message.

    full_response = ""
    for update in agent.process_message(message):
        if update.startswith("Final Answer:"):
            answer = update.replace("Final Answer:", "").strip()
            full_response += f"\n\n**Answer:** {answer}"
        elif update.startswith("Thought:"):
            full_response += f"\n*Thinking: {update.replace('Thought:', '').strip()}*"
        elif update.startswith("Executing SQL:"):
            full_response += f"\n`{update}`"
        elif update.startswith("SQL Result"):
             full_response += f"\n_{update}_"
        elif update.startswith("SQL Error"):
             full_response += f"\n{update}"
        else:
            full_response += f"\n{update}"

        yield full_response

custom_css = """
#component-0 {
    height: 100vh !important;
}
.chatbot {
    min-height: 500px;
}
"""

with gr.Blocks(title="Text2SQL Agent", theme="soft", css=custom_css) as demo:
    gr.Markdown("# Text2SQL Agent with SQL Agent")
    gr.Markdown(f"Connected to database: `{DB_PATH}` using model `{MODEL}`")

    chat_interface = gr.ChatInterface(
        respond,
        chatbot=gr.Chatbot(height=600),
        textbox=gr.Textbox(placeholder="Ask a question about your database...", container=False, scale=7),
        examples=[
            "Show me the available tables",
            "How many tracks are there?",
            "List the top 5 longest tracks",
            "Who are the customers from USA?"
        ]
    )

if __name__ == "__main__":
    demo.launch()
