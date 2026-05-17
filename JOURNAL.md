# VizEx — Dev Journal

> A running log of what's been built, how it works, and where it's going.
> Updated after each significant milestone.

---

## Project Summary

**What it is:** Browser-based tool that parses C++ source files using libclang and renders interactive visualizations of code structure — function call graphs now, UML class diagrams next.

**Tagline:** VizEx is to Python Tutor what GeoGebra is to Maple.

**Why it exists:** Reading a C++ codebase cold is slow. VizEx gives you a structural map instantly — without reading it line by line.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML / CSS / D3.js v7 |
| Backend | Flask (Python) |
| Parsing | libclang Python bindings |
| Graph engine | D3 force simulation |
| IDE | PyCharm |
| Version control | GitHub + GitHub Desktop |

---

## File Map

### `app.py`
Flask entry point. Two routes:
- `GET /` — serves the frontend
- `POST /graph` — accepts a `.cpp` upload, writes it to a `tempfile`, calls the parser, returns graph JSON

Contains two parser functions:
- `get_call_graph(filepath)` — current, powers the function call graph
- `get_class_data(filepath)` — Phase 1, extracts class structure for UML

### `templates/index.html`
Single-page frontend. Sidebar with file upload + live metadata. SVG canvas rendered by D3 force simulation. Features: node drag, hover-to-highlight, neighbor dimming, directional arrowhead markers. No framework — vanilla JS + D3 v7.

### `parse3.py`
Standalone diagnostic script (not used by Flask). Runs libclang directly on `sp.cpp` and prints every `FUNCTION_DECL` with its line number. Used for debugging the parser without running the full server.

### `prototype/`
Earlier regex-based parser. Superseded by the libclang approach. Kept for reference.

---

## Data Flow

```
.cpp upload (browser)
  → POST /graph (Flask)
  → write to tempfile (libclang needs a real path, not a file object)
  → libclang Index.parse()
  → AST cursor traversal
  → JSON { nodes, links }
  → D3 force simulation
  → SVG render
  → os.unlink(tempfile)
```

---

## Parser Logic

### `get_call_graph()` — current
- Walks top-level `FUNCTION_DECL` nodes (free functions, global scope only)
- For each function, runs `walk_preorder()` over its subtree to find `CALL_EXPR` nodes
- Builds a `caller → [callees]` map
- Only links where both source and target are known functions are included
- **Limitation:** does not capture class methods (`CXX_METHOD`), lambdas, or nested functions

### `get_class_data()` — Phase 1
- Walks top-level `CLASS_DECL` nodes
- For each class, iterates `get_children()` and sorts by cursor kind:
  - `CXX_BASE_SPECIFIER` → base classes (inheritance)
  - `FIELD_DECL` → member variables (with type)
  - `CXX_METHOD` → methods (with return type)
- Returns a dict keyed by class name

Output shape per class:
```python
{
  "ClassName": {
    "bases":   ["BaseClass"],
    "fields":  [{"name": "x", "type": "int"}],
    "methods": [{"name": "foo", "return_type": "void"}]
  }
}
```

---

## Key AST Concepts

- The AST represents **syntactic containment**, not execution order
- `get_children()` on a `CLASS_DECL` yields its fields, methods, and base specifiers — not a call sequence
- `walk_preorder()` does a full depth-first traversal of a subtree
- `get_children()` on the root translation unit surfaces nodes from `#include`d headers — always filter by `node.location.file.name == filepath` to stay in-file only

---

## Build Log

### Phase 0 — ✅ Complete
**Function call graph (original scope)**

Regex-based parser, D3 force graph, browser file upload. Working demo with drag, zoom, sidebar metadata. Stored in `prototype/`.

---

### Phase 0.5 — ✅ Complete
**Migration to libclang + AST**

Replaced regex parsing with libclang Python bindings. `get_call_graph()` in `app.py` uses proper AST cursor traversal. All source files annotated with inline comments. `parse3.py` added as standalone debug tool.

---

### Phase 1 — 🚧 In Progress
**UML class diagram generation**

- [x] `get_class_data()` implemented — extracts classes, fields, methods, inheritance from AST
- [ ] Wire `get_class_data()` to a new `/classes` Flask route
- [ ] Build UML box renderer in D3 (frontend)
- [ ] Filter standard library noise
- [ ] Render inheritance relationship arrows
- [ ] Improve layout for larger files

---

### Phase 2 — Upcoming
**Features**

- [ ] Multi-file project support
- [ ] Recursive call highlighting
- [ ] Call depth filtering
- [ ] UI polish

---

### Phase 3 — Future
**Live execution**

- [ ] GDB/LLDB debugger integration
- [ ] Variable state display per step
- [ ] Stack frame visualization

---

## War Stories
The early prototype was built on Ubuntu. It was character-building.

- Terminal overhead — Linux CLI is unforgiving if you're not fluent. Wrong flags, wrong paths, cryptic errors. A lot of time went into just navigating the environment rather than building.
- libclang setup — getting the Python bindings to actually find the shared library (libclang.so) was painful. It doesn't just work out of the box; library paths, version - mismatches, and environment variables all conspire against you.
- Ego damage — the gap between "I'll just parse C++ files" and "ok why does libclang not see anything" is humbling.
SVG/D3 layout bugs — early graph renders had overlapping nodes and interfaces colliding. D3's force simulation needs tuning (charge strength, link distance, collision radius) before it looks like anything useful.

Eventually moved to PyCharm on Windows. Sanity partially restored.

---

## Open Decisions

- **UML layout:** force-directed (consistent with existing graph) or static hierarchical grid? Force looks familiar but may be harder to read for class boxes with many members.
- **Relationship scope:** inheritance is already extracted via `CXX_BASE_SPECIFIER`. Should Phase 1 also attempt composition/dependency detection?
- **Mode switching:** preserve the function call graph view alongside UML, or replace it? A toggle between "call graph" and "class diagram" modes is likely the cleanest UX.

---

*Last updated: 16 May 2025*
