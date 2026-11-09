import ast

from edd.taxonomy import ROOT


def test_the_workbench_never_imports_the_world_or_the_evaluation():
    bad = []
    for p in (ROOT / "src" / "edd").rglob("*.py"):
        for node in ast.walk(ast.parse(p.read_text())):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            )
            bad += [(p.name, n) for n in names if n.split(".")[0] in ("edd_world", "edd_eval")]
    assert bad == []
