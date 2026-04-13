from flask import Flask, jsonify, render_template, request
import clang.cindex  # Python bindings for libclang — lets us walk the C++ AST
import os
import tempfile

app = Flask(__name__)


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

    # get_children() gives us only the TOP-LEVEL nodes of the translation unit
    # (i.e. things declared directly in global scope: free functions, classes, globals)
    # This is intentional here — we only want free functions for the call graph
    for n in tu.cursor.get_children():

        # Filter to nodes that actually belong to THIS file
        # (libclang also surfaces nodes from #included headers — we skip those)
        if n.location.file and n.location.file.name == filepath:

            # FUNCTION_DECL = a free function definition or declaration
            # This does NOT match class methods (those are CXX_METHOD)
            if n.kind == clang.cindex.CursorKind.FUNCTION_DECL:

                calls[n.spelling] = []  # n.spelling = the function's name as a string

                # walk_preorder() does a full depth-first traversal of this function's
                # entire subtree — every statement, expression, and sub-expression
                for child in n.walk_preorder():

                    # CALL_EXPR = any function call site (foo(), obj.method(), etc.)
                    if child.kind == clang.cindex.CursorKind.CALL_EXPR:

                        # Only record calls that originate in this file
                        # (filters out calls to stdlib, headers, etc.)
                        if child.location.file and child.location.file.name == filepath:
                            calls[n.spelling].append(child.spelling)

    return calls


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    """
    GET  /graph  — renders the call graph for the bundled sp.cpp sample file
    POST /graph  — accepts a .cpp file upload, parses it, returns graph JSON

    Response shape:
        {
            "nodes": [{ "id": "functionName" }, ...],
            "links": [{ "source": "caller", "target": "callee" }, ...],
            "filename": "example.cpp"
        }

    Only links between KNOWN functions (nodes) are included —
    calls to stdlib or undefined functions are silently dropped.
    """

    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "no file"}), 400

        # Write the uploaded file to a temp path so libclang can read it from disk
        # (libclang needs a real file path, not a file object)
        tmp = tempfile.NamedTemporaryFile(suffix='.cpp', delete=False)
        file.save(tmp.name)
        filepath = tmp.name
        filename = file.filename
    else:
        # Default GET: use the bundled sample file
        filepath = 'sp.cpp'
        filename = 'sp.cpp'

    data = get_call_graph(filepath)

    # Build the node list — one node per known function
    known = set(data.keys())
    nodes = [{"id": k} for k in known]

    # Build the link list — only include edges where BOTH ends are known functions
    # This drops calls to stdlib, forward declarations, etc.
    links = []
    for caller, callees in data.items():
        for callee in callees:
            if callee in known:
                links.append({"source": caller, "target": callee})

    # Clean up the temp file after parsing
    if request.method == 'POST':
        os.unlink(filepath)

    return jsonify({"nodes": nodes, "links": links, "filename": filename})


if __name__ == '__main__':
    app.run(debug=True)
