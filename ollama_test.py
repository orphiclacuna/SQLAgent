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

    def chat(self, model, messages, stream=False):
        endpoint = f"{self.api_url}/chat"
        payload = {"model": model, "messages": messages, "stream": stream}

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

if __name__ == "__main__":
    client = OllamaClient(timeout=180, retries=2)

    # Simple text generation (non-streaming)
    print("=== Text Generation ===")
    result = client.generate(model="qwen3:4b", prompt="Why is the sky blue?", stream=False)
    if isinstance(result, dict) and result.get("error"):
        print("Error:", result)
    else:
        print(f"Response: {result.get('response')}")
        print(f"Model: {result.get('model')}")
        print(f"Total duration: {result.get('total_duration')} ns")

    # # Streaming text generation
    # print("\n=== Streaming Generation ===")
    # for chunk in client.generate(model="qwen3:4b", prompt="Why are u gay", stream=True):
    #     if isinstance(chunk, dict) and chunk.get("error"):
    #         print("\nStream error:", chunk)
    #         break
    #     if "response" in chunk:
    #         print(chunk["response"], end="", flush=True)
    # print()

    # # Chat completion
    # print("\n=== Chat Completion ===")
    # messages = [
    #     {"role": "user", "content": "What is Python?"},
    #     {"role": "assistant", "content": "Python is a programming language."},
    #     {"role": "user", "content": "What are its main uses?"}
    # ]
    # chat_result = client.chat(model="qwen3:4b", messages=messages, stream=False)
    # if isinstance(chat_result, dict) and chat_result.get("error"):
    #     print("Error:", chat_result)
    # else:
    #     print(f"Assistant: {chat_result.get('message', {}).get('content')}")

    # # Streaming chat
    # print("\n=== Streaming Chat ===")
    # messages = [{"role": "user", "content": "Tell me a joke"}]
    # for chunk in client.chat(model="qwen3:4b", messages=messages, stream=True):
    #     if isinstance(chunk, dict) and chunk.get("error"):
    #         print("\nStream error:", chunk)
    #         break
    #     if "message" in chunk and "content" in chunk["message"]:
    #         print(chunk["message"]["content"], end="", flush=True)
    # print()

    # List available models
    print("\n=== Available Models ===")
    models = client.list_models()
    if isinstance(models, dict) and models.get("error"):
        print("Error:", models)
    else:
        for model in models.get("models", []):
            print(f"- {model['name']}")
