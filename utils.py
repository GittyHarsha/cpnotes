# utils.py
def sanitize(text: str) -> str:
    import re
    slug = text.strip().replace("/", "_").replace(" ", "_")
    slug = re.sub(r"[^A-Za-z0-9_-]", "", slug)
    if re.match(r"^[0-9]", slug):
        slug = f"id_{slug}"
    return slug
