"""يقسّم ملفًا إلى ملف لكل دالة/كلاس دون أن يلمس الأصل.
python split_functions.py المصدر.py اسم.الحزمة مجلد_الإخراج [--flat] [--map ملف.json] [--exclude a,b]"""
import ast
import builtins
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

GROUP_RULES = [
    ("auth", r"login|logout|register|signup|profile|password"),
    ("cart", r"cart"),
    ("orders", r"order|checkout|payment"),
    ("merchant", r"merchant|import|excel|dashboard|delete|edit|create|update|export|template"),
    ("products", r"product|search|category|home|detail|list"),
]
DEFAULT_GROUP = "misc"


def pick_group(name, mapping):
    if name in mapping:
        return mapping[name]
    for group, pattern in GROUP_RULES:
        if re.search(pattern, name, re.I):
            return group
    return DEFAULT_GROUP


def snake(name):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def bound_of(alias):
    return (alias.asname or alias.name).split(".")[0]


def bound_names(node):
    names = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            names.add(sub.id)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            names |= {bound_of(a) for a in sub.names}
    return names


def undefined_names(tree):
    known = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
    loaded = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            (loaded if isinstance(n.ctx, ast.Load) else known).add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            known.add(n.name)
        elif isinstance(n, ast.arg):
            known.add(n.arg)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            known |= {bound_of(a) for a in n.names}
        elif isinstance(n, ast.ExceptHandler) and n.name:
            known.add(n.name)
    return sorted(loaded - known)


def absolute_module(node, src_pkg):
    if node.level:
        base = src_pkg[: len(src_pkg) - (node.level - 1)]
        return ".".join(base + ([node.module] if node.module else []))
    return node.module


def build_imports(import_nodes, used, src_pkg):
    emitted, lines = set(), []
    for node in import_nodes:
        keep = []
        for a in node.names:
            b = "*" if a.name == "*" else bound_of(a)
            is_future = isinstance(node, ast.ImportFrom) and node.module == "__future__"
            if (b in used or b == "*" or is_future) and b not in emitted:
                keep.append(a)
                emitted.add(b)
        if not keep:
            continue
        if isinstance(node, ast.ImportFrom):
            new = ast.ImportFrom(module=absolute_module(node, src_pkg), names=keep, level=0)
        else:
            new = ast.Import(names=keep)
        lines.append(ast.unparse(new))
    lines.sort(key=lambda s: 0 if s.startswith("from __future__") else 1)
    return "\n".join(lines)


def find_cycles(graph):
    cycles, state = [], {}

    def dfs(n, path):
        state[n] = 1
        for m in graph.get(n, ()):
            if state.get(m) == 1:
                cycles.append(path[path.index(m):] + [m] if m in path else [n, m])
            elif m not in state:
                dfs(m, path + [m])
        state[n] = 2

    for n in graph:
        if n not in state:
            dfs(n, [n])
    return cycles


def parse_args():
    argv = sys.argv[1:]
    opts = {"flat": False, "map": None, "exclude": set()}
    pos, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--flat":
            opts["flat"] = True
        elif a == "--map":
            i += 1
            opts["map"] = argv[i]
        elif a == "--exclude":
            i += 1
            opts["exclude"] = {x.strip() for x in argv[i].split(",") if x.strip()}
        else:
            pos.append(a)
        i += 1
    if len(pos) != 3:
        print(__doc__)
        sys.exit(2)
    return pos, opts


