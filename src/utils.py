def slugify(s: str) -> str:
    return (
        s.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("&", "and")
        .replace(",", "")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
    )
