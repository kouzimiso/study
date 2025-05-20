import os
import re
import json

def find_c_files(root_dir):
    c_files = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith('.c') or f.endswith('.h'):
                c_files.append(os.path.join(root, f))
    return c_files

def parse_arguments(arg_str):
    arg_str = arg_str.strip()
    if arg_str == "" or arg_str == "void":
        return [], []
    args = []
    depth = 0
    current = ""
    for c in arg_str:
        if c == ',' and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += c
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
    if current:
        args.append(current.strip())

    arg_types = []
    arg_names = []

    for a in args:
        parts = a.rsplit(' ', 1)
        if len(parts) == 1:
            arg_types.append(parts[0])
            arg_names.append("")
        else:
            arg_types.append(parts[0])
            arg_names.append(parts[1])

    return arg_names, arg_types

def extract_functions_and_links(filepath):
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        code = f.read()

    code = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code)

    func_pattern = re.compile(r'''
        (?P<deco>(?:inline|static|extern)?\s*)
        (?P<rtype>\w[\w\s\*]*?)\s+
        (?P<name>\w+)\s*
        \((?P<args>[^;]*?)\)\s*
        \{
    ''', re.VERBOSE)

    call_pattern = re.compile(r'(\w+)\s*\(', re.MULTILINE)

    results = {}
    matches = list(func_pattern.finditer(code))

    if not matches:
        print(f"⚠️  関数定義が見つからなかった: {filepath}")
        return {}

    for match in matches:
        func_name = match.group("name")
        arg_str = match.group("args")
        arg_names, arg_types = parse_arguments(arg_str)

        start = match.end()
        brace_count = 1
        i = start
        while i < len(code) and brace_count > 0:
            if code[i] == '{':
                brace_count += 1
            elif code[i] == '}':
                brace_count -= 1
            i += 1
        body = code[start:i]

        called_funcs = set()
        for call in call_pattern.finditer(body):
            called_func = call.group(1)
            if called_func not in ["if", "for", "while", "switch", "return"]:
                called_funcs.add(called_func)

        results[func_name] = {
            "program_path": filepath,
            "links": list(called_funcs),
            "argument_names": arg_names,
            "argument_types": arg_types
        }

    return results

def analyze_directory(dir_path):
    all_files = find_c_files(dir_path)
    funcs = {}
    for f in all_files:
        funcs.update(extract_functions_and_links(f))

    # ここから指定JSON構造へ変換
    elements = {}
    groups = {}

    for func_name, info in funcs.items():
        # elementsに関数情報
        elements[func_name] = {
            "label": func_name,
            "type": "function",
            "description": "",
            "links": [{"name": l, "color": "blue"} for l in info["links"]],
            "argument_names": info.get("argument_names", []),
            "argument_types": info.get("argument_types", [])
        }

        # groupsは program_pathごとにグループ化
        path = info["program_path"]
        if path not in groups:
            groups[path] = {
                "label": path,
                "elements": []
            }
        groups[path]["elements"].append(func_name)

    # groupsの辞書はキーがpathなので、そのままだと仕様と少し違う場合は調整可能
    # 例：キーをpathから任意のIDにする等

    return {
        "elements": elements,
        "groups": groups
    }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="C 関数の呼び出し関係を解析するツール")
    parser.add_argument("directory", help="解析対象のディレクトリ")
    parser.add_argument("-o", "--output", help="出力ファイル名", default="call_graph.json")

    args = parser.parse_args()

    result = analyze_directory(args.directory)

    with open(args.output, "w", encoding="utf-8") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)

    print(f"関数の呼び出し関係を {args.output} に出力しました。")
