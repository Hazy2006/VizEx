import clang.cindex

idx = clang.cindex.Index.create()
tu = idx.parse('sp.cpp')

for node in tu.cursor.walk_preorder():
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        if node.location.file and node.location.file.name == 'sp.cpp':
            print(f"Function: {node.spelling} at line {node.location.line}")
