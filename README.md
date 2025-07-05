# DocPrompting: Enhancing Code Generation with Documentation

This project is a simplified implementation of the **DocPrompting** research paper, which improves code generation from natural language (NL) intent by retrieving and incorporating relevant documentation during prompting.

## 🧠 Key Features

- Accepts NL intent from users at runtime
- Retrieves relevant documentation using TF-IDF and cosine similarity
- Generates Python code using a causal language model (CodeGen-350M-mono)
- Compares generations **with** and **without** documentation
- Evaluates performance using **CodeBLEU**



