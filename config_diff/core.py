"""Load JSON / INI / TOML configs, flatten to dotted paths and compare values semantically."""
import configparser
import fnmatch
import json
import math
import os

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None


def _coerce(v):
    """INI values are strings: interpret numbers, booleans and null like JSON would."""
    s = v.strip()
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("none", "null", ""):
        return None
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    try:
        return json.loads(s)
    except ValueError:
        return s.strip("'\"")


def load_config(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    if ext == ".toml":
        if tomllib is None:
            raise RuntimeError("TOML support needs Python 3.11+ (tomllib)")
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    if ext in (".ini", ".cfg", ".conf"):
        cp = configparser.ConfigParser(interpolation=None)
        cp.optionxform = str
        cp.read(path, encoding="utf-8")
        out = {k: _coerce(v) for k, v in cp.defaults().items()}
        for sec in cp.sections():
            out[sec] = {k: _coerce(v) for k, v in cp.items(sec, raw=True) if k not in cp.defaults()}
        return out
    raise ValueError("unsupported config type %r (use .json, .toml, .ini/.cfg)" % ext)


def flatten(obj, prefix=""):
    """{'a': {'b': [1, {'c': 2}]}} -> {'a.b[0]': 1, 'a.b[1].c': 2}. Empty containers are kept as leaves."""
    out = {}
    if isinstance(obj, dict) and obj:
        for k, v in obj.items():
            out.update(flatten(v, "%s.%s" % (prefix, k) if prefix else str(k)))
    elif isinstance(obj, list) and obj:
        for i, v in enumerate(obj):
            out.update(flatten(v, "%s[%d]" % (prefix, i)))
    else:
        out[prefix] = obj
    return out


def _equal(a, b, rel_tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=0.0) if rel_tol else a == b
    return a == b


def diff(old, new, ignore=(), rel_tol=0.0):
    """Return list of (kind, path, old_value, new_value) with kind in added/removed/changed/type."""
    fa, fb = flatten(old), flatten(new)
    out = []
    for path in sorted(set(fa) | set(fb)):
        if any(fnmatch.fnmatch(path, pat) for pat in ignore):
            continue
        if path not in fb:
            out.append(("removed", path, fa[path], None))
        elif path not in fa:
            out.append(("added", path, None, fb[path]))
        elif not _equal(fa[path], fb[path], rel_tol):
            num = (int, float)
            same_kind = type(fa[path]) is type(fb[path]) or (isinstance(fa[path], num) and isinstance(fb[path], num)
                                                             and not isinstance(fa[path], bool) and not isinstance(fb[path], bool))
            out.append(("changed" if same_kind else "type", path, fa[path], fb[path]))
    return out


def _fmt(v):
    return json.dumps(v) if not isinstance(v, str) else repr(v)


def render_text(changes):
    sym = {"added": "+", "removed": "-", "changed": "~", "type": "!"}
    lines = []
    for kind, path, a, b in changes:
        if kind == "added":
            lines.append("+ %s = %s" % (path, _fmt(b)))
        elif kind == "removed":
            lines.append("- %s = %s" % (path, _fmt(a)))
        else:
            lines.append("%s %s: %s -> %s%s" % (sym[kind], path, _fmt(a), _fmt(b), "  (type changed)" if kind == "type" else ""))
    return "\n".join(lines)


def render_markdown(changes, old_name="old", new_name="new"):
    lines = ["| Parameter | %s | %s | |" % (old_name, new_name), "|---|---|---|---|"]
    for kind, path, a, b in changes:
        lines.append("| `%s` | %s | %s | %s |" % (path, "" if a is None and kind == "added" else _fmt(a),
                                                 "" if b is None and kind == "removed" else _fmt(b), kind))
    return "\n".join(lines) + "\n"
