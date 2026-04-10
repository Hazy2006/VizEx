from flask import Flask, jsonify, render_template
import clang.cindex

app = Flask(__name__)

def get_call_graph(filepath):
    idx = clang.cindex.Index.create()
    tu = idx.parse(filepath)
    calls = {}
    for n in tu.cursor.get_children():
        if n.location.file and n.location.file.name == filepath:
            if n.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                calls[n.spelling] = []
                for child in n.walk_preorder():
                    if child.kind == clang.cindex.CursorKind.CALL_EXPR:
                        if child.location.file and child.location.file.name == filepath:
                            calls[n.spelling].append(child.spelling)
    return calls

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/graph')
def graph():
    data = get_call_graph('sp.cpp')
    known = set(data.keys())
    nodes = [{"id": k} for k in known]
    links = []
    for caller, callees in data.items():
        for callee in callees:
            if callee in known:
                links.append({"source": caller, "target": callee})
    return jsonify({"nodes": nodes, "links": links})

if __name__ == '__main__':
    app.run(debug=True)
