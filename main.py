from datasets import load_dataset
from retriever import Retriever
from generator import Generator

def main():
    # Initialize components
    retriever = Retriever('data/docs.json')  # Assuming your docs are in this file
    generator = Generator()

    # User input
    user_input = input("Enter your task in natural language: ")
    print(f"Task: {user_input}")

    # Retrieve documents based on the input
    docs = retriever.retrieve(user_input)

    # With DocPrompting
    pred_with_docs = generator.generate(user_input, docs)
    print(f"Code with DocPrompting:\n{pred_with_docs}")

    # Without DocPrompting
    pred_without_docs = generator.generate(user_input, [])
    print(f"Code without DocPrompting:\n{pred_without_docs}")

    # Save generated code to compare with references later
    with open("predictions_with_docs.txt", "w") as f:
        f.write(pred_with_docs)
    
    with open("predictions_without_docs.txt", "w") as f:
        f.write(pred_without_docs)

if __name__ == "__main__":
    main()
