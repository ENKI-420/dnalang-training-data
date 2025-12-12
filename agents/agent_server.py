#!/usr/bin/env python3
"""Sovereign Agent HTTP Server"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / ".sovereign/training"))

from train_sovereign_agent import SovereignAgent, TrainingConfig

config = TrainingConfig()
agent = SovereignAgent(config)

class AgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            response = agent.generate(body.get('message', ''))
            status = agent.get_status()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response,
                "ccce": status['ccce']
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(agent.get_status()).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    port = 8888
    print(f"[Ω] Sovereign Agent Server starting on port {port}")
    HTTPServer(('0.0.0.0', port), AgentHandler).serve_forever()
