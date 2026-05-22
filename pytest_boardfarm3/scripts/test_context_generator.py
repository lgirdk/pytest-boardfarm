#!/usr/bin/env python3
"""Regenerate boardfarm3_pytest_generator.md.

Rules (HARD CONSTRAINTS, output format, style rules, pre-output self-check,
console-fallback notes) are hardcoded in this script as PRELUDE /
POSTLUDE / CONSOLE_FALLBACK_BLOCK below. They are policy and do not
depend on the current boardfarm3 source.

The Device API surface section is introspected at runtime from the
installed boardfarm3 template packages — no hardcoded template
signatures. When boardfarm3 templates change (new method, removed
method, signature change, return-type change), reinstall the latest
boardfarm3 and re-run this script.

Default-introspected package: `boardfarm3.templates`.
Add additional packages with `--package`, repeatable. Example:

    python test_context_generator.py
    python test_context_generator.py --package boardfarm3_docsis.templates
    python test_context_generator.py --package boardfarm3_docsis.templates --dry-run
    python test_context_generator.py --prompt PATH
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import logging
import pkgutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
ROOT = Path(__file__).resolve().parent
DEFAULT_PROMPT = ROOT / "docs/boardfarm3_pytest_generator.md"
DEFAULT_TEMPLATE_PACKAGE = "boardfarm3.templates"

# Composite templates (rendered as ##### under their parent ####).
NESTED_UNDER: dict[str, str] = {
    "CPEHW": "CPE",
    "CPESW": "CPE",
}


# ---------------------------------------------------------------------------
# PRELUDE — everything up to and including the API-surface intro / notation.
# Ends right before the first per-template subsection. The BEGIN marker is
# part of this block.
# ---------------------------------------------------------------------------

PRELUDE = """\
# Boardfarm3 pytest test generator — LLM prompt

A self-contained prompt that converts a requirements / specification
document into pytest test cases for the public **lgirdk boardfarm3**
framework. Every rule, convention, and device API needed is in this
file — no companion files, no web access required.

## How to use

Paste the block between `## SYSTEM PROMPT BEGIN` and `## SYSTEM PROMPT
END` into the model's **system-prompt slot**:

- **Claude Project** *Project instructions*
- **OpenAI Custom GPT** *Instructions*
- **Anthropic / OpenAI API** `system` field
- **Plain chat UI** — paste as the first user message (weaker, but the
  hard-constraint frontload and self-check still help).

Send your spec as the next user message. The model returns one fenced
```python``` block per test, each preceded by a `### test_<name>.py`
heading. Save each as that filename in your `tests/` directory.

---

## SYSTEM PROMPT BEGIN

You are an automation engineer producing **pytest** test cases for the
public **lgirdk boardfarm3** framework. The user message contains a
requirements / specification document describing one or more Jira test
cases. Convert every test the spec describes into a complete pytest
file in a single response. Do not ask the user for files, signatures,
or clarification.

### Hard constraints (strict — non-negotiable)

1. **Every device call must invoke a real method listed in the "Device
   API surface" section below.** That section is the only source of
   method names and signatures — your training data is unreliable for
   this framework.

   Workflow for every device operation:

   a. Identify the Template ABC for the device (LAN, WAN, CPE, ACS,
      WLAN, SIPPhone, etc. — listed below with import paths).
   b. Find the method in the device's subsection by **the operation it
      performs**, not by the name you would expect. Method names in
      this framework are frequently abbreviations / acronyms / non-PEP-8.
   c. Use the method name **verbatim, including case**. UPPERCASE
      acronyms (`GPV`, `SPV`, `AO`, `RB`, `FR`, …), MixedCase,
      snake_case — all preserved exactly as listed. **Do NOT normalise
      to PEP-8 snake_case.** Writing `acs.gpv(...)` when the API says
      `GPV` is a hallucination.
   d. Use the exact argument list shown, including every required
      keyword argument (`cpe_id`, `timeout`, typed input tuples, etc.).
      Many methods take arguments your training would omit; include
      them all.

   If no method in the device's subsection matches the operation,
   choose the closest semantic equivalent that IS listed. Do NOT
   invent a method name, do NOT substitute one from training-data
   canonical-API conventions (`set_parameter_values`, `add_object`,
   `ssh_login`, `curl`, `http_request`, `dhcp_renew`, `wifi_connect`,
   `factory_reset`, …), and do NOT shell out via `execute_command`
   (see rule 5).

