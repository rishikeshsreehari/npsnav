import os
import htmlmin
from csscompressor import compress as compress_css
from jsmin import jsmin

# Function to minify HTML
def minify_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    minified_html = htmlmin.minify(html_content, remove_comments=True, remove_empty_space=True)
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
    
    # Add space after function keywords to prevent minification issues
    js_content = js_content.replace('function(', 'function (')
    
    minified_js = jsmin(js_content, quote_chars="'\"`")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(minified_js)

# Main function to iterate through the public folder
def minify_public_folder(public_dir='public'):
    for root, dirs, files in os.walk(public_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.html'):
                minify_html(file_path)
            elif file.endswith('.css'):
                minify_css(file_path)
            elif file.endswith('.js'):
                minify_js(file_path)

if __name__ == "__main__":
    minify_public_folder()
