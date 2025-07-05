# generate_docs.py
import json
import builtins

docs = []

for name in dir(builtins):
    obj = getattr(builtins, name)
    doc = getattr(obj, '__doc__', '')
    if doc:
        docs.append({
            "id": f"builtin_{name}",
            "content": f"{name}:\n{doc}"
        })

with open('data/docs.json', 'w') as f:
    json.dump(docs, f, indent=2)
