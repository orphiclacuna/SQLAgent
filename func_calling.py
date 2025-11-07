import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class OllamaClient:
    def __init__(self, base_url="http://10.131.71.235:11434", timeout=5, retries=3, backoff_factor=0.3):
        """
        timeout: seconds to wait for connect/read operations
        retries: number of total retries for idempotent requests
        backoff_factor: sleep between retries: {backoff_factor} * (2 ** (retry_number - 1))
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.timeout = timeout

        self.session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def generate(self, model, prompt, stream=False):
        endpoint = f"{self.api_url}/generate"
        payload = {"model": model, "prompt": prompt, "stream": stream}

        if stream:
            return self._stream_response(endpoint, payload)
        try:
            resp = self.session.post(endpoint, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {"error": "invalid_json", "message": "Response is not valid JSON", "text": resp.text}
        except requests.exceptions.ConnectTimeout as e:
            return {"error": "connect_timeout", "message": str(e)}
        except requests.exceptions.ReadTimeout as e:
            return {"error": "read_timeout", "message": str(e)}
        except requests.exceptions.ConnectionError as e:
            return {"error": "connection_error", "message": str(e)}
        except requests.exceptions.HTTPError as e:
            return {"error": "http_error", "message": str(e), "status_code": getattr(e.response, "status_code", None)}
        except requests.exceptions.RequestException as e:
            return {"error": "request_exception", "message": str(e)}

    def chat(self, model, messages, stream=False, tools=None):
        """
        Chat endpoint with optional tools support for function calling
        """
        endpoint = f"{self.api_url}/chat"
        payload = {"model": model, "messages": messages, "stream": stream}
        
        # Add tools to payload if provided
        if tools:
            payload["tools"] = tools

        if stream:
            return self._stream_response(endpoint, payload)
        try:
            resp = self.session.post(endpoint, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {"error": "invalid_json", "message": "Response is not valid JSON", "text": resp.text}
        except requests.exceptions.ConnectTimeout as e:
            return {"error": "connect_timeout", "message": str(e)}
        except requests.exceptions.ReadTimeout as e:
            return {"error": "read_timeout", "message": str(e)}
        except requests.exceptions.ConnectionError as e:
            return {"error": "connection_error", "message": str(e)}
        except requests.exceptions.HTTPError as e:
            return {"error": "http_error", "message": str(e), "status_code": getattr(e.response, "status_code", None)}
        except requests.exceptions.RequestException as e:
            return {"error": "request_exception", "message": str(e)}

    def list_models(self):
        endpoint = f"{self.api_url}/tags"
        try:
            resp = self.session.get(endpoint, timeout=self.timeout)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {"error": "invalid_json", "message": "Response is not valid JSON", "text": resp.text}
        except requests.exceptions.RequestException as e:
            return {"error": "request_exception", "message": str(e)}

    def _stream_response(self, endpoint, payload):
        """
        Generator that yields parsed JSON lines or an error dict on failure.
        Yields dicts for consistency with non-streaming responses.
        """
        try:
            with self.session.post(endpoint, json=payload, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except ValueError:
                        # Non-JSON line received; yield raw text for debugging
                        yield {"error": "invalid_json_line", "line": line.decode(errors="replace")}
        except requests.exceptions.ConnectTimeout as e:
            yield {"error": "connect_timeout", "message": str(e)}
        except requests.exceptions.ReadTimeout as e:
            yield {"error": "read_timeout", "message": str(e)}
        except requests.exceptions.ConnectionError as e:
            yield {"error": "connection_error", "message": str(e)}
        except requests.exceptions.HTTPError as e:
            yield {"error": "http_error", "message": str(e), "status_code": getattr(e.response, "status_code", None)}
        except requests.exceptions.RequestException as e:
            yield {"error": "request_exception", "message": str(e)}


# ============================================
# FUNCTION CALLING IMPLEMENTATION
# ============================================

# Define tools/functions for the model
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_temperature",
            "description": "Get the current temperature for a city",
            "parameters": {
                "type": "object",
                "required": ["city"],
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_conditions",
            "description": "Get the current weather conditions for a city",
            "parameters": {
                "type": "object",
                "required": ["city"],
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform basic mathematical calculations",
            "parameters": {
                "type": "object",
                "required": ["operation", "a", "b"],
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The mathematical operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                }
            }
        }
    }
]

# Implement the actual functions
def get_temperature(city, unit="celsius"):
    """Simulated weather function - replace with real API call"""
    temperatures = {
        "New York": {"celsius": "22°C", "fahrenheit": "72°F"},
        "London": {"celsius": "15°C", "fahrenheit": "59°F"},
        "Tokyo": {"celsius": "18°C", "fahrenheit": "64°F"},
        "Mumbai": {"celsius": "32°C", "fahrenheit": "90°F"}
    }
    temp = temperatures.get(city, {"celsius": "20°C", "fahrenheit": "68°F"})
    return temp.get(unit, temp["celsius"])

def get_conditions(city):
    """Simulated weather conditions - replace with real API call"""
    conditions = {
        "New York": "Partly cloudy",
        "London": "Rainy",
        "Tokyo": "Sunny",
        "Mumbai": "Hot and humid"
    }
    return conditions.get(city, "Clear skies")

def calculate(operation, a, b):
    """Perform mathematical calculations"""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: Division by zero"
    }
    return str(operations.get(operation, "Invalid operation"))

# Map function names to actual functions
available_functions = {
    "get_temperature": get_temperature,
    "get_conditions": get_conditions,
    "calculate": calculate
}


def generate_with_function_calling(client, user_message, model="qwen3:4b", max_iterations=5):
    """
    Generate with function calling support - handles agent loop using generate endpoint
    """
    prompt = user_message
    
    print(f"User: {user_message}\n")
    
    for iteration in range(max_iterations):
        # Make generate request
        response = client.generate(model=model, prompt=prompt, stream=False)
        
        # Check for errors
        if isinstance(response, dict) and response.get("error"):
            print(f"Error: {response}")
            return response
        
        # Extract the response text
        response_text = response.get("response", "")
        print(f"[Iteration {iteration + 1}] Response: {response_text}")
        
        # For simplicity with generate endpoint, we'll process the response directly
        # The generate endpoint doesn't natively support function calling like chat does,
        # so this is a basic implementation
        print(f"\nAssistant: {response_text}")
        return response
    
    print("\nMax iterations reached")
    return response


def single_shot_generate(client, user_message, model="qwen3:4b"):
    """
    Simple single-shot generation example using generate endpoint
    """
    prompt = user_message
    
    print(f"User: {user_message}\n")
    
    # Make generate request
    response = client.generate(model=model, prompt=prompt, stream=False)
    
    if isinstance(response, dict) and response.get("error"):
        print(f"Error: {response}")
        return response
    
    response_text = response.get("response", "")
    print(f"Assistant: {response_text}")
    
    return response


def streaming_generate(client, user_message, model="qwen3:4b"):
    """
    Streaming generation example using generate endpoint
    """
    prompt = user_message
    
    print(f"User: {user_message}\n")
    print("Assistant (streaming): ", end="", flush=True)
    
    # Stream the response
    for chunk in client.generate(model=model, prompt=prompt, stream=True):
        if isinstance(chunk, dict) and chunk.get("error"):
            print(f"\nError: {chunk}")
            return chunk
        
        response_text = chunk.get("response", "")
        print(response_text, end="", flush=True)
    
    print()


if __name__ == "__main__":
    # Initialize client with higher timeout for function calling
    client = OllamaClient(timeout=180, retries=2)
    
    print("=== 1. Single-Shot Generate ===")
    single_shot_generate(
        client, 
        "What's the temperature in New York?"
    )
    
    print("\n\n=== 2. Simple Generate ===")
    single_shot_generate(
        client,
        "What are the temperature and weather conditions in London?"
    )
    
    print("\n\n=== 3. Multi-step Query ===")
    single_shot_generate(
        client,
        "What is 156 multiplied by 23, and what's the weather like in Tokyo?"
    )
    
    print("\n\n=== 4. Streaming Generate ===")
    streaming_generate(
        client,
        "Tell me the weather conditions in Mumbai"
    )
    
    print("\n\n=== 5. Complex Multi-step Query ===")
    single_shot_generate(
        client,
        "Calculate 100 + 50, then tell me if it's warmer in New York or London"
    )
