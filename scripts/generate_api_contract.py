"""Generate docs/API_CONTRACT.md from the FastAPI route definitions (static parse, no imports).

Run from the repo root:  python scripts/generate_api_contract.py
The hand-written preface is kept in docs/_api_preface.md.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "backend" / "app" / "api"
SCHEMAS = ROOT / "backend" / "app" / "schemas.py"
OUT = ROOT / "docs" / "API_CONTRACT.md"
METHODS = {"get", "post", "put", "patch", "delete"}
SKIP = {"db", "current_user", "request", "response", "_"}


def code_of(node):
    if isinstance(node, ast.Attribute):
        m = re.match(r"HTTP_(\d+)_", node.attr)
        return int(m.group(1)) if m else None
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value


def detail_of(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "code" and isinstance(v, ast.Constant):
                return f"object with code {v.value}"
        return "object"
    return "dynamic message"


def schema_classes():
    tree = ast.parse(SCHEMAS.read_text())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    default = f" = {ast.unparse(item.value)}" if item.value is not None else ""
                    fields.append(f"{item.target.id}: {ast.unparse(item.annotation)}{default}")
            out[node.name] = fields
    return out


def routes_of(path, classes):
    tree = ast.parse(path.read_text())
    prefix, tags = "", ""
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "APIRouter":
            for kw in node.value.keywords:
                if kw.arg == "prefix":
                    prefix = kw.value.value
                if kw.arg == "tags":
                    tags = ", ".join(e.value for e in kw.value.elts)
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for dec in fn.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in METHODS
                    and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router"):
                continue
            route = prefix + (dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else "")
            kw = {k.arg: k.value for k in dec.keywords}
            success = code_of(kw["status_code"]) if "status_code" in kw else 200
            model = ast.unparse(kw["response_model"]) if "response_model" in kw else None
            auth, params, body = "none", [], None
            args = fn.args.args
            defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
            for a, d in zip(args, defaults):
                ann = ast.unparse(a.annotation) if a.annotation else ""
                if isinstance(d, ast.Call):
                    fname = ast.unparse(d.func)
                    if fname == "Depends":
                        inner = ast.unparse(d.args[0])
                        if "require_roles" in inner:
                            auth = "Bearer token, roles: " + ", ".join(re.findall(r'"([^"]+)"', inner))
                        elif "get_current_user" in inner and auth == "none":
                            auth = "Bearer token"
                        continue
                    if fname in {"Query", "Form", "File", "Body"}:
                        req = "required" if d.args and isinstance(d.args[0], ast.Constant) and d.args[0].value is Ellipsis else \
                              f"default {ast.unparse(d.args[0])}" if d.args else "optional"
                        loc = "path" if "{%s}" % a.arg in route else fname.lower()
                        params.append((a.arg, ann, loc, req))
                        continue
                if a.arg in SKIP:
                    continue
                if "{%s}" % a.arg in route:
                    params.append((a.arg, ann, "path", "required"))
                elif ann in classes:
                    body = ann
                else:
                    params.append((a.arg, ann, "query", "optional" if d is not None else "required"))
            errors = []
            for call in [n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "HTTPException"]:
                ckw = {k.arg: k.value for k in call.keywords}
                c = code_of(ckw.get("status_code")) if "status_code" in ckw else None
                if c:
                    errors.append((c, detail_of(ckw["detail"]) if "detail" in ckw else ""))
            limits = [ast.unparse(d.args[0]) for d in fn.decorator_list
                      if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "limit" and d.args]
            doc = (ast.get_docstring(fn) or "").splitlines()[0] if ast.get_docstring(fn) else ""
            yield tags, dec.func.attr.upper(), route, doc, auth, params, body, success, model, sorted(set(errors)), limits


def main():
    classes = schema_classes()
    preface = (ROOT / "docs" / "_api_preface.md").read_text()
    lines = [preface.rstrip(), "", "## Endpoints (generated from the code)", ""]
    for f in sorted(API.glob("*.py")):
        if f.name == "__init__.py":
            continue
        for tags, method, route, doc, auth, params, body, success, model, errors, limits in routes_of(f, classes):
            lines += [f"### {method} {route}", ""]
            if doc:
                lines += [doc, ""]
            lines += [f"- Tag: {tags}", f"- Authentication: {auth}"]
            if limits:
                lines.append(f"- Rate limit: {', '.join(limits)}")
            for name, ann, loc, req in params:
                lines.append(f"- Parameter `{name}` ({loc}, {ann or 'str'}, {req})")
            if body:
                lines.append(f"- Request body (JSON): `{body}`")
            lines.append(f"- Success: {success}" + (f", response `{model}`" if model else ""))
            if errors:
                lines.append("- Errors raised in this handler: " + "; ".join(f"{c} {d}".strip() for c, d in errors))
            lines.append("")
    lines += ["## Schemas (from `backend/app/schemas.py`)", ""]
    for name, fields in classes.items():
        lines += [f"**{name}**", ""] + [f"- `{f}`" for f in fields] + [""]
    OUT.write_text("\n".join(lines) + "\n")
    print("wrote", OUT, "-", sum(1 for l in lines if l.startswith("### ")), "endpoints")


if __name__ == "__main__":
    main()
