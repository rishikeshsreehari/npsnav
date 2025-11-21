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
            # Try to find a corresponding .html file
            html_path = self.translate_path(self.path) + ".html"
            if os.path.exists(html_path):
                self.path += ".html"
        
        return super().do_GET()

if __name__ == "__main__":
    # Ensure we are serving from the correct directory context
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory '{DIRECTORY}' not found. Please run 'make build' first.")
        exit(1)

    with socketserver.TCPServer(("", PORT), CleanUrlHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
