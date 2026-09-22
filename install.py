#!/usr/bin/env python3
"""Install the local Token Smart skill using only the Python standard library."""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

NAME = "token-smart"
RECEIPT = ".token-smart-install.json"
SOURCE = Path(__file__).resolve().parent / "skills" / NAME
START = b"<!-- token-smart:start -->"
END = b"<!-- token-smart:end -->"
BLOCK = (b"\n\n" + START + b"\n"
         b"Use Token Smart's efficiency defaults: read only relevant context, batch independent lookups, "
         b"reuse existing tools, and stop checking once the required checks pass. "
         b"Token Smart has three layers -- live discipline is the default; consult the token-smart skill "
         b"for history cold storage or offline skill/memory consolidation when relevant. "
         b"Preserve task quality, user requirements, and necessary verification; "
         b"do not repeat the installation introduction during ordinary tasks.\n" + END + b"\n")


def defaults(target):
    home = Path.home()
    if target == "claude":
        return home / ".claude" / "skills", home / ".claude" / "CLAUDE.md"
    codex = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    override = codex / "AGENTS.override.md"
    return home / ".agents" / "skills", override if override.is_file() else codex / "AGENTS.md"


def read_receipt(dest):
    path = dest / RECEIPT
    if not path.is_file():
        raise ValueError(f"Existing directory is not managed by this installer: {dest}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for name in data["files"]:
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:
            raise ValueError("Invalid installed file path in receipt")
    return data


def save_receipt(dest, data):
    path = dest / RECEIPT
    temp = dest / (RECEIPT + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def uninstall(dest, instructions):
    if not dest.exists():
        print(f"Not installed: {dest}")
        return
    data = read_receipt(dest)
    kept = []
    rule = data.get("instructions")
    if rule:
        path = Path(rule["path"])
        if instructions is not None and instructions.resolve() != path.resolve():
            raise ValueError(f"Installed rule belongs to {path}; use the same --instructions path")
        if path.exists():
            content = path.read_bytes()
            block = base64.b64decode(rule["block"])
            if content.count(block) == 1:
                remaining = content.replace(block, b"", 1)
                if not remaining and rule["created"]:
                    path.unlink()
                else:
                    path.write_bytes(remaining)
            elif content:
                kept.append(str(path))
    for name, encoded in data["files"].items():
        path = dest / name
        if path.is_file():
            if path.read_bytes() == base64.b64decode(encoded):
                path.unlink()
            else:
                kept.append(str(path))
    (dest / RECEIPT).unlink()
    for path in sorted(dest.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    if not any(dest.iterdir()):
        dest.rmdir()
    else:
        kept.extend(str(p) for p in dest.rglob("*") if p.is_file() and str(p) not in kept)
    print("Uninstalled Token Smart.")
    for path in kept:
        print(f"Preserved user changes: {path}")


def install(dest, instructions, activate, lang):
    if dest == SOURCE.resolve() or SOURCE.resolve() in dest.parents:
        raise ValueError("The installation destination must be outside the source skill")
    if activate and (instructions == dest or dest in instructions.parents):
        raise ValueError("The instructions file must be outside the installed skill")
    onboarding = SOURCE / "references" / ("onboarding.en.md" if lang == "en" else "onboarding.md")
    intro = onboarding.read_text(encoding="utf-8")
    if not (SOURCE / "SKILL.md").is_file():
        raise ValueError(f"Missing SKILL.md: {SOURCE}")
    files = {p.relative_to(SOURCE).as_posix(): base64.b64encode(p.read_bytes()).decode("ascii")
             for p in SOURCE.rglob("*") if p.is_file()}
    fresh = not dest.exists()
    data = {"files": files} if fresh else read_receipt(dest)
    if not fresh:
        if data["files"] != files or any(not (dest / n).is_file() or
                (dest / n).read_bytes() != base64.b64decode(b) for n, b in files.items()):
            raise ValueError("Installed files differ. Existing files were preserved; uninstall before installing this version.")
    content = b""
    add_rule = False
    if activate:
        content = instructions.read_bytes() if instructions.exists() else b""
        old_rule = data.get("instructions")
        if old_rule and Path(old_rule["path"]).resolve() != instructions.resolve():
            raise ValueError("Activation is already installed in another instructions file")
        if START in content or END in content:
            if not old_rule or content.count(BLOCK) != 1:
                raise ValueError("Existing Token Smart block differs; user text was preserved")
        else:
            add_rule = True
    if fresh:
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(SOURCE, dest)
            save_receipt(dest, data)
        except Exception:
            # Only this call's new destination is removed after a failed copy.
            if dest.is_dir():
                shutil.rmtree(dest)
            raise
    if add_rule:
        created = not instructions.exists()
        instructions.parent.mkdir(parents=True, exist_ok=True)
        data["instructions"] = {"path": str(instructions.resolve()), "created": created,
                                "block": base64.b64encode(BLOCK).decode("ascii")}
        save_receipt(dest, data)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=instructions.parent, prefix=".token-smart-", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content + BLOCK)
            temporary.replace(instructions)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    print(f"{'Installed' if fresh else 'Already installed'}: {dest}")
    if fresh:
        print("\n" + intro.strip())
    if activate:
        print(f"Optional standing rules: {instructions}. Start a new session to load them.")
    elif fresh:
        print("On-demand skill only; no standing instructions were changed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=("codex", "claude"))
    parser.add_argument("--skills-dir", type=Path)
    parser.add_argument("--instructions", type=Path)
    parser.add_argument("--activate", action="store_true", help="Append optional short standing rules")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh")
    args = parser.parse_args(argv)
    skills, instructions = defaults(args.target)
    dest = (args.skills_dir or skills).expanduser().resolve() / NAME
    if args.activate and args.uninstall:
        parser.error("--activate and --uninstall cannot be combined")
    if args.instructions and not (args.activate or args.uninstall):
        parser.error("--instructions requires --activate or --uninstall")
    try:
        if args.uninstall:
            uninstall(dest, args.instructions.expanduser() if args.instructions else None)
        else:
            install(dest, (args.instructions or instructions).expanduser().resolve(), args.activate, args.lang)
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
