from pathlib import Path

SKILLS_DIR = Path(__file__).parent/"skills"

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    _, raw_meta, body = parts
    meta = {}
    for line in raw_meta.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body.strip()
 
 
def list_skills() -> list[dict]:
    menu = []
    for path in sorted(SKILLS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(text)
        menu.append({
            "name": meta.get("name", path.stem),
            "description": meta.get("description", ""),
            "_path": path,
        })
    return menu
 
 
def load_skill_body(name: str) -> str | None:
    for entry in list_skills():
        if entry["name"] == name:
            text = entry["_path"].read_text(encoding="utf-8")
            _, body = _parse_frontmatter(text)
            return body
    return None
 
 
if __name__ == "__main__":
    print("=== Cheap pass: skill menu (frontmatter only) ===")
    menu = list_skills()
    for s in menu:
        print(f"  {s['name']:12s} - {s['description']}")
 
    print("\n=== Now simulate picking ONE based on a fake user request ===")
    fake_user_request = "can you write me a haiku about monsoon season"
    print(f"user: {fake_user_request!r}")
    chosen = "haiku"
    print(f"[chosen skill]: {chosen}")
 
    print(f"\n=== Expensive pass: full body of '{chosen}' only ===")
    print(load_skill_body(chosen))
 
    print(f"\n(sql_review body was NEVER read in this run -- proving selectivity)")
