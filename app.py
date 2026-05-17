from flask import Flask, jsonify, render_template, request
import clang.cindex  # Python bindings for libclang — lets us walk the C++ AST
import os
import tempfile

app = Flask(__name__)

def get_class_data(filepath):
    idx = clang.cindex.Index.create()
    tu = idx.parse(filepath)

    classes = {}
    norm_filepath = os.path.normcase(filepath)

    for n in tu.cursor.get_children():
        if n.location.file and os.path.normcase(n.location.file.name) == norm_filepath and n.kind == clang.cindex.CursorKind.CLASS_DECL:
            bases = []
            fields = []
            methods = []

            for child in n.get_children():
                if child.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER:
                    bases.append(child.spelling)
                elif child.kind == clang.cindex.CursorKind.FIELD_DECL:
                    fields.append({"name": child.spelling, "type": child.type.spelling})
                elif child.kind == clang.cindex.CursorKind.CXX_METHOD:
                    methods.append({"name": child.spelling, "return_type": child.result_type.spelling})

            classes[n.spelling] = {
                "bases": bases,
                "fields": fields,
                "methods": methods
            }

    return classes

def get_call_graph(filepath):
    """
    Parses a C++ file and returns a dict mapping each function to the list
    of functions it calls.

    Example output:
        {
            "main":  ["run"],
            "run":   ["greet"],
            "greet": []
        }

    Limitation: only detects FREE functions (top-level FUNCTION_DECLs).
    Class methods, lambdas, and nested functions are not picked up here.
    That's what get_class_data() (Phase 1 of roadmap) will address.
    """

    # Index is the entry point for libclang — one per parsing session
    idx = clang.cindex.Index.create()

    # Parse the file into a Translation Unit (the root of the AST)
    tu = idx.parse(filepath)

    calls = {}
    # os.path.normcase normalises slash direction on Windows so libclang's
    # forward-slash paths match Python's backslash tempfile paths
    norm_filepath = os.path.normcase(filepath)

    # get_children() gives us only the TOP-LEVEL nodes of the translation unit
    # (i.e. things declared directly in global scope: free functions, classes, globals)
    for n in tu.cursor.get_children():

        # Filter to nodes that actually belong to THIS file
        # (libclang also surfaces nodes from #included headers — we skip those)
        if n.location.file and os.path.normcase(n.location.file.name) == norm_filepath and n.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            calls[n.spelling] = []  # n.spelling = the function's name as a string

            # walk_preorder() does a full depth-first traversal of this function's
            # entire subtree — every statement, expression, and sub-expression
            for child in n.walk_preorder():

                # CALL_EXPR = any function call site (foo(), obj.method(), etc.)
                if child.kind == clang.cindex.CursorKind.CALL_EXPR and (child.location.file and os.path.normcase(child.location.file.name) == norm_filepath):
                    calls[n.spelling].append(child.spelling)

    return calls


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "no file"}), 400

        tmp = tempfile.NamedTemporaryFile(suffix='.cpp', delete=False)
        file.save(tmp.name)
        tmp.close()  # explicitly close before parsing (Windows requirement)
        filepath = tmp.name
        filename = file.filename

        try:
            data = get_call_graph(filepath)
        finally:
            try:
                os.unlink(filepath)
            except PermissionError:
                pass

        known = set(data.keys())
        nodes = [{"id": k} for k in known]
        links = []
        for caller, callees in data.items():
            for callee in callees:
                if callee in known:
                    links.append({"source": caller, "target": callee})

        return jsonify({"nodes": nodes, "links": links, "filename": filename})

    else:
        return jsonify({"nodes": [], "links": [], "filename": ""})


if __name__ == '__main__':
    app.run(debug=True)
