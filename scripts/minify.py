import os
import minify_html
from csscompressor import compress as compress_css
from jsmin import jsmin

# Function to minify HTML using minify-html
def minify_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    minified_html = minify_html.minify(html_content, minify_js=True, minify_css=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(minified_html)
    print(f"Minified HTML: {file_path}")

# Function to minify CSS
def minify_css(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    minified_css = compress_css(css_content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(minified_css)
    print(f"Minified CSS: {file_path}")

# Function to minify JavaScript
def minify_js(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    minified_js = jsmin(js_content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(minified_js)
    print(f"Minified JS: {file_path}")

# Main function to iterate through the public folder
def minify_public_folder(public_dir='public'):
    for root, dirs, files in os.walk(public_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.html'):
                minify_html_file(file_path)
            elif file.endswith('.css'):
                minify_css(file_path)
            elif file.endswith('.js'):
                minify_js(file_path)

if __name__ == "__main__":
    minify_public_folder()
