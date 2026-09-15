import json
import sys
from openai import OpenAI
import skills


def _build_select_skill_tool(menu: list[dict]) -> dict:
    names = [s["name"] for s in menu]
    descriptions = "\n".join(f"- {s['name']}: {s['description']}" for s in menu)
    return {
        "type": "function",
        "function": {
            "name": "select_skill",
            "description": f"Pick the most relevant skill for the user's request.\nAvailable skills:\n{descriptions}",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "enum": names},
                },
                "required": ["skill_name"],
            },
        },
    }


def run_skill_routed_turn(user_message: str, api_key: str,
                           model: str = "cohere/north-mini-code:free"):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    menu = skills.list_skills()
    select_tool = _build_select_skill_tool(menu)

    routing_resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        tools=[select_tool],
        tool_choice={"type": "function", "function": {"name": "select_skill"}},  # force it to route
    )
    call = routing_resp.choices[0].message.tool_calls[0]
    chosen_name = json.loads(call.function.arguments)["skill_name"]
    print(f"[routed to skill] {chosen_name}")

    body = skills.load_skill_body(chosen_name)

    final_resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": body},
            {"role": "user", "content": user_message},
        ],
    )
    print(f"[final output]\n{final_resp.choices[0].message.content}")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else input("OpenRouter API key: ")

    print("=== Test 1: should route to haiku ===")
    run_skill_routed_turn("write me a haiku about monsoon season", key)

    print("\n=== Test 2: should route to sql_review ===")
    run_skill_routed_turn(
        "here's my query: SELECT * FROM orders WHERE user_id = 5; any issues?", key
    )