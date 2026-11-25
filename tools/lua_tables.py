"""Read data tables out of Lua source files without running them.

Only literal values are understood: strings, numbers, booleans, nil and nested tables. Anything else (a variable,
a function call, string concatenation) is kept as {"expr": "<source text>"} so it can be looked at, never run.
Usage: lua_tables.py FILE.lua NAME [NAME ...] > OUT.json   (NAME is a top-level assignment such as killers or p.perks)
"""
import sys, re, json

TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<lcomment>--\[(?P<leq>=*)\[.*?\](?P=leq)\])
  | (?P<comment>--[^\n]*)
  | (?P<lstr>\[(?P<seq>=*)\[.*?\](?P=seq)\])
  | (?P<str>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')
  | (?P<num>0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>\.\.\.|\.\.|==|~=|<=|>=|[{}\[\]=,;().:#+\-*/%^<>])
""", re.S | re.X)

ESC = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "\n": "\n", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}


def unquote(s):
    body = s[1:-1]
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            n = body[i + 1]
            if n.isdigit():
                m = re.match(r"\d{1,3}", body[i + 1:])
                out.append(chr(int(m.group(0))))
                i += 1 + len(m.group(0))
                continue
            out.append(ESC.get(n, n))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def tokens(src):
    pos, out = 0, []
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise ValueError(f"cannot read Lua at {pos}: {src[pos:pos + 40]!r}")
        pos = m.end()
        if m.group("ws") or m.group("lcomment") or m.group("comment"):
            continue
        if m.group("lstr"):
            t = m.group("lstr")
            eq = len(m.group("seq"))
            out.append(("str", t[2 + eq:-(2 + eq)].lstrip("\n"), m.start(), m.end()))
        elif m.group("str"):
            out.append(("str", unquote(m.group("str")), m.start(), m.end()))
        elif m.group("num"):
            t = m.group("num")
            v = int(t, 16) if t[:2].lower() == "0x" else (float(t) if re.search(r"[.eE]", t) else int(t))
            out.append(("num", v, m.start(), m.end()))
        elif m.group("name"):
            out.append(("name", m.group("name"), m.start(), m.end()))
        else:
            out.append(("op", m.group("op"), m.start(), m.end()))
    return out


class Parser:
    def __init__(self, src):
        self.src, self.t, self.i = src, tokens(src), 0

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else ("eof", None, len(self.src), len(self.src))

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect(self, v):
        tok = self.next()
        if tok[1] != v:
            raise ValueError(f"expected {v!r}, got {tok[1]!r} near {self.src[tok[2]:tok[2] + 60]!r}")
        return tok

    def value(self):
        """A value up to the next ',' ';' or '}' at this depth. Literal if possible, else {"expr": text}."""
        start, at = self.peek(), self.i
        if start[0] == "op" and start[1] == "{":
            v = self.table()
            if self.peek()[1] in (",", ";", "}"):
                return v
            return self.skip_expr(start, at)
        if start[0] in ("str", "num") or (start[0] == "name" and start[1] in ("true", "false", "nil")) or (start[1] == "-" and self.peek(1)[0] == "num"):
            neg = False
            if start[1] == "-":
                self.next()
                neg = True
            tok = self.next()
            if self.peek()[1] in (",", ";", "}", "]", "eof"):
                if tok[0] == "name":
                    return {"true": True, "false": False, "nil": None}[tok[1]]
                return -tok[1] if neg else tok[1]
        return self.skip_expr(start, at)

    def skip_expr(self, start, at):
        depth = 0
        self.i = at
        while True:
            tok = self.peek()
            if tok[0] == "eof":
                break
            if tok[0] == "op" and tok[1] in "([{":
                depth += 1
            elif tok[0] == "op" and tok[1] in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif tok[0] == "op" and tok[1] in (",", ";") and depth == 0:
                break
            self.next()
        end = self.t[self.i - 1][3]
        return {"expr": self.src[start[2]:end]}

    def table(self):
        self.expect("{")
        arr, hsh = [], {}
        while self.peek()[1] != "}":
            a, b = self.peek(), self.peek(1)
            if a[0] == "op" and a[1] == "[":
                self.next()
                key = self.value()
                self.expect("]")
                self.expect("=")
                hsh[key if not isinstance(key, dict) else key["expr"]] = self.value()
            elif a[0] == "name" and b[1] == "=" and self.peek(2)[1] != "=":
                self.next()
                self.next()
                hsh[a[1]] = self.value()
            else:
                arr.append(self.value())
            if self.peek()[1] in (",", ";"):
                self.next()
        self.expect("}")
        if hsh and arr:
            for n, v in enumerate(arr, 1):
                hsh.setdefault(n, v)
            return hsh
        return hsh if hsh else arr


def read(src, names):
    out = {}
    p = Parser(src)
    toks = p.t
    for n in names:
        parts = n.split(".")
        found = False
        for i in range(len(toks)):
            if toks[i][0] != "name" or toks[i][1] != parts[0]:
                continue
            j, ok = i, True
            for part in parts[1:]:
                if toks[j + 1][1] == "." and toks[j + 2][1] == part:
                    j += 2
                else:
                    ok = False
                    break
            if not ok or toks[j + 1][1] != "=" or toks[j + 2][1] != "{":
                continue
            if i > 0 and toks[i - 1][1] in (".", ":"):
                continue
            p.i = j + 2
            out[n] = p.table()
            found = True
            break
        if not found:
            raise SystemExit(f"no table {n}")
    return out


if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8").read()
    json.dump(read(src, sys.argv[2:]), sys.stdout, ensure_ascii=False, indent=1, default=str)
