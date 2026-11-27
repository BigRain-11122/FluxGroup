"""C2140 crash-adoption: collapse stash-pop conflict markers in dispatcher logs.

Law: empty conflict blocks (both sides carry no content) are noise left by a
killed `pull --rebase` autostash pop; blocks with real content are merged as a
union (ours then theirs, drop base section).
"""
import io
import sys

TARGETS = [
    (r"cph4/fleet/dispatcher/CEO-PROXY/LOG.md", "ours"),
    (r"cph4/fleet/dispatcher/PATROL-FLEET/LOG.md", "theirs"),
]

MARK_OPEN = "<<<<<<<"
MARK_SEP = "======="
MARK_BASE = "|||||||"
MARK_CLOSE = ">>>>>>>"


def is_marker(line, tag):
    return line.startswith(tag) and (len(line) == len(tag) or line[len(tag)] == " ")


def resolve(lines):
    out = []
    i = 0
    collapsed = 0
    merged = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if is_marker(line, MARK_OPEN):
            ours, theirs, base = [], [], []
            i += 1
            cur = ours
            closed = False
            while i < n:
                l = lines[i]
                if is_marker(l, MARK_BASE):
                    cur = base
                    i += 1
                    continue
                if is_marker(l, MARK_SEP):
                    cur = theirs
                    i += 1
                    continue
                if is_marker(l, MARK_CLOSE):
                    closed = True
                    i += 1
                    break
                if is_marker(l, MARK_OPEN):
                    # nested opener: treat as noise marker, re-enter block
                    i += 1
                    continue
                cur.append(l)
                i += 1
            if not closed:
                sys.stderr.write("UNCLOSED block, keeping ours\n")
                out.extend(ours)
                continue
            if not ours and not theirs:
                collapsed += 1
                continue
            if ours == theirs:
                collapsed += 1
                out.extend(ours)
                continue
            merged += 1
            out.extend(ours)
            out.extend(theirs)
            continue
        if is_marker(line, MARK_SEP) or is_marker(line, MARK_CLOSE):
            # stray marker (no matching opener): drop it as noise
            collapsed += 1
            i += 1
            continue
        out.append(line)
        i += 1
    return out, collapsed, merged


def main():
    side = sys.argv[1] if len(sys.argv) > 1 else None
    for path, strategy in TARGETS:
        if side and side not in path:
            continue
        raw = io.open(path, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        eol = "\r\n" if "\r\n" in text else "\n"
        lines = text.split(eol)
        trailing = lines[-1] == ""
        if trailing:
            lines = lines[:-1]
        resolved, collapsed, merged = resolve(lines)
        body = eol.join(resolved) + (eol if trailing else "")
        data = body.encode("utf-8")
        if bom:
            data = b"\xef\xbb\xbf" + data
        io.open(path, "wb").write(data)
        left = sum(
            1
            for l in resolved
            if is_marker(l, MARK_OPEN) or is_marker(l, MARK_CLOSE)
        )
        print(
            "%s strategy=%s lines=%d markers_left=%d collapsed_blocks=%d merged_blocks=%d bom=%s eol=%s"
            % (path, strategy, len(resolved), left, collapsed, merged, bom, repr(eol))
        )


main()