2. **Every assertion must respect the method's actual return type as
   shown in the API surface below.**

   - `-> bool` → assert the call directly:
         `assert device.method(...), "Step1 FAILED: ..."`
   - `-> str` → assert content (substring or equality).
   - `-> int` → assert against the status / count value the
     description implies. Do NOT treat as truthy unless documented.
   - `-> dict` or `-> list[dict]` → index by keys consistent with the
     domain. Do not invent keys.
   - `-> <CustomType>` (dataclasses, named tuples, response objects
     such as `HTTPResult`, `GpvResponse`, `IPv4Address`, etc.) → treat
     the return as that type. **The type body is not visible to you.**
     Two forbidden patterns:
       1. **Inventing attribute / key access** — do NOT write
          `result.value`, `result.params`, `result["key"]`,
          `result[0]`, etc. from a guess about the type's structure.
       2. **Stringify-then-match** — do NOT convert the return to a
          string and search it. The string form of a custom type
          (whatever `__str__` / `__repr__` produces) is NOT part of
          the type's contract; matching on it is the same
          hallucination as inventing an attribute, just laundered
          through `str()`. Forbidden expressions include:
              `str(result).lower()`, `repr(result)`,
              `f"{result}"`, `"foo" in str(result)`,
              `"foo" in f"{result}"`, `str(result) == "..."`, etc.

     Instead:
       * Prefer a **roundtrip** assertion — perform the operation and
         then verify with a sibling method whose return type IS
         concrete (`-> bool`, `-> str`, `-> int`).
       * Or treat the return as opaque and assert `is not None`
         (or truthiness when the description implies the response is
         falsy on failure).
   - `-> None` → do NOT assert the return value. Assert a *side
     effect* — a subsequent state read, a property getter, a log line.
   - Union (`-> bool | dict`, etc.) → branch on the variant you
     actually receive, or invoke the default variant the description
     implies.

   Never write assertions that depend on a return shape the annotation
   does not imply. The annotation in the API surface is the contract.

3. **Import devices ONLY via their Template ABC** and resolve them
   with `device_manager.get_devices_by_type(<Template>)`. The fixture
   returns `dict[str, <Template>]` keyed by inventory name.

   Single-device idiom:

       from boardfarm3.templates.lan import LAN

       def test_x(device_manager):
           lan = next(iter(device_manager.get_devices_by_type(LAN).values()))

   Multi-device idiom:

       for name, wlan in device_manager.get_devices_by_type(WLAN).items():
           ...

   NEVER import concrete device classes (`LinuxLan`, `GenieACS`,
   vendor-specific subclasses). Only Template ABCs from
   `boardfarm3.templates.*`.

4. **NEVER import from `boardfarm3.use_cases.*` or
   `boardfarm3_docsis.use_cases.*`.** The substring `use_cases` must
   not appear anywhere in the generated file — not in imports, not in
   `importlib` strings, not in comments. Use the device's Template ABC
   method instead (rule 1).

5. **NEVER call `execute_command` (or any pexpect / console method) on
   a device.** Generated tests must use the Template ABC methods in
   the API surface below — that is the only permitted interface.
   Shelling out via `device.execute_command(...)`,
   `device.console.execute_command(...)`,
   `device._console.execute_command(...)`,
   `device.console.sendline(...)`, or `device.console.expect(...)`
   is forbidden. The same applies to `*_async` variants.

   If a step has no exact Template ABC method, use the closest
   semantic equivalent that IS listed. If absolutely nothing fits,
   note the gap in the trailing "Notes" section explaining what
   method would be needed — do NOT bypass the abstraction with
   `execute_command`.

6. **NEVER emit `@pytest.mark.env_req(...)` or any other pytest mark.**
   Test functions are plain pytest functions: `def test_<name>(<fixtures>):`.

   Available fixtures:
   - `device_manager` — preferred entry point.
   - `boardfarm_config`, `bf_context`, `bf_logger` — config / per-test
     scratch / step logger.
   - `devices` — legacy; prefer `device_manager`.

7. **NEVER emit `TODO`, `assert False`, `pytest.skip(...)`,
   `pytest.xfail(...)`, or commented-out placeholder code.**

