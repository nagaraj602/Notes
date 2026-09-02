import os
import re
import markdown
from pymdownx import superfences

def resolve_path(base_dir: str, rel_path: str) -> str:
    if rel_path.startswith("/") or "://" in rel_path or rel_path.startswith("data:"):
        return rel_path
    combined = os.path.normpath(os.path.join(base_dir, rel_path)).replace("\\", "/")
    return combined.lstrip("/")

def rewrite_relative_assets(html_content: str, file_rel_path: str) -> str:
    if not file_rel_path:
        return html_content
    base_dir = os.path.dirname(file_rel_path).replace("\\", "/")

    # Rewrite <img> src attributes
    def replace_img_src(match):
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:") or src.startswith("/raw/"):
            return match.group(0)
        resolved = resolve_path(base_dir, src)
        return f'{prefix}/raw/{resolved}{suffix}'

    html_content = re.sub(r'(<img\s+[^>]*?src=["\'])([^"\']+)(["\'])', replace_img_src, html_content, flags=re.IGNORECASE)
    return html_content

def render_markdown(raw_content: str, file_rel_path: str = "") -> str:
    """Renders GitHub Flavored Markdown with syntax highlighting, tables, tasklists, and asset resolution."""
    extensions = [
        'extra',
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'pymdownx.superfences',
        'pymdownx.tasklist',
        'pymdownx.highlight',
        'pymdownx.inlinehilite',
    ]
    extension_configs = {
        'codehilite': {
            'linenums': False,
            'css_class': 'highlight',
            'guess_lang': False
        },
        'pymdownx.highlight': {
            'linenums': False,
            'css_class': 'highlight'
        },
        'pymdownx.tasklist': {
            'custom_checkbox': True
        }
    }
    rendered_html = markdown.markdown(raw_content, extensions=extensions, extension_configs=extension_configs)
    if file_rel_path:
        rendered_html = rewrite_relative_assets(rendered_html, file_rel_path)
    return rendered_html