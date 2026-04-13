# prototype/parse.py — Original matplotlib prototype (not used by the Flask server)
#
# This was the first working version of VizEx before the web UI existed.
# It parses sp.cpp, builds a NetworkX directed graph, and saves it as graph.png.
#
# Superseded by app.py + index.html (D3 frontend).
# Kept for reference — shows the evolution from static image to interactive web app.
#
# Run with: python parse.py
# (expects sp.cpp in the same directory, outputs graph.png)

import clang.cindex
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # non-interactive backend — renders to file without a display
import matplotlib.pyplot as plt

idx = clang.cindex.Index.create()
tu = idx.parse('sp.cpp')


def get_calls(source_file):
    """
    Same logic as get_call_graph() in app.py — walks top-level FUNCTION_DECLs
    and collects CALL_EXPRs within each function body.

    Returns a dict: { "functionName": ["callee1", "callee2", ...], ... }
    """
    calls = {}

    for n in tu.cursor.get_children():
        if n.location.file and n.location.file.name == source_file:
            if n.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                calls[n.spelling] = []
                for child in n.walk_preorder():
                    if child.kind == clang.cindex.CursorKind.CALL_EXPR:
                        if child.location.file and child.location.file.name == source_file:
                            calls[n.spelling].append(child.spelling)

    return calls


graph_data = get_calls('sp.cpp')

# Build a NetworkX directed graph from the call data
# NetworkX handles the graph structure; matplotlib handles rendering
G = nx.DiGraph()
for caller, callees in graph_data.items():
    for callee in callees:
        G.add_edge(caller, callee)  # adds both nodes and the edge between them

# spring_layout places nodes using a force-directed algorithm (same idea as D3's sim)
pos = nx.spring_layout(G)

nx.draw(G, pos,
    with_labels=True,
    node_color='lightblue',
    node_size=2000,
    font_size=10,
    arrows=True
)

plt.title("Call Graph - sp.cpp")
plt.savefig('graph.png')
print("Saved to graph.png")
