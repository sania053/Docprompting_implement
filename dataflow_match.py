# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.

from tree_sitter import Language, Parser
from tree_sitter_languages import get_language # MODIFICATION: Import get_language

# Assuming DFG functions are correctly defined in a 'parser' directory/module
# Adjust these imports based on your actual project structure.
# If 'parser' is a directory with DFG.py and utils.py:
try:
    from parser.DFG import DFG_python,DFG_java,DFG_ruby,DFG_go,DFG_php,DFG_javascript,DFG_csharp
    from parser.utils import (remove_comments_and_docstrings,
                              tree_to_token_index,
                              index_to_code_token,
                              tree_to_variable_index)
except ImportError:
    # Fallback if parser is a .py file or structure is different
    # This might require you to ensure parser.py is in PYTHONPATH or similar
    # For example, if they are in a sibling 'parser.py' file:
    # from parser_module import DFG_python, ... (if parser.py is named parser_module.py)
    # Or if they are directly in a parser.py in the same dir (less common for modules):
    try:
        from parser.DFG import DFG_python,DFG_java,DFG_ruby,DFG_go,DFG_php,DFG_javascript,DFG_csharp
        from utils import (remove_comments_and_docstrings, # Assuming utils.py for these
                           tree_to_token_index,
                           index_to_code_token,
                           tree_to_variable_index)
    except ImportError as e:
        print(f"Could not import DFG functions or utils from parser. Error: {e}")
        print("Please ensure your 'parser' module/directory structure and imports are correct.")
        # Define them as None or raise error to indicate a critical missing component
        DFG_python = DFG_java = DFG_ruby = DFG_go = DFG_php = DFG_javascript = DFG_csharp = None
        remove_comments_and_docstrings = tree_to_token_index = index_to_code_token = tree_to_variable_index = None


import pdb # pdb import was in the original, keeping it.

dfg_function={
    'python':DFG_python,
    'java':DFG_java,
    'ruby':DFG_ruby,
    'go':DFG_go,
    'php':DFG_php,
    'javascript':DFG_javascript,
    'c_sharp':DFG_csharp,
}

def calc_dataflow_match(references, candidate, lang):
    # Ensure references is a list of lists for corpus_dataflow_match
    if isinstance(references, str):
        references = [[references]] # A single reference string
    elif isinstance(references, list) and references and isinstance(references[0], str):
        references = [references] # A list of reference strings for one candidate
    return corpus_dataflow_match(references, [candidate], lang)


def corpus_dataflow_match(references, candidates, lang):   
    # MODIFICATION: Initialize parser and set language using tree-sitter-languages
    ts_parser = Parser() # Renamed to ts_parser to avoid conflict with the list 'parser' below
    try:
        language_to_load = lang
        # Add mappings if lang argument differs from tree-sitter-languages naming
        if lang == 'c_sharp': 
            language_to_load = 'c_sharp'
        elif lang == 'javascript': # Example, if you use 'js' as lang arg
            language_to_load = 'javascript'
        # ... other potential mappings ...
            
        selected_language = get_language(language_to_load)
        ts_parser.set_language(selected_language)
    except Exception as e:
        print(f"Error setting language '{lang}' in dataflow_match.py using tree-sitter-languages: {e}")
        print(f"  Please ensure 'tree-sitter' and 'tree-sitter-languages' are installed.")
        print(f"  Supported languages include 'python', 'java', 'javascript', 'c_sharp', 'ruby', 'go', 'php'.")
        print(f"  Ensure your --lang argument (currently '{lang}') matches one of these.")
        return 0.0 # Return default score on critical error

    # The 'parser' variable in the original script was a list containing the
    # tree-sitter parser object and the language-specific DFG extraction function.
    # We will now use our configured ts_parser.
    # Also check if the DFG function for the lang is available.
    if lang not in dfg_function or dfg_function[lang] is None:
        print(f"Warning: DFG function for language '{lang}' is not available. Dataflow match will be 0.")
        return 0.0
        
    parser_and_dfg_func = [ts_parser, dfg_function[lang]] 
    
    match_count = 0
    total_count = 0

    for i in range(len(candidates)):
        references_sample = references[i] # list of reference strings for this candidate
        candidate = candidates[i] 
        
        for reference in references_sample:
            # MODIFICATION: Use the 'lang' parameter for remove_comments_and_docstrings
            # The original code hardcoded 'java', which was an error.
            candidate_cleaned = candidate
            reference_cleaned = reference
            if remove_comments_and_docstrings: # Check if function is available
                try:
                    candidate_cleaned = remove_comments_and_docstrings(candidate, lang)
                except: # Broad except from original
                    pass    
                try:
                    reference_cleaned = remove_comments_and_docstrings(reference, lang)
                except: # Broad except from original
                    pass  

            # Pass the parser_and_dfg_func list to get_data_flow
            cand_dfg = get_data_flow(candidate_cleaned, parser_and_dfg_func)
            ref_dfg = get_data_flow(reference_cleaned, parser_and_dfg_func)
            
            normalized_cand_dfg = normalize_dataflow(cand_dfg)
            normalized_ref_dfg = normalize_dataflow(ref_dfg)

            if len(normalized_ref_dfg) > 0:
                total_count += len(normalized_ref_dfg)
                # Create a copy of normalized_cand_dfg for modification if elements are removed
                # This ensures that if a candidate dataflow matches multiple reference dataflows (if allowed),
                # it's only counted once per unique candidate dataflow.
                # The original .remove() modifies the list being iterated over indirectly.
                # A safer way is to count available candidate dataflows.
                
                # Using a simpler matching: count how many ref dataflows are in cand_dataflows
                # For more precise "BLEU-like" dataflow matching, one might use collections.Counter
                # or ensure one-to-one matching if duplicates in ref_dfg shouldn't match same item in cand_dfg.
                # The original remove implies trying to match each ref_dfg item at most once.
                
                # Let's replicate the original logic with a mutable copy for cand_dfg
                temp_normalized_cand_dfg = list(normalized_cand_dfg) # Make a mutable copy

                for dataflow in normalized_ref_dfg:
                    if dataflow in temp_normalized_cand_dfg:
                            match_count += 1
                            temp_normalized_cand_dfg.remove(dataflow) # Remove from copy to ensure one-to-one match
    
    if total_count == 0:
        print("WARNING: There is no reference data-flows extracted from the whole corpus, and the data-flow match score degenerates to 0. Please consider ignoring this score.")
        return 0.0 # Return 0.0 not 0 to be consistent with float scores
        
    score = match_count / total_count
    return score

