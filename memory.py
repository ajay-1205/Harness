from pathlib import Path

MEMORY_DIR = Path(__file__).parent/"memories"

MEMORY_CHAR_BUDGET = 2000

def _read(filename: str) -> str:
    path = MEMORY_DIR/filename
    if not path.exists():
        return ""
    return path.read_text().strip()

def load_memory_layers()-> dict:
    return{
        "soul": _read("Soul.md"),
        "memory": _read("memory.md"),
        "user": _read("user.md"),
    }

def build_system_prompt(layers: dict) -> str:
    parts = []
    if layers.get("soul"):
        parts.append(layers["soul"])
    if layers.get("memory"):
        parts.append(layers["memory"])
    if layers.get("user"):
        parts.append(layers["user"])
    return "\n\n".join(parts)

if __name__ == "__main__":
    layers = load_memory_layers()
    prompt = build_system_prompt(layers)

    for name, content in layers.items():
        print(f"  {name:8s}: {len(content):4d} chars")

    print(f"\n=== Assembled system prompt ({len(prompt)}/{MEMORY_CHAR_BUDGET} char budget) ===\n")
    print(prompt)