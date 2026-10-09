"""A small, standard-library JSON Schema checker (draft 2020-12 subset).

ENGINEERING module for TP-03.  It exists so that `openpona validate-record` needs no
third-party dependency.  It implements ONLY the keywords the record profiles in
`schema/profiles/` use and raises `SchemaError` on any other keyword, so a schema can
never silently pass because a keyword was ignored.  The profile files are ordinary
2020-12 schemas: `jsonschema` (or any full validator) accepts them too, and
`tests/test_records.py` cross-checks the two when `jsonschema` is importable.

Supported: type, enum, const, required, properties, patternProperties,
additionalProperties (bool or schema), items, minItems, maxItems, uniqueItems,
minLength, maxLength, minimum, pattern, format (date-time), $ref (local `#/$defs/..`),
allOf, if/then (no else).  Annotations are ignored: $schema, $id, title, description,
$comment, $defs, default, examples.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

_ANNOTATIONS = {"$schema", "$id", "title", "description", "$comment", "$defs",
                "default", "examples"}
_KEYWORDS = _ANNOTATIONS | {
    "type", "enum", "const", "required", "properties", "patternProperties",
    "additionalProperties", "items", "minItems", "maxItems", "uniqueItems",
    "minLength", "maxLength", "minimum", "pattern", "format", "$ref", "allOf",
    "if", "then",
}
_RFC3339 = re.compile(
    r"^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(\.[0-9]+)?"
    r"(Z|[+-]([0-9]{2}):([0-9]{2}))$")


class SchemaError(ValueError):
    """The SCHEMA uses something this checker does not implement."""


@dataclass(frozen=True)
class SchemaIssue:
    keyword: str       # JSON Schema keyword that failed
    path: str          # JSON pointer of the offending instance part ("" = root)
    message: str
    detail: str = ""   # property name for required / additionalProperties
    conditional: bool = False   # raised inside an `if`/`then` branch


def is_rfc3339(value: str) -> bool:
    """RFC 3339 date-time (`T` separator, mandatory offset), calendar-valid."""
    m = _RFC3339.match(value)
    if not m:
        return False
    if m.group(4) is not None and (int(m.group(4)) > 23 or int(m.group(5)) > 59):
        return False
    try:
        datetime.fromisoformat(m.group(1))
    except ValueError:
        return False
    return True


def _type_ok(inst, name: str) -> bool:
    if name == "null":
        return inst is None
    if name == "boolean":
        return isinstance(inst, bool)
    if name == "integer":
        return isinstance(inst, int) and not isinstance(inst, bool)
    if name == "number":
        return isinstance(inst, (int, float)) and not isinstance(inst, bool)
    if name == "string":
        return isinstance(inst, str)
    if name == "array":
        return isinstance(inst, list)
    if name == "object":
        return isinstance(inst, dict)
    raise SchemaError(f"unknown type name {name!r}")


def _equal(a, b) -> bool:
    """JSON equality (True != 1)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return type(a) is type(b) and a == b


def _ptr(path: str, part) -> str:
    return f"{path}/{str(part).replace('~', '~0').replace('/', '~1')}"


def check(schema: dict, instance) -> list[SchemaIssue]:
    """All violations of `schema` by `instance` (empty list = valid)."""
    out: list[SchemaIssue] = []
    _walk(schema, instance, "", False, schema, out)
    return out


def _resolve(ref: str, root: dict) -> dict:
    if not ref.startswith("#/"):
        raise SchemaError(f"only local $ref supported, got {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise SchemaError(f"unresolvable $ref {ref!r}")
        node = node[part]
    return node


def _walk(schema, inst, path, cond, root, out) -> None:
    if schema is True or schema == {}:
        return
    if schema is False:
        out.append(SchemaIssue("false", path, "no value is allowed here", "", cond))
        return
    if not isinstance(schema, dict):
        raise SchemaError(f"schema must be an object, got {type(schema).__name__}")
    unknown = set(schema) - _KEYWORDS
    if unknown:
        raise SchemaError(f"unsupported schema keyword(s): {sorted(unknown)}")

    def add(kw, msg, detail=""):
        out.append(SchemaIssue(kw, path, msg, detail, cond))

    if "$ref" in schema:
        _walk(_resolve(schema["$ref"], root), inst, path, cond, root, out)
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(inst, n) for n in names):
            add("type", f"expected {' or '.join(names)}, got {type(inst).__name__}")
            return   # the remaining keywords assume the right type
    if "const" in schema and not _equal(inst, schema["const"]):
        add("const", f"must equal {schema['const']!r}")
    if "enum" in schema and not any(_equal(inst, v) for v in schema["enum"]):
        shown = repr(inst) if not isinstance(inst, (dict, list)) else type(inst).__name__
        add("enum", f"{shown} is not one of the {len(schema['enum'])} allowed values")
    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            add("minLength", f"shorter than {schema['minLength']}")
        if "maxLength" in schema and len(inst) > schema["maxLength"]:
            add("maxLength", f"longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            add("pattern", f"does not match {schema['pattern']}")
        if schema.get("format") == "date-time" and not is_rfc3339(inst):
            add("format", "not an RFC 3339 date-time")
        elif "format" in schema and schema["format"] != "date-time":
            raise SchemaError(f"unsupported format {schema['format']!r}")
    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            add("minimum", f"below {schema['minimum']}")
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            add("minItems", f"fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            add("maxItems", f"more than {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            for i, a in enumerate(inst):
                if any(_equal(a, b) for b in inst[:i]):
                    add("uniqueItems", f"item {i} duplicates an earlier item")
                    break
        if "items" in schema:
            for i, item in enumerate(inst):
                _walk(schema["items"], item, _ptr(path, i), cond, root, out)
    if isinstance(inst, dict):
        props = schema.get("properties", {})
        pats = schema.get("patternProperties", {})
        for name in schema.get("required", []):
            if name not in inst:
                add("required", f"missing required property {name!r}", name)
        for key, value in inst.items():
            matched = False
            if key in props:
                matched = True
                _walk(props[key], value, _ptr(path, key), cond, root, out)
            for pat, sub in pats.items():
                if re.search(pat, key):
                    matched = True
                    _walk(sub, value, _ptr(path, key), cond, root, out)
            if not matched and "additionalProperties" in schema:
                ap = schema["additionalProperties"]
                if ap is False:
                    out.append(SchemaIssue("additionalProperties", _ptr(path, key),
                                           f"unknown property {key!r}", key, cond))
                else:
                    _walk(ap, value, _ptr(path, key), cond, root, out)
    for sub in schema.get("allOf", []):
        _walk(sub, inst, path, cond, root, out)
    if "if" in schema:
        probe: list[SchemaIssue] = []
        _walk(schema["if"], inst, path, cond, root, probe)
        if not probe and "then" in schema:
            _walk(schema["then"], inst, path, True, root, out)
