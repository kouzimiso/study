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

def extract_functions_and_links(filepath):
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        code = f.read()

    # コメント除去（少し強化）
    code = re.sub(r'//.*|/\*[\s\S]*?\*/', '', code)

    # 関数定義抽出：inline/static/戻り値/関数名/引数/本体開始
    func_pattern = re.compile(r'''
        (?P<deco>(?:inline|static|extern)?\s*)      # 修飾子
        (?P<rtype>\w[\w\s\*]*?)\s+                  # 戻り値
        (?P<name>\w+)\s*                            # 関数名
        \(([^;]*?)\)\s*                             # 引数リスト（宣言ではなく定義のみ）
        \{                                          # 本体開始
    ''', re.VERBOSE)

    call_pattern = re.compile(r'(\w+)\s*\(', re.MULTILINE)

    results = {}
    matches = list(func_pattern.finditer(code))

    if not matches:
        print(f"⚠️  関数定義が見つからなかった: {filepath}")
        return {}

    for match in matches:
        func_name = match.group("name")
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
            "links": list(called_funcs)
        }

    return results

def analyze_directory(dir_path):
    all_files = find_c_files(dir_path)
    call_graph = {}
    for f in all_files:
        func_links = extract_functions_and_links(f)
        call_graph.update(func_links)

    return call_graph

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
