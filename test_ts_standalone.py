# test_ts_standalone.py
import sys
print(f"Python Executable: {sys.executable}") 

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language

    print(f"tree-sitter version: {tree_sitter.__version__ if hasattr(tree_sitter, '__version__') else 'unknown'}")
    # tree-sitter-languages doesn't have a standard __version__ usually
    print(f"tree_sitter.Language class: {Language}")
    print(f"tree_sitter_languages.get_language: {get_language}")

    lang_str = "python"
    print(f"Attempting to get language for: '{lang_str}'")
    lang_obj = get_language(lang_str) 
    print(f"SUCCESS: Got language object: {lang_obj}, type: {type(lang_obj)}")

    parser = Parser()
    print("Attempting to set language on parser...")
    parser.set_language(lang_obj) 
    print("SUCCESS: Language set on parser.")

    code_to_parse = "def hello():\n  print('world')"
    tree = parser.parse(bytes(code_to_parse, "utf8"))
    print(f"Parsed tree root S-expression: {tree.root_node.sexp()}")
    print("Standalone test successful!")

except Exception as e:
    print(f"Error in standalone tree-sitter test: {e}")
    import traceback
    traceback.print_exc()