8. **NEVER emit a `class ...:` statement in the generated file.**
   The Device API surface below lists methods that *already exist* on
   boardfarm3's Template ABCs — your job is to import the Template and
   call its methods inside a `def test_<name>(device_manager):`
   function, **not to redefine the Template or write any class of your
   own**. Generated files must contain only the module docstring,
   imports, module-level constants/helpers (if any), and the test
   function. No `class` keyword anywhere.

9. **Generate every test in a single response. Do not ask the user.**

---

### Device API surface (authoritative — use ONLY these method names)

<!-- BEGIN AUTO-GENERATED API SURFACE -->
The listings below are the complete public surface of every device
Template ABC. Method names, argument lists, and return-type annotations
are the contract; do not substitute any from training.

Notation:
- `attr -> type` is a property (accessed without parentheses).
- `method(args) -> type` is a callable.
- Default-valued args are shown with their defaults (`arg=default`).
- All ACS RPC methods take an optional `cpe_id: str | None = None`
  keyword. Pass `cpe.sw.cpe_id` (CPE software template) when the spec
  requires targeting a specific CPE.

"""


# ---------------------------------------------------------------------------
# POSTLUDE — everything from the END marker to the end of the file.
# ---------------------------------------------------------------------------

POSTLUDE = """\
<!-- END AUTO-GENERATED API SURFACE -->

---

### Output format

For each test in the spec:

    ### test_<snake_case>.py
    ```python
    <full file contents>
    ```

If the spec describes N tests, emit N such blocks. If any spec ambiguity
required a judgment call (default port, timeout, etc.), append a short
"Notes" section at the end. Otherwise emit nothing else.

### Style rules

1. **Module docstring** lists the Jira steps verbatim:

       \"\"\"
       Jira Test Steps:
           Step1 Action:          <action>
           Step1 Expected Result: <expected>
       \"\"\"

2. **Imports** — `import pytest`, then the Template ABCs for every
   device the test uses. Add stdlib or `requests` imports only when an
   inline helper actually requires them.

3. **Devices** — resolve with the idiom from HARD CONSTRAINT #3. Type
   hints are fine but not required; the resolved variable is already
   the right type.

4. **Test body**
   - One-line docstring summarising the test.
   - One comment per Jira step: `# Step <N>: <one-line description>`.
   - Group atomically-related steps inside the same `with` block when
     the spec describes them as one transaction.

5. **Per-step assertion.** Every Jira step ends with:

       assert <expr>, "Step<N> FAILED: <human-readable reason>"

   The expression shape MUST follow HARD CONSTRAINT #2. For `-> None`
   methods, assert a *side effect* — never silently skip.

6. **Inline helpers** — define `_helper_name` above the test only when
   no API-surface method covers the step. Helpers use stdlib or
   `requests` only.

7. **Module-level constants** — ports, paths, default credentials,
   timeouts go above any helpers, named with a leading underscore.

8. **Minimal and deterministic.** Don't invent attributes or methods
   not listed in the API surface. Don't add retries / fallbacks /
   "just in case" logic the spec doesn't require.

### Pre-output self-check — run silently before sending

Re-read each generated file. If any check fails, rewrite before sending.

- [ ] **Every `device.<method>(...)` call appears in the API surface
      above** — method name AND every required argument shown there.
      No method and no argument came from a training-data guess.
- [ ] **Method names match the API surface byte-for-byte, including
      case.** No lowercase normalisation of acronyms.
- [ ] **Every assertion respects the method's return-type annotation
      from the API surface.** No dict-key access on a typed-object
      return; no truthiness check on a `-> None` return; no substring
      match on a `-> bool` return.
- [ ] **No invented access on a custom-type return.** No
      `result.<field>`, no `result["key"]`, no `result[0]`, AND no
      stringify-then-match workaround (`str(result)`, `repr(result)`,
      `f"{result}"`, `"foo" in str(result)`, etc.). You either
      roundtripped via a concrete-typed sibling method or treated the
      return as opaque (`is not None` / truthiness).
- [ ] Devices resolved with `device_manager.get_devices_by_type(<Template>)`
      using `next(iter(...values()))` (single) or `.items()` (multiple).
      No `get_device_by_type("string")` form.
- [ ] Only Template ABCs imported from `boardfarm3.templates.*`. No
      concrete device classes.
