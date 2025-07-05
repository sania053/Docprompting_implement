from generator import Generator
from retriever import Retriever

import os
import subprocess 
import sys 


def get_evaluation_examples():
    
    examples = [
        {
            "id": "eval_001",
            "nl_intent": "Implement a function to perform a binary search on a sorted list and return the index of the element, or -1 if not found.",
            "reference_code": """def binary_search(sorted_list, target):
    low = 0
    high = len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        if sorted_list[mid] == target:
            return mid
        elif sorted_list[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1"""
        },
        {
            "id": "eval_002",
            "nl_intent": "Create a Python function to find the Nth Fibonacci number using recursion.",
            "reference_code": """def fibonacci_recursive(n):
    if n <= 0:
        raise ValueError("Input must be a positive integer")
    elif n == 1:
        return 0
    elif n == 2:
        return 1
    else:
        return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)"""
        },
        {
            "id": "eval_003",
            "nl_intent": "Write a function that takes a list of strings and returns a new list with all strings converted to uppercase.",
            "reference_code": """def uppercase_list_strings(string_list):
    return [s.upper() for s in string_list]"""
        }
        
    ]
    for ex in examples:
        ex["reference_code"] = ex["reference_code"].strip()
    return examples


def run_codebleu_script(refs_file, hyp_file, lang="python"):
    """
    Calls the calc_code_bleu.py script using subprocess.
    Assumes calc_code_bleu.py is in the same directory or in PATH.
    """
    script_path = "calc_code_bleu.py" 
    
    
    command = [
        sys.executable, 
        script_path,
        "--refs", refs_file,
        "--hyp", hyp_file,
        "--lang", lang
    ]
    print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("CodeBLEU Output:")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running CodeBLEU script for {hyp_file}:")
        print(e.stderr)
    except FileNotFoundError:
        print(f"Error: The script '{script_path}' was not found. Make sure it's in the correct path.")


def evaluate_codebleu():
    print("Initializing Generator and Retriever...")
    
    generator = Generator() 
    
    retriever = Retriever("data/docs.json") 

    examples = get_evaluation_examples()

    generated_code_with_docs_list = []
    generated_code_without_docs_list = []
    reference_codes_list = []

    print("\n--- Generating Code for Evaluation ---\n")

    for i, example in enumerate(examples, 1):
        nl_intent = example["nl_intent"]
        reference_code = example["reference_code"] 
        reference_codes_list.append(reference_code)

        print(f"Processing Example {i}/{len(examples)}: {nl_intent[:60]}...")

       
        retrieved_doc_contents = retriever.retrieve(nl_intent, top_k=3) 
        top_docs_for_generator = retriever.retrieve(nl_intent, top_k=3) 
                                                                   

        gen_with_docs_raw = generator.generate(nl_intent, top_docs_for_generator)
        
        generated_code_with_docs_list.append(gen_with_docs_raw) 

        
        gen_without_docs_raw = generator.generate(nl_intent, []) 
        
        generated_code_without_docs_list.append(gen_without_docs_raw)

        
    newline_placeholder = "<NEWLINE_CODEBLEU>"
    
    processed_refs = [r.replace("\n", newline_placeholder) for r in reference_codes_list]
    processed_hyps_with = [h.replace("\n", newline_placeholder) for h in generated_code_with_docs_list]
    processed_hyps_without = [h.replace("\n", newline_placeholder) for h in generated_code_without_docs_list]

    ref_file_path = "temp_refs.txt"
    hyp_with_file_path = "temp_hyps_with.txt"
    hyp_without_file_path = "temp_hyps_without.txt"

    with open(ref_file_path, "w", encoding="utf-8") as f:
        for line in processed_refs:
            f.write(line + "\n")
    with open(hyp_with_file_path, "w", encoding="utf-8") as f:
        for line in processed_hyps_with:
            f.write(line + "\n")
    with open(hyp_without_file_path, "w", encoding="utf-8") as f:
        for line in processed_hyps_without:
            f.write(line + "\n")
    
    print("\n=== Calculating CodeBLEU Scores via Script ===")
    print("\n--- With DocPrompting ---")
    run_codebleu_script(refs_file=ref_file_path, hyp_file=hyp_with_file_path, lang="python")
    
    print("\n--- Without DocPrompting ---")
    run_codebleu_script(refs_file=ref_file_path, hyp_file=hyp_without_file_path, lang="python")

    
    try:
        os.remove(ref_file_path)
        os.remove(hyp_with_file_path)
        os.remove(hyp_without_file_path)
        print("\nTemporary files cleaned up.")
    except OSError as e:
        print(f"Error removing temporary files: {e}")

if __name__ == "__main__":
    evaluate_codebleu()