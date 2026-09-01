import markdown
from pymdownx import superfences

def render_markdown(raw_content: str) -> str:
    """Renders GitHub Flavored Markdown with syntax highlighting, tables, tasklists, and TOC."""
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
    return markdown.markdown(raw_content, extensions=extensions, extension_configs=extension_configs)