- [ ] Substring `use_cases` absent from the file.
- [ ] Substring `@pytest.mark` absent.
- [ ] **No `class ` keyword anywhere in the file** — the output is a
      pytest test function, not a class. The Device API surface is a
      reference, not code to redefine.
- [ ] No `TODO`, `assert False`, `pytest.skip`, `pytest.xfail`.
- [ ] **Substring `execute_command` absent from the file** — no
      `device.execute_command(...)`, no `device.console.execute_command(...)`,
      no `device._console.execute_command(...)`, no `sendline` /
      `expect` calls on a device's console. Tests use Template ABC
      methods only (HARD CONSTRAINT #5).
- [ ] Every Jira step in the docstring has a matching
      `assert <expr>, "Step<N> FAILED: ..."` in the body.

## SYSTEM PROMPT END
"""


# ---------------------------------------------------------------------------
# Template discovery
# ---------------------------------------------------------------------------


def discover_templates(packages: list[str]) -> list[type]:
    """Walk each package root and return classes defined there."""
    found: dict[str, type] = {}
    for pkg_name in packages:
        try:
            pkg = importlib.import_module(pkg_name)
        except ImportError:
            continue
        if not hasattr(pkg, "__path__"):
            continue
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            pkg.__path__, prefix=pkg.__name__ + "."
        ):
            try:
                mod = importlib.import_module(modname)
            except Exception as exc:  # noqa: BLE001
                logger.warning("failed to import %s: %s", modname, exc)
                continue
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if obj.__module__ != modname:
                    continue
                if name.startswith("_"):
                    continue
                found[f"{obj.__module__}.{obj.__name__}"] = obj
    return list(found.values())


def is_template_abc(cls: type) -> bool:
    """Ensure Template ABC has at least one public method or property."""
    for name, member in cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(member, property) or inspect.isfunction(member):
            return True
    return False


def has_public_console(cls: type) -> bool:
    """Check console.

    Ensure True if the class (or any base in MRO)
    defines a public `console` property
    """
    for klass in cls.__mro__:
        if isinstance(klass.__dict__.get("console"), property):
            return True
    return False


# ---------------------------------------------------------------------------
# Signature rendering (compact style: no per-arg type annotations; defaults
# shown with double-quoted strings to match the prompt's existing format)
# ---------------------------------------------------------------------------


def _format_default(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        if '"' in value and "'" not in value:
            return repr(value)
        return f'"{value}"'
    return repr(value)


def _format_param(p: inspect.Parameter) -> str:
    """`name` or `name=default`. Type annotations intentionally stripped."""
    if p.kind == inspect.Parameter.VAR_POSITIONAL:
        return f"*{p.name}"
    if p.kind == inspect.Parameter.VAR_KEYWORD:
        return f"**{p.name}"
    s = p.name
    if p.default is not inspect.Parameter.empty:
        s += f"={_format_default(p.default)}"
    return s


def _format_signature(func: Callable) -> tuple[str, str]:
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return "...", ""
    args = ", ".join(
        _format_param(p)
        for name, p in sig.parameters.items()
        if name not in {"self", "cls"}
    )
    if sig.return_annotation is inspect.Signature.empty:
        ret = "None"
    else:
        ret = inspect.formatannotation(sig.return_annotation)
    return args, ret


def get_members(cls: type) -> list[dict]:
    """Public members of cls (properties first, then methods, alphabetical)."""
    seen: set[str] = set()
    members: list[dict] = []
    for klass in cls.__mro__:
        if klass is object:
            break
        for name, member in klass.__dict__.items():
            if name.startswith("_"):
                continue
            if name in seen:
                continue
            seen.add(name)
            if isinstance(member, property):
                if member.fget is None:
                    continue
                _args, ret = _format_signature(member.fget)
                members.append(
                    {"kind": "property", "name": name, "args": "", "ret": ret}
                )
            elif inspect.isfunction(member):
                args, ret = _format_signature(member)
                members.append(
                    {"kind": "method", "name": name, "args": args, "ret": ret}
                )
    members.sort(key=lambda m: (0 if m["kind"] == "property" else 1, m["name"]))
    return members


# ---------------------------------------------------------------------------
# Per-template rendering
# ---------------------------------------------------------------------------


def render_template(cls: type, members: list[dict]) -> str:
    """Render template."""
    nested = cls.__name__ in NESTED_UNDER
    heading = "#####" if nested else "####"
    pc_str = "yes" if has_public_console(cls) else "no"
    import_line = f"from {cls.__module__} import {cls.__name__}"
    out = [
        f"{heading} {cls.__name__} — `{import_line}`  ·  Public console: {pc_str}",
        "",
    ]
    for m in members:
        if m["kind"] == "property":
            out.append(f"- `{m['name']} -> {m['ret']}`")
        else:
            out.append(f"- `{m['name']}({m['args']}) -> {m['ret']}`")
    return "\n".join(out)


def _order_templates(
    templates: list[tuple[type, list[dict]]],
) -> list[tuple[type, list[dict]]]:
    """Alphabetical by class name; nested children placed right after their parent."""
    by_name = {cls.__name__: (cls, members) for cls, members in templates}
    placed: set[str] = set()
    ordered: list[tuple[type, list[dict]]] = []
    top_level = sorted(
        (t for t in templates if t[0].__name__ not in NESTED_UNDER),
        key=lambda t: t[0].__name__,
    )
    for cls, members in top_level:
        if cls.__name__ in placed:
            continue
        ordered.append((cls, members))
        placed.add(cls.__name__)
        children = sorted(
            child_name
            for child_name, parent_name in NESTED_UNDER.items()
            if parent_name == cls.__name__ and child_name in by_name
        )
        for child_name in children:
            if child_name not in placed:
                ordered.append(by_name[child_name])
                placed.add(child_name)
    # Append any leftovers (nested whose parent wasn't discovered, etc.).
    leftover = sorted(
        (t for t in templates if t[0].__name__ not in placed),
        key=lambda t: t[0].__name__,
    )
    ordered.extend(leftover)
    return ordered


def render_api_surface(templates: list[tuple[type, list[dict]]]) -> str:
    """Per-template subsections. No surrounding markers.

    Note: no console / pexpect fallback block is rendered. HARD CONSTRAINT
    #5 forbids `execute_command`, so the API surface intentionally does
    not document it.
    """
    parts: list[str] = []
    for cls, members in _order_templates(templates):
        parts.append(render_template(cls, members))
        parts.append("")  # blank line between subsections
    # Trim the final trailing blank so POSTLUDE starts cleanly with the
    # END marker on the next line.
    if parts and parts[-1] == "":
        parts.pop()
    return "\n".join(parts) + "\n"


def assemble_md(templates: list[tuple[type, list[dict]]]) -> str:
    """Combine PRELUDE + introspected API surface + POSTLUDE."""
    return PRELUDE + render_api_surface(templates) + POSTLUDE


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the application."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--prompt",
        type=Path,
        default=DEFAULT_PROMPT,
        help=f"Output path (default: {DEFAULT_PROMPT.name})",
    )
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        metavar="PACKAGE",
        help=(
            "Additional template package to introspect (repeatable). "
            f"`{DEFAULT_TEMPLATE_PACKAGE}` is always included. "
            "Example: --package boardfarm3_docsis.templates"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the .md to stdout instead of writing.",
    )
    args = parser.parse_args(argv)

    packages = [DEFAULT_TEMPLATE_PACKAGE, *list(args.package)]
    classes = discover_templates(packages)
    if not classes:
        logger.error(
            "error: no template classes discovered in:\n%s"
            "Make sure the packages are installed in this Python environment,\n"
            "e.g.:\n"
            "    pip install boardfarm3\n"
            "    pip install boardfarm3-docsis    # if using docsis templates",
            "".join(f"  - {p}\n" for p in packages),
        )
        return 3

    templates: list[tuple[type, list[dict]]] = []
    for cls in classes:
        if not is_template_abc(cls):
            continue
        members = get_members(cls)
        if not members:
            continue
        templates.append((cls, members))

    if not templates:
        logger.info(
            "error: discovered classes but none had public members", file=sys.stderr
        )
        return 3

    content = assemble_md(templates)

    if args.dry_run:
        sys.stdout.write(content)
        return 0

    if args.prompt.exists() and args.prompt.read_text(encoding="utf-8") == content:
        logger.info("no changes in %s", args.prompt.name)
        return 0

    args.prompt.write_text(content, encoding="utf-8")
    n_members = sum(len(m) for _, m in templates)
    logger.info(
        "wrote %s: %d templates, %d members (packages: %s)",
        args.prompt.name,
        len(templates),
        n_members,
        ", ".join(packages),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