def get_data_flow(code, parser_info): # parser_info is the list [ts_parser_object, dfg_extraction_func]
    # Unpack the parser object and DFG function
    ts_parser = parser_info[0]
    dfg_extraction_func = parser_info[1]

    try:
        tree = ts_parser.parse(bytes(code,'utf8'))    
        root_node = tree.root_node  
        
        # Check if tree_to_token_index and index_to_code_token are available
        if not tree_to_token_index or not index_to_code_token:
            print("Warning: tree_to_token_index or index_to_code_token not available. Cannot extract detailed DFG.")
            return []

        tokens_index=tree_to_token_index(root_node)     
        code_lines=code.split('\n') # Renamed from 'code' to 'code_lines' to avoid conflict
        code_tokens=[index_to_code_token(x,code_lines) for x in tokens_index]  
        
        index_to_code={}
        for idx,(index,tok_code) in enumerate(zip(tokens_index,code_tokens)): # Renamed 'code' var here
            index_to_code[index]=(idx,tok_code)  
        
        try:
            # DFG,_=parser[1](root_node,index_to_code,{}) # Original used parser[1]
            DFG,_ = dfg_extraction_func(root_node,index_to_code,{}) 
        except Exception as e_dfg:
            # print(f"Warning: DFG extraction failed: {e_dfg}") # Optional debug
            DFG=[]
            
        DFG=sorted(DFG,key=lambda x:x[1])
        indexs=set()
        for d in DFG:
            if len(d[-1])!=0: # If it has outgoing edges
                indexs.add(d[1]) # Add current node's 'pos' (token index)
            for x in d[-1]: # For each target node 'pos' in outgoing edges
                indexs.add(x)
        
        new_DFG=[]
        for d in DFG:
            if d[1] in indexs: # Only keep dataflow items whose 'pos' is in 'indexs'
                new_DFG.append(d)
        
        # codes=code_tokens # 'codes' variable was not used further in original
        dfg=new_DFG
    except Exception as e_outer: # Broader exception for parsing or token indexing
        # print(f"Warning: Outer error in get_data_flow: {e_outer}") # Optional debug
        # codes=code.split() # 'codes' variable was not used further
        dfg=[]
        
    #merge nodes (original logic)
    dic={}
    for d in dfg:
        if d[1] not in dic: # d[1] is 'pos' (token index of the variable)
            dic[d[1]]=d
        else:
            # d is (var_name, var_pos, relationship_type, list_of_parent_var_names, list_of_parent_var_pos)
            # Merge if multiple entries for the same var_pos
            dic[d[1]]=(d[0],d[1],d[2],list(set(dic[d[1]][3]+d[3])),list(set(dic[d[1]][4]+d[4])))
    
    DFG_merged=[] # Renamed to avoid conflict with DFG from extraction
    for d_pos in dic: # Iterate over keys (var_pos)
        DFG_merged.append(dic[d_pos])
    dfg=DFG_merged # Assign merged DFG back to dfg
    return dfg

def normalize_dataflow_item(dataflow_item): # This function seems unused in the provided corpus_dataflow_match
    var_name = dataflow_item[0]
    var_pos = dataflow_item[1] # Unused in this normalization logic
    relationship = dataflow_item[2]
    par_vars_name_list = dataflow_item[3]
    # par_vars_pos_list = dataflow_item[4] # Unused in this normalization logic

    var_names = list(set(par_vars_name_list+[var_name]))
    norm_names = {}
    for i in range(len(var_names)):
        norm_names[var_names[i]] = 'var_'+str(i)

    norm_var_name = norm_names[var_name]
    # relationship = dataflow_item[2] # Redundant assignment
    norm_par_vars_name_list = [norm_names[x] for x in par_vars_name_list]

    return (norm_var_name, relationship, norm_par_vars_name_list)

def normalize_dataflow(dataflow):
    var_dict = {} # Maps original var names to normalized var_X names
    i = 0
    normalized_dataflow = []
    for item in dataflow: # item is (var_name, var_pos, relationship, parent_names, parent_pos)
        var_name = item[0]
        relationship = item[2]
        par_vars_name_list = item[3] # List of names of parent variables

        # Normalize parent variable names
        for name in par_vars_name_list:
            if name not in var_dict:
                var_dict[name] = 'var_'+str(i)
                i += 1
        # Normalize current variable name
        if var_name not in var_dict:
            var_dict[var_name] = 'var_'+str(i)
            i+= 1
        
        # Create the normalized tuple: (normalized_var_name, relationship, list_of_normalized_parent_names)
        normalized_dataflow.append((var_dict[var_name], relationship, [var_dict[x] for x in par_vars_name_list]))
    return normalized_dataflow