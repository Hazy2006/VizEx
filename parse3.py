# parse3.py — Standalone diagnostic script (not used by the Flask server)
#
# Purpose: quickly inspect what libclang sees in sp.cpp without running the
# full web server. Useful for debugging the parser or checking a new file.
#
# Run with: python parse3.py
# (expects sp.cpp to exist in the same directory)

import clang.cindex

idx = clang.cindex.Index.create()
tu = idx.parse('sp.cpp')  # parse into a Translation Unit (root of the AST)

# Walk every node in the entire AST (depth-first, preorder)
for node in tu.cursor.walk_preorder():

    # Only print FUNCTION_DECLs that belong to sp.cpp itself
    # (walk_preorder includes nodes from #included headers — we skip those)
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        if node.location.file and node.location.file.name == 'sp.cpp':
            print(f"Function: {node.spelling} at line {node.location.line}")
