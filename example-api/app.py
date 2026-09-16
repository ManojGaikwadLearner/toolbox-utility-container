"""
A deliberately trivial HTTP server (stdlib only, no framework) standing in
for "a real app". Its only job here is to prove that by the time it starts,
the entrypoint's `toolbox wait-for db:5432` has already succeeded.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - example-api started after the database became reachable\n")

    def log_message(self, format, *args):  # noqa: A002 - matches BaseHTTPRequestHandler's signature
        # Keep container logs focused on the entrypoint's own structured output.
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()
