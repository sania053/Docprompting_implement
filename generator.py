from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class Generator:
    def __init__(self):
        model_name = "Salesforce/codegen-350M-mono"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def prompt_engineer(self, nl_intent, docs):
        docs_content = docs if isinstance(docs, list) else []

        if docs_content:
            print("\nRetrieved Documentation Used:")
            for i, doc in enumerate(docs_content):
                print(f"Doc {i+1}: {doc.strip()}\n")

            doc_section = '\n'.join(docs_content)
            documentation_prompt = f"Documentation:\n{doc_section}\n"
            return (
                f"You are a helpful code assistant.\n"
                f"{documentation_prompt}"
                f"Task: {nl_intent}\n"
                f"Write Python code to solve the task base on the provided documentation and your own pretrained knowledge.\n"
                f"Code:\n"
            )
        else:
            return (
                f"Write a Python function for the task: {nl_intent}.\n"
                f"Code:\n"
            )

    def generate(self, nl_intent, docs):
        prompt = self.prompt_engineer(nl_intent, docs)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=100, do_sample=False)
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return decoded.split("Code:")[-1].strip()