def main():
    (source, package, out), opts = parse_args()
    source, out = Path(source), Path(out)
    flat, exclude = opts["flat"], opts["exclude"]
    mapping = {}
    if opts["map"]:
        for group, names in json.loads(Path(opts["map"]).read_text(encoding="utf-8")).items():
            for n in names:
                mapping[n] = group
    if out.exists() and any(out.iterdir()):
        sys.exit(f"مجلد الإخراج {out} غير فارغ. اختر مجلدًا جديدًا.")

    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text)
    src_pkg = package.split(".")[:-1]

    imports, others, defs, dups = [], [], {}, []
    for i, node in enumerate(tree.body):
        if i == 0 and isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
                and isinstance(node.value.value, str):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in defs:
                dups.append(defs[node.name])
            defs[node.name] = node
        else:
            others.append(node)

    def segment(node):
        start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        return "\n".join(lines[start - 1: node.end_lineno])

    active = {n: d for n, d in defs.items() if n not in exclude}
    is_class = {n: isinstance(d, ast.ClassDef) for n, d in active.items()}
    stem = {}
    for n in active:
        s = snake(n) if is_class[n] else n
        if s in stem.values():
            s += "_cls"
        stem[n] = s

    shared_names = set()
    for n in others:
        shared_names |= bound_names(n)
    shared_module = f"{package}._shared"
    location = {n: (None if flat else pick_group(n, mapping)) for n in active}

    def module_of(n):
        g = location[n]
        return f"{package}.{g}.{stem[n]}" if g else f"{package}.{stem[n]}"

    def names_used(node):
        return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}

    graph, warnings = {}, []
    out.mkdir(parents=True, exist_ok=True)

    for name, node in active.items():
        used = names_used(node)
        loaded = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        local = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Load)}
        local |= {a.arg for a in ast.walk(node) if isinstance(a, ast.arg)}
        real = loaded - local
        deps = sorted((real & set(active)) - {name})
        shared_used = sorted(real & shared_names)
        excluded_used = sorted((real & exclude) - {name})
        if excluded_used:
            warnings.append(f"{name} يستخدم دوالًا مستثناة: {', '.join(excluded_used)}")
        graph[name] = deps
        parts = []
        hdr = build_imports(imports, used, src_pkg)
        if hdr:
            parts.append(hdr)
        extra = [f"from {module_of(d)} import {d}" for d in deps]
        if shared_used:
            extra.append(f"from {shared_module} import {', '.join(shared_used)}")
        if extra:
            parts.append("\n".join(extra))
        body = ("\n\n".join(parts) + "\n\n\n" if parts else "") + segment(node) + "\n"
        folder = out / location[name] if location[name] else out
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{stem[name]}.py").write_text(body, encoding="utf-8")

    if others:
        used_in_others = set()
        for n in others:
            used_in_others |= names_used(n)
        hdr = build_imports(imports, used_in_others, src_pkg)
        body = (hdr + "\n\n\n" if hdr else "") + "\n\n".join(segment(n) for n in others) + "\n"
        (out / "_shared.py").write_text(body, encoding="utf-8")

    if dups:
        (out / "_duplicates").mkdir(exist_ok=True)
        for n in dups:
            hdr = build_imports(imports, names_used(n), src_pkg)
            body = (hdr + "\n\n\n" if hdr else "") + segment(n) + "\n"
            (out / "_duplicates" / f"{n.name}_line{n.lineno}.py").write_text(body, encoding="utf-8")

    ordered = sorted(active, key=lambda n: active[n].lineno)
    root_init, groups = [], {}
    if others:
        root_init.append("from . import _shared  # noqa: F401")
    for name in ordered:
        g = location[name]
        if g:
            groups.setdefault(g, []).append(name)
            root_init.append(f"from .{g}.{stem[name]} import {name}")
        else:
            root_init.append(f"from .{stem[name]} import {name}")
    (out / "__init__.py").write_text("\n".join(root_init) + "\n", encoding="utf-8")
    for g, names in groups.items():
        (out / g / "__init__.py").write_text(
            "\n".join(f"from .{stem[n]} import {n}" for n in names) + "\n", encoding="utf-8")

    bad = 0
    for f in sorted(out.rglob("*.py")):
        try:
            t = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            bad += 1
            print("خطأ صياغة في", f, exc)
            continue
        if f.name != "__init__.py" and "_duplicates" not in f.parts:
            und = [u for u in undefined_names(t) if u not in shared_names or f.name == "_shared.py"]
            if und:
                warnings.append(f"{f.relative_to(out)}: أسماء غير معرّفة: {', '.join(und)}")

    print(f"الملف المصدر: {len(defs) + len(dups)} دالة/كلاس")
    print(f"ملفات مولّدة: {len(active)}  |  مستثناة: {len(exclude & set(defs))}  |  "
          f"مكررة محفوظة: {len(dups)}  |  أسطر عامة في _shared: {len(others)}")
    for g, names in groups.items():
        print(f"  {g}/: {', '.join(names)}")
    for n in dups:
        print(f"  مكررة: {n.name} (السطر {n.lineno}) حُفظت في _duplicates/")
    cycles = find_cycles(graph)
    if cycles:
        warnings.append("دورات استيراد محتملة: " + " | ".join(" -> ".join(c) for c in cycles))
    if warnings:
        print("\nتنبيهات:")
        for w in warnings:
            print("  -", w)
    print("\nانتهى" if not bad else f"\n{bad} ملف فيه أخطاء")


if __name__ == "__main__":
    main()