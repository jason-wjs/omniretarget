from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (
    PROJECT_ROOT / "src" / "holosoma_retargeting",
    PROJECT_ROOT / "tests",
)
LEGACY_SRC_PREFIX = "holosoma_retargeting.src"
EXPECTED_LEGACY_REFERENCE_CENSUS = {
    "tests/test_module_entrypoints.py": ["dynamic_import"],
    "tests/test_solver_module_boundaries.py": ["dynamic_import"],
}


def _is_legacy_src_reference(module_name: str | None) -> bool:
    return module_name == LEGACY_SRC_PREFIX or (
        module_name is not None and module_name.startswith(f"{LEGACY_SRC_PREFIX}.")
    )

class LegacySrcReferenceCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.reference_categories: set[str] = set()
        self.module_level_string_constants: dict[str, str] = {}
        self.importlib_module_aliases: set[str] = {"importlib"}
        self.import_module_function_aliases: set[str] = {"import_module"}

    def visit_Module(self, node: ast.Module) -> None:
        for statement in node.body:
            self._record_module_level_constant(statement)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "importlib":
                self.importlib_module_aliases.add(alias.asname or alias.name)
            if _is_legacy_src_reference(alias.name):
                self.reference_categories.add("import")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "importlib":
            for alias in node.names:
                if alias.name == "import_module":
                    self.import_module_function_aliases.add(alias.asname or alias.name)
        if _is_legacy_src_reference(node.module):
            self.reference_categories.add("from_import")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_import_module_call(node.func):
            module_name = self._resolve_import_module_argument(node)
            if _is_legacy_src_reference(module_name):
                self.reference_categories.add("dynamic_import")
        self.generic_visit(node)

    def _record_module_level_constant(self, statement: ast.stmt) -> None:
        target_name: str | None = None
        value: ast.expr | None = None

        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                target_name = target.id
                value = statement.value
        elif isinstance(statement, ast.AnnAssign):
            if isinstance(statement.target, ast.Name):
                target_name = statement.target.id
                value = statement.value

        if target_name is None or value is None:
            return

        resolved = self._resolve_string_expression(value)
        if resolved is not None:
            self.module_level_string_constants[target_name] = resolved

    def _resolve_import_module_argument(self, node: ast.Call) -> str | None:
        if node.args:
            return self._resolve_string_expression(node.args[0])

        for keyword in node.keywords:
            if keyword.arg == "name":
                return self._resolve_string_expression(keyword.value)

        return None

    def _resolve_string_expression(self, expression: ast.expr) -> str | None:
        if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
            return expression.value

        if isinstance(expression, ast.Name):
            return self.module_level_string_constants.get(expression.id)

        if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
            left = self._resolve_string_expression(expression.left)
            right = self._resolve_string_expression(expression.right)
            if left is not None and right is not None:
                return left + right
            return None

        if isinstance(expression, ast.JoinedStr):
            parts: list[str] = []
            for value in expression.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                    continue
                if isinstance(value, ast.FormattedValue):
                    resolved = self._resolve_string_expression(value.value)
                    if resolved is None:
                        return None
                    parts.append(resolved)
                    continue
                return None
            return "".join(parts)

        return None

    def _is_import_module_call(self, function: ast.expr) -> bool:
        if isinstance(function, ast.Attribute):
            return (
                isinstance(function.value, ast.Name)
                and function.value.id in self.importlib_module_aliases
                and function.attr == "import_module"
            )
        return isinstance(function, ast.Name) and function.id in self.import_module_function_aliases


def _iter_python_sources() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        files.extend(root.rglob("*.py"))
    return sorted(files)


def _collect_legacy_src_reference_categories(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    collector = LegacySrcReferenceCollector()
    collector.visit(tree)
    return sorted(collector.reference_categories)


def test_src_compatibility_reference_census_matches_phase_allowlist() -> None:
    actual_census = {}
    for path in _iter_python_sources():
        categories = _collect_legacy_src_reference_categories(path)
        if categories:
            actual_census[str(path.relative_to(PROJECT_ROOT))] = categories

    assert actual_census == EXPECTED_LEGACY_REFERENCE_CENSUS, (
        "Unexpected legacy src reference census within configured scan roots. "
        f"Expected {EXPECTED_LEGACY_REFERENCE_CENSUS}, found {actual_census}."
    )
