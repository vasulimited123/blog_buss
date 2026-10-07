"""
Shared helpers for the seed_content command.

Article data is authored as a list of dicts in _content_batch*.py modules.
Each article dict uses a compact structure; render_body() turns the
structured `body` blocks into HTML the templates display.

Ad-safe language rule: keep everything clinical, educational, and polite.
No explicit or crude terms anywhere.
"""


def render_body(blocks):
    """Convert structured content blocks into HTML.

    Block kinds:
      ("p", "text")            -> paragraph
      ("h2", "text")           -> section heading
      ("quote", "text")        -> blockquote
      ("ul", [item, item])     -> bullet list
      ("ol", [item, item])     -> numbered list
    """
    html = []
    for block in blocks:
        kind = block[0]
        val = block[1]
        if kind == "h2":
            html.append(f"<h2>{val}</h2>")
        elif kind == "quote":
            html.append(f"<blockquote>{val}</blockquote>")
        elif kind == "ul":
            items = "".join(f"<li>{i}</li>" for i in val)
            html.append(f"<ul>{items}</ul>")
        elif kind == "ol":
            items = "".join(f"<li>{i}</li>" for i in val)
            html.append(f"<ol>{items}</ol>")
        else:  # "p"
            html.append(f"<p>{val}</p>")
    return "\n".join(html)


# Standard reputable sources reused across health articles (generic, safe).
DEFAULT_SOURCES = [
    "https://www.who.int/health-topics/sexual-health",
    "https://www.ncbi.nlm.nih.gov/",
    "https://www.mayoclinic.org/",
]

# Standard educational disclaimer note appended to sensitive articles.
STANDARD_WARNING = "This article is educational and discusses adult health and relationship topics."
