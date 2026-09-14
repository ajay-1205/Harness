import json
from openai import OpenAI
import tools


def run_tool_choosing_turn(user_message: str, api_key: str,
                            model: str = "cohere/north-mini-code:free"):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    messages = [{"role": "user", "content": user_message}]

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools.TOOL_SCHEMAS,
    )

    choice = resp.choices[0].message

    if not choice.tool_calls:
        print(f"[model answered directly, no tool needed]\n{choice.content}")
        return

    for call in choice.tool_calls:
        name = call.function.name
        args = json.loads(call.function.arguments)  # model outputs args as a JSON STRING
        print(f"[model chose tool] {name}({args})")

        result = tools.dispatch(name, args)
        print(f"[tool result] {result}")

        # Feed the result back so the model can phrase a final answer
        messages.append(choice)
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": result,
        })

    final = client.chat.completions.create(model=model, messages=messages, tools=tools.TOOL_SCHEMAS)
    print(f"\n[final answer] {final.choices[0].message.content}")


if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else input("OpenRouter API key: ")

    print("=== Test 1: should trigger calculator ===")
    run_tool_choosing_turn("What is 47 times 12, minus 6?", key)

    print("\n=== Test 2: should trigger get_current_time ===")
    run_tool_choosing_turn("What time is it right now?", key)

    print("\n=== Test 3: should need NO tool ===")
    run_tool_choosing_turn("What's the capital of France?", key)