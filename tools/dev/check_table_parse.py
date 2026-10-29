"""按引擎 TextTable::parseTabSeparated 的规则解析表，抽查某几行。

用法：python check_table_parse.py <表路径> <id列=0> <id...>
"""
import sys


def has_closing_quote_before_tab(s, begin):
    i = begin
    while i < len(s):
        c = s[i]
        if c == "\t":
            return False
        if c == '"':
            if i + 1 < len(s) and s[i + 1] == '"':
                i += 2
                continue
            return True
        i += 1
    return False


def parse(s):
    rows = []
    row = []
    cell = ""
    in_quotes = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == '"':
            if in_quotes and i + 1 < len(s) and s[i + 1] == '"':
                cell += '"'
                i += 1
            elif in_quotes:
                in_quotes = False
            elif not cell and has_closing_quote_before_tab(s, i + 1):
                in_quotes = True
            else:
                cell += c
            i += 1
            continue
        if c == "\r":
            i += 1
            continue
        if c == "\t" and not in_quotes:
            row.append(cell)
            cell = ""
            i += 1
            continue
        if c == "\n" and not in_quotes:
            row.append(cell)
            rows.append(row)
            row = []
            cell = ""
            i += 1
            continue
        cell += c
        i += 1
    if in_quotes:
        return None
    if cell or row:
        row.append(cell)
        rows.append(row)
    return rows


def main():
    path = sys.argv[1]
    wanted = set(sys.argv[2:])
    raw = open(path, "rb").read().decode("utf-8")
    rows = parse(raw)
    if rows is None:
        print("解析失败：引号未闭合")
        return
    print(f"逻辑行数 {len(rows)}")
    for row in rows:
        key = row[0].strip() if row else ""
        if key in wanted:
            text = row[1] if len(row) > 1 else ""
            print(f"--- id {key} 字段数 {len(row)}")
            print(text[:200].replace("\n", "\\n"))


if __name__ == "__main__":
    main()
