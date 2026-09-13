from pathlib import Path
from openai import OpenAI

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


def append_fact(fact:str) -> bool:
    content = _read("memory.md")
    existing_lines = [l.strip() for l in content.splitlines()]
    bullet = f"- {fact.strip()}"

    if bullet in existing_lines:
        return False

    if "# Facts" not in content:
        content = "# Facts\n" + content if content else "# Facts"

    content = content.strip() + f"\n{bullet}\n"
    (MEMORY_DIR/"memory.md").write_text(content)
    print(f" [written] {fact!r}")
    return True


def enforce_budget():
    content = _read("MEMORY.md")
    if len(content) <= MEMORY_CHAR_BUDGET:
        return
 
    lines = content.splitlines()
    header = [l for l in lines if l.startswith("#")]
    facts = [l for l in lines if l.startswith("-")]
 
    print(f"  [!] MEMORY.md at {len(content)} chars, over budget of {MEMORY_CHAR_BUDGET}.")
    while facts and len("\n".join(header + facts)) > MEMORY_CHAR_BUDGET:
        dropped = facts.pop(0)  # oldest first
        print(f"  [evicted, FIFO -- not smart] {dropped}")
 
    new_content = "\n".join(header + facts) + "\n"
    (MEMORY_DIR / "MEMORY.md").write_text(new_content)


def enforce_budget_smart(api_key: str, model: str="nvidia/nemotron-3-ultra-550b-a55b:free"):
    content = _read("MEMORY.md")
    if len(content) <= MEMORY_CHAR_BUDGET:
        print("  [ok] under budget, no compaction needed")
        return

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    system = (
        "You curate a running memory file for a personal AI assistant. "
        f"The file must be reduced to under {MEMORY_CHAR_BUDGET} characters. "
        "Keep facts that are stable and identity-relevant (name, role, goals, "
        "standing preferences) over facts that are trivial or situational "
        "(tool preferences, one-off mentions). Preserve the '# Facts' heading. "
        "Output ONLY the revised markdown file content, no commentary, no code fences."
    )
    user = f"Current MEMORY.md ({len(content)} chars, budget {MEMORY_CHAR_BUDGET}):\n\n{content}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
    )
    revised = response.choices[0].message.content.strip()
    print(f"  [llm-compacted] {len(content)} -> {len(revised)} chars")
    (MEMORY_DIR / "MEMORY.md").write_text(revised + "\n", encoding="utf-8")
    return revised



if __name__ == "__main__":
    layers = load_memory_layers()
    prompt = build_system_prompt(layers)

    for name, content in layers.items():
        print(f"  {name:8s}: {len(content):4d} chars")

    print(f"\n=== Assembled system prompt ({len(prompt)}/{MEMORY_CHAR_BUDGET} char budget) ===\n")
    print(prompt)