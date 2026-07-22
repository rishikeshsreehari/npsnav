import http.server
import socketserver
import os

PORT = 8000
DIRECTORY = "public"

class CleanUrlHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Check if the path ends with a slash or has no extension
        if not self.path.endswith('/') and '.' not in os.path.basename(self.path):
            # Try a corresponding .html file (page routes), then .json
            # (mirrors the /api/.../:id -> :id.json rules in _redirects)
            for ext in ('.html', '.json'):
                candidate = self.translate_path(self.path) + ext
                if os.path.exists(candidate):
                    self.path += ext
                    break

        return super().do_GET()


if __name__ == "__main__":
    # Ensure we are serving from the correct directory context
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory '{DIRECTORY}' not found. Please run 'make build' first.")
        exit(1)

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    # Try default port first
    port = PORT
    try:
        httpd = ReusableTCPServer(("", port), CleanUrlHandler)
    except OSError:
        # Default port busy — pick any free port automatically
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))       # 0 = any free port
            port = s.getsockname()[1]

        httpd = ReusableTCPServer(("", port), CleanUrlHandler)

    print(f"Serving at http://localhost:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


