import bleach

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "span", "a", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "code",
    "img", "table", "thead", "tbody", "tr", "th", "td", "hr"
]
ALLOWED_ATTRS = {
    "*": ["class", "style"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading"]
}
ALLOWED_PROTOCOLS = ["http", "https", "data"]

def sanitize_html(html: str) -> str:
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned)
