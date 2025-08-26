#!/usr/bin/env python3

from __future__ import annotations
import argparse, sys, os
from pathlib import Path

# ------------------- CUSTOM SWAPS (add more here) -------------------
# Key format inside {{...}} as {{$KEY}}.
# Value can be a str or a callable: (current_file: Path) -> str
SWAPS = {
    "CWD": lambda current_file: str(current_file.parent.resolve()),
    # "DATE": lambda _: __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
    # "FILENAME": lambda current_file: current_file.name,
}
# --------------------------------------------------------------------

class CompileError(Exception):
    pass

def _resolve_swap(token: str, current_file: Path) -> str:
    # token shape expected: $KEY (no braces)
    if not token.startswith("$"):
        raise CompileError(f'Unknown swap token "{token}". Expected like "{{$CWD}}".')
    key = token[1:]
    if key not in SWAPS:
        raise CompileError(f'No swap defined for key "{key}". Add it to SWAPS.')
    v = SWAPS[key]
    return v(current_file) if callable(v) else str(v)

def _read_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise CompileError(f'Include not found: "{p}"')
    except Exception as e:
        raise CompileError(f'Failed reading "{p}": {e}')

def _find_balanced_double_brace_spans(s: str):
    # Returns list of (start_idx, end_idx_exclusive, inner_content) for all balanced pairs.
    spans = []
    stack = []
    i, n = 0, len(s)
    while i < n - 1:
        duo = s[i:i+2]
        if duo == "{{":
            stack.append(i)
            i += 2
            continue
        if duo == "}}":
            if not stack:
                raise CompileError("Unbalanced braces: found '}}' without matching '{{'.")
            start = stack.pop()
            end = i + 2
            inner = s[start+2:end-2]
            spans.append((start, end, inner))
            i += 2
            continue
        i += 1
    if stack:
        raise CompileError("Unbalanced braces: missing closing '}}'.")
    # Return innermost-first: spans are naturally innermost-first due to stack pops occurring latest-opened first.
    # For deterministic left-to-right replacement of same depth, sort by start descending so slicing works.
    spans.sort(key=lambda t: t[0], reverse=True)
    return spans

def _process_text(text: str, current_file: Path, stack: list[Path], max_depth: int = 200) -> str:
    if len(stack) > max_depth:
        raise CompileError("Max include depth exceeded. Check for cyclic includes.")
    # Keep expanding until no tokens remain.
    while True:
        try:
            spans = _find_balanced_double_brace_spans(text)
        except CompileError as e:
            # If no braces at all, return text unchanged; else re-raise.
            if "{{" not in text and "}}" not in text:
                return text
            raise
        if not spans:
            return text
        # Replace innermost pairs right-to-left to keep indices valid.
        for start, end, inner in spans:
            token = inner.strip()
            if token.startswith("$"):  # swap
                replacement = _resolve_swap(token, current_file)
            else:  # include path
                # Resolve against current file's folder
                inc_path = (current_file.parent / token).expanduser()
                inc_path = inc_path.resolve()
                if inc_path in stack:
                    cycle = " -> ".join([str(p) for p in stack + [inc_path]])
                    raise CompileError(f"Cyclic include detected:\n{cycle}")
                inc_text = _read_file(inc_path)
                # Recursively process included file in its own context
                replacement = _process_text(inc_text, inc_path, stack + [inc_path], max_depth=max_depth)
            # Splice replacement
            text = text[:start] + replacement + text[end:]
        # Loop to catch new tokens revealed by replacements.

def compile_file(entry: Path, dry_run: bool = False):
    entry = entry.resolve()
    raw = _read_file(entry)
    compiled = _process_text(raw, entry, stack=[entry])
    if dry_run:
        sys.stdout.write(compiled)
    else:
        with open('prompt_full.txt', 'w') as f:
            f.write(compiled)

def main():
    ap = argparse.ArgumentParser(description="Prompt compiler.")
    ap.add_argument("file", type=Path, help="Entry text file to compile in place by default.")
    ap.add_argument("--dry-run", action="store_true", help="Print compiled output to stdout instead of writing.")
    ap.add_argument("--max-depth", type=int, default=200, help="Maximum include nesting depth.")
    args = ap.parse_args()

    # Allow max_depth override
    global _PROCESS_MAX_DEPTH
    try:
        compile_file(args.file, dry_run=args.dry_run)
    except CompileError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()