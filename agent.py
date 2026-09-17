import sys
import json
from openai import OpenAI

import memory
import tools
import skills
import state

MODEL = "cohere/north-mini-code:free"

REMEMBER_TOOL = {
    "type": "function",
    "function": {
        "name": "remember_fact",
        "description": "Save one durable, stable fact about the user for future sessions. Do NOT use for trivia already in memory, or for one-off situational details.",
        "parameters": {
            "type": "object",
            "properties": {"fact": {"type": "string"}},
            "required": ["fact"],
        },
    },
}


def _select_skill_tool(menu):
    names = [s["name"] for s in menu]
    descriptions = "\n".join(f"- {s['name']}: {s['description']}" for s in menu)
    return {
        "type": "function",
        "function": {
            "name": "select_skill",
            "description": f"Route to a specialized skill if one clearly fits.\n{descriptions}",
            "parameters": {
                "type": "object",
                "properties": {"skill_name": {"type": "string", "enum": names}},
                "required": ["skill_name"],
            },
        },
    }


def run_turn(user_message: str, api_key: str, session_id: int, history_limit: int = 10):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    layers = memory.load_memory_layers()
    system_prompt = memory.build_system_prompt(layers)
    recent_history = state.get_recent_history(session_id, limit=history_limit)
    print(f"[phase 1] system prompt loaded ({len(system_prompt)} chars), "
          f"{len(recent_history)} prior messages pulled from state.db")

    menu = skills.list_skills()
    available_tools = tools.TOOL_SCHEMAS + [_select_skill_tool(menu)]

    messages = [
        {"role": "system", "content": system_prompt},
        *recent_history,
        {"role": "user", "content": user_message},
    ]
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, tools=available_tools, tool_choice="auto"
    )
    choice = resp.choices[0].message

    if choice.tool_calls:
        call = choice.tool_calls[0]
        name = call.function.name
        args = json.loads(call.function.arguments)

        if name == "select_skill":
            skill_body = skills.load_skill_body(args["skill_name"])
            print(f"[phase 2] routed to skill: {args['skill_name']}")
            final = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\n" + skill_body},
                    {"role": "user", "content": user_message},
                ],
            )
            answer = final.choices[0].message.content
        else:
            print(f"[phase 2] called real tool: {name}({args})")
            result = tools.dispatch(name, args)
            messages.append(choice)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            final = client.chat.completions.create(model=MODEL, messages=messages)
            answer = final.choices[0].message.content
    else:
        print("[phase 2] answered directly, no tool/skill needed")
        answer = choice.content

    print(f"\n[answer]\n{answer}\n")
    state.log_message(session_id, "user", user_message)
    state.log_message(session_id, "assistant", answer)


    #memory write-back
    extract_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Given this exchange, decide if there's a NEW durable fact about the user worth saving long-term. Call remember_fact only if something new and stable was revealed. Otherwise don't call any tool."},
            {"role": "user", "content": f"User said: {user_message}\nAgent answered: {answer}"},
        ],
        tools=[REMEMBER_TOOL],
    )
    extract_choice = extract_resp.choices[0].message
    if extract_choice.tool_calls:
        fact = json.loads(extract_choice.tool_calls[0].function.arguments)["fact"]
        print(f"[phase 3] extracted fact: {fact!r}")
        wrote = memory.append_fact(fact)
        if wrote:
            memory.enforce_budget_smart(api_key)
    else:
        print("[phase 3] nothing new worth remembering")


if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else input("OpenRouter API key: ")

    state.init_db()
    sid = state.create_session()
    print(f"=== session {sid} ===\n")

    print("--- Turn 1 ---")
    run_turn("What is 47 times 12, minus 6?", key, session_id=sid)

    print("--- Turn 2 (this ONLY works if turn 1 is actually remembered) ---")
    run_turn("Now divide that by 4.", key, session_id=sid)
