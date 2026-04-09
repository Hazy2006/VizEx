import clang.cindex
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

idx = clang.cindex.Index.create()
tu = idx.parse('sp.cpp')

def get_calls(source_file):
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

G = nx.DiGraph()
for caller, callees in graph_data.items():
    for callee in callees:
        G.add_edge(caller, callee)

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, arrows=True)
plt.title("Call Graph - sp.cpp")
plt.savefig('graph.png')
print("Saved to graph.png")
