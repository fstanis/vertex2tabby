#!/usr/bin/env python3

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import google.auth
import httpx
from google.auth.transport.requests import Request

# Configuration
LISTEN_ADDRESS = "127.0.0.1"
LISTEN_PORT = 4000
PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
REGION = os.environ.get("GOOGLE_REGION")
EMBEDDING_REGION = "us-central1"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

EMBEDDING_MODEL = "text-embedding-005"
MISTRAL_MODEL = "codestral-2"
DEEPSEEK_MODEL = "deepseek-v3.2-maas"


def get_headers():
    creds, _ = google.auth.default(scopes=SCOPES)
    creds.refresh(Request())
    return {"Authorization": f"Bearer {creds.token}", "Accept": "application/json"}


def build_url(region, model, stream):
    host = (
        "https://aiplatform.googleapis.com"
        if region == "global"
        else f"https://{region}-aiplatform.googleapis.com"
    )
    base = f"{host}/v1/projects/{PROJECT_ID}/locations/{region}"
    if model == MISTRAL_MODEL:
        full_model = f"mistralai/models/{model}"
        method = "streamRawPredict" if stream else "rawPredict"
        return f"{base}/publishers/{full_model}:{method}"
    elif model == EMBEDDING_MODEL:
        full_model = f"google/models/{model}"
        return f"{base}/publishers/{full_model}:predict"
    else:
        return f"{base}/endpoints/openapi/chat/completions"


class Handler(BaseHTTPRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        print(f"=== REQUEST: {self.command} {self.path} ===")
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            return self.send_error(400, "Invalid JSON")
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            return

        try:
            print(f"Path: {self.path}, Model: {body.get('model')}")

            if self.path in ["/v1/fim/completions", "/chat/completions"]:
                self.handle_completion(body)
            elif self.path.startswith("/openai/deployments/"):
                self.handle_embedding(body)
            else:
                self.send_error(404)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            return
        except Exception as e:
            print(f"Error: {e}")
            try:
                self.send_error(500)
            except:
                pass

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data if isinstance(data, bytes) else json.dumps(data).encode())

    def handle_completion(self, data):
        req_model = data.get("model")
        stream = data.get("stream", False)
        url = None

        if self.path == "/chat/completions":
            region = REGION
            if req_model == DEEPSEEK_MODEL:
                data["model"] = f"deepseek-ai/{DEEPSEEK_MODEL}"
                region = "global"
            url = build_url(region, req_model, stream)
        elif self.path == "/v1/fim/completions":
            if req_model and req_model != MISTRAL_MODEL:
                return self.send_error(
                    400,
                    f"Model {req_model} not supported for FIM. Use {MISTRAL_MODEL}.",
                )
            url = build_url(REGION, MISTRAL_MODEL, stream)

        if not url:
            return self.send_error(404, "Not Found")

        print(f"  -> Forwarding to: {url} (stream={stream})")

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            with httpx.Client() as client:
                with client.stream(
                    "POST", url, json=data, headers=get_headers(), timeout=None
                ) as r:
                    for line in r.iter_lines():
                        if line.startswith("data:"):
                            chunk = line[5:].strip()
                            if chunk == "[DONE]":
                                self.wfile.write(b"data: [DONE]\n\n")
                                self.wfile.flush()
                                break
                            try:
                                chunk_data = json.loads(chunk)
                                if (
                                    "usage" in chunk_data
                                    and "prompt_tokens" not in chunk_data["usage"]
                                ):
                                    del chunk_data["usage"]
                                self.wfile.write(
                                    f"data: {json.dumps(chunk_data)}\n\n".encode()
                                )
                                self.wfile.flush()
                            except json.JSONDecodeError:
                                pass
        else:
            with httpx.Client() as client:
                resp = client.post(url, json=data, headers=get_headers(), timeout=None)
            print(f"  <- Response: {resp.status_code}")
            self.send_json(resp.status_code, resp.content)

    def handle_embedding(self, data):
        url = build_url(EMBEDDING_REGION, EMBEDDING_MODEL, False)
        payload = {
            "instances": [
                {"task_type": "RETRIEVAL_QUERY", "content": data.get("input", "")}
            ]
        }
        print(f"  -> Forwarding to: {url}")

        with httpx.Client() as client:
            resp = client.post(url, json=payload, headers=get_headers(), timeout=None)

        print(f"  <- Response: {resp.status_code}")
        if resp.status_code != 200:
            self.send_json(resp.status_code, resp.content)
        else:
            openai_resp = {
                "data": [
                    {"embedding": p["embeddings"]["values"]}
                    for p in resp.json().get("predictions", [])
                ]
            }
            self.send_json(200, openai_resp)


if __name__ == "__main__":
    try:
        google.auth.default(scopes=SCOPES)
    except google.auth.exceptions.DefaultCredentialsError:
        print("Error: Application Default Credentials not found.")
        print("Run 'gcloud auth application-default login' to set them up.")
        exit(1)

    server = HTTPServer((LISTEN_ADDRESS, LISTEN_PORT), Handler)
    server.serve_forever()
