# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.

# Assuming DFG functions are correctly defined in a 'parser' directory/module
# If DFG_python etc. are in the same directory or a 'parser.py' file, adjust import
try:
    from .parser import DFG_python,DFG_java,DFG_ruby,DFG_go,DFG_php,DFG_javascript,DFG_csharp
    from .parser import (remove_comments_and_docstrings,
                       tree_to_token_index,
                       index_to_code_token,
                       tree_to_variable_index)
except ImportError: # Fallback if running as a script and parser is a sibling directory
    from parser.DFG import DFG_python,DFG_java,DFG_ruby,DFG_go,DFG_php,DFG_javascript,DFG_csharp
    from parser.utils import (remove_comments_and_docstrings,
                              tree_to_token_index,
                              index_to_code_token,
                              tree_to_variable_index)


from tree_sitter import Language, Parser
from tree_sitter_languages import get_language # MODIFICATION: Import get_language

dfg_function={
    'python':DFG_python,
    'java':DFG_java,
    'ruby':DFG_ruby,
    'go':DFG_go,
    'php':DFG_php,
    'javascript':DFG_javascript,
    'c_sharp':DFG_csharp, # Note: tree-sitter-languages uses 'c_sharp' for C#
}

def calc_syntax_match(references, candidate, lang):
    # Ensure references is a list of lists for corpus_syntax_match
    if isinstance(references, str):
        references = [[references]]
    elif isinstance(references, list) and references and isinstance(references[0], str):
        references = [references] # Make it list of lists if it's a flat list of ref strings
    return corpus_syntax_match(references, [candidate], lang)

def corpus_syntax_match(references, candidates, lang):   
    parser = Parser()
    
    # MODIFICATION: Load language using tree-sitter-languages
    try:
        # Ensure 'lang' matches the names used by tree-sitter-languages
        # Common names: 'python', 'java', 'ruby', 'go', 'php', 'javascript', 'c_sharp'
        # The 'lang' variable from args.lang in calc_code_bleu.py should be one of these.
        language_to_load = lang
        if lang == 'c_sharp': # tree_sitter_languages might expect 'c_sharp' or 'c-sharp'
            language_to_load = 'c_sharp' # Adjust if your lang string is different (e.g. 'csharp')
        elif lang == 'javascript':
            language_to_load = 'javascript' # or 'typescript' if you want to handle ts/tsx
            
        selected_language = get_language(language_to_load)
        parser.set_language(selected_language)
    except Exception as e:
        print(f"Error setting language '{lang}' using tree-sitter-languages: {e}")
        print(f"  Please ensure 'tree-sitter' and 'tree-sitter-languages' are installed.")
        print(f"  Supported languages include 'python', 'java', 'javascript', 'c_sharp', 'ruby', 'go', 'php'.")
        print(f"  Ensure your --lang argument (currently '{lang}') matches one of these.")
        # Depending on desired behavior, you might return a default score or re-raise
        return 0.0 # Default score indicating syntax match failure

    match_count = 0
    total_count = 0

    for i in range(len(candidates)):
        references_sample = references[i] # This is a list of reference strings for the i-th candidate
        candidate = candidates[i] 
        
        for reference in references_sample:
            # Use the 'lang' parameter for remove_comments_and_docstrings
            # The original code hardcoded 'java', which is likely an error.
            try:
                candidate_cleaned = remove_comments_and_docstrings(candidate, lang)
            except Exception as e_cand:
                # print(f"Warning: Could not remove comments/docstrings from candidate for lang '{lang}': {e_cand}")
                candidate_cleaned = candidate # Use original if cleaning fails
            try:
                reference_cleaned = remove_comments_and_docstrings(reference, lang)
            except Exception as e_ref:
                # print(f"Warning: Could not remove comments/docstrings from reference for lang '{lang}': {e_ref}")
                reference_cleaned = reference # Use original if cleaning fails

            try:
                candidate_tree = parser.parse(bytes(candidate_cleaned, 'utf8')).root_node
                reference_tree = parser.parse(bytes(reference_cleaned, 'utf8')).root_node
            except Exception as e_parse:
                # print(f"Warning: Tree-sitter parsing error for lang '{lang}': {e_parse}")
                # If parsing fails, we can't compare subtrees for this pair
                continue # Skip to the next reference or candidate

            def get_all_sub_trees(root_node):
                if root_node is None: # Handle cases where parsing might have failed subtly
                    return []
                node_stack = []
                sub_tree_sexp_list = []
                depth = 1
                node_stack.append([root_node, depth])
                while len(node_stack) != 0:
                    cur_node, cur_depth = node_stack.pop()
                    sub_tree_sexp_list.append([cur_node.sexp(), cur_depth])
                    # Original code had a bug: it would not traverse children if they themselves had no children.
                    # It should traverse all children to add them to the stack.
                    for child_node in cur_node.children:
                        # Only add to stack if it's a node that can be further expanded meaningfully
                        # For s-expression matching, typically all children are considered parts of subtrees
                        # The original condition `if len(child_node.children) != 0:` might be too restrictive.
                        # Let's add all children to the stack. The depth logic will handle tree structure.
                        # However, the original intent might have been to only consider non-terminal subtrees.
                        # Sticking to original logic for now, but this is a point of potential improvement/difference.
                        if len(child_node.children) != 0: # Original condition
                           depth = cur_depth + 1 # This depth increment seems off, should be independent of child's children
                           node_stack.append([child_node, cur_depth + 1]) # Corrected depth increment
                        else: # If it's a leaf in terms of complex subtrees, still add its s-expression
                            sub_tree_sexp_list.append([child_node.sexp(), cur_depth + 1])


                return sub_tree_sexp_list

            cand_sexps = [x[0] for x in get_all_sub_trees(candidate_tree)]
            ref_sexps_with_depth = get_all_sub_trees(reference_tree) # Keep depth for potential future use

            if not ref_sexps_with_depth: # If reference has no subtrees (e.g., empty or parse error)
                continue

            # Filter out very simple/common s-expressions if needed, or specific types
            # For now, direct matching as per original script's intent
            
            # Count matches
            for sub_tree_sexp, depth in ref_sexps_with_depth:
                if sub_tree_sexp in cand_sexps:
                     match_count += 1
            total_count += len(ref_sexps_with_depth)
    
    if total_count == 0:
        return 0.0 # Avoid division by zero if no reference subtrees were processed
        
    score = match_count / total_count
    return score