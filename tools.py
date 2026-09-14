import ast, operator
from datetime import datetime

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

def calculator(expression: str) -> str:
    tree = ast.parse(expression, mode='eval')
    result = _safe_eval(tree.body)
    return str(result)

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate.",
                    },
                },
                "required": ["expression"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
    }
]


_REGISTRY = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}

def dispatch(tool_name: str, arguments: dict) -> str:
    if tool_name not in _REGISTRY:
        return f"[error] no such tool: {tool_name}"
    fn = _REGISTRY[tool_name]
    try:
        return fn(**arguments)
    except Exception as e:
        return f"[error] {tool_name} failed: {e}"


if __name__ == "__main__":
    fake_model_decisions = [
        ("calculator", {"expression": "12 * (3 + 4)"}),
        ("get_current_time", {}),
        ("calculator", {"expression": "__import__('os').system('echo pwned')"}),  # should be rejected
        ("delete_everything", {}),  # tool that doesn't exist
    ]
 
    for name, args in fake_model_decisions:
        print(f"model wants: {name}({args})")
        print(f"  -> {dispatch(name, args)}\n")
