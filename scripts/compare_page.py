import os
import json
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = "src/templates"
OUTPUT_DIR = "public"
TEMPLATE_NAME = "compare.html"
OUTPUT_NAME = "compare.html"

def load_funds():
    with open("data/data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def render_compare_page(funds):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_NAME)
    html = template.render(funds=funds)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, OUTPUT_NAME)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {out_path}")

if __name__ == "__main__":
    render_compare_page(load_funds())