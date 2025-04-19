#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動テスト設定生成・実行プログラム (更新版)

【機能概要】
① 指定された Python プログラムファイル内の関数定義と引数を解析（AST を使用）。
② 各引数の型（型注釈があればそれを、なければ引数名から推測）に合わせ、
   数値なら [0, 2147483647, -2147483647]、文字列なら ["", "sample", "test"]、リストなら [[], [1,2,3]]、辞書なら [{}, {"key": "value"}] 
   などのテストケースを用意。
   ※各テストケースは、引数名とその値のマッピング（辞書形式）で生成。
③ それらを JSON のリスト形式のテスト設定として生成・保存 (--generate時は --output で指定)。
④ --execute 実行時、テスト結果に応じて expected を更新し、--config で指定されたファイルがあれば上書き保存します。
   ※引数が指定されなかった場合は、カレントフォルダ内の *.py ファイルでテスト生成を行います。
"""

import ast
import json
import os
import sys
import argparse
import importlib.util

# キーワードによる型推測用の辞書
KEYWORD_MAP = {
    "numeric_keywords": {'size', 'count', 'width', 'height', 'ratio', 'length', 'number', 'index'},
    "string_keywords": {'name', 'text', 'message', 'title', 'path', 'filename'},
    "list_keywords": {"list"},
    "dictionary_keywords": {"dict", "dictionary"}
}

def infer_type(arg_name):
    """型注釈が無い場合、引数名から型を推測する"""
    lower_name = arg_name.lower()
    for keyword in KEYWORD_MAP["numeric_keywords"]:
        if keyword in lower_name:
            return "numeric"
    for keyword in KEYWORD_MAP["string_keywords"]:
        if keyword in lower_name:
            return "string"
    for keyword in KEYWORD_MAP["list_keywords"]:
        if keyword in lower_name:
            return "list"
    for keyword in KEYWORD_MAP["dictionary_keywords"]:
        if keyword in lower_name:
            return "dictionary"
    return "string"

def get_test_values(arg_type):
    """型に応じたテスト値リストを返す"""
    if arg_type == "numeric":
        return [0, 2147483647, -2147483647]
    elif arg_type == "string":
        return ["", "sample", "test"]
    elif arg_type == "list":
        return [[], [1, 2, 3]]
    elif arg_type == "dictionary":
        return [{}, {"key": "value"}]
    else:
        return [None]

def parse_functions_from_file(file_path):
    """指定ファイル内の関数定義と各引数の情報を取得する"""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, file_path)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_info = {
                "name": node.name,
                "args": []  # 各要素は {"name": arg_name, "type": arg_type}
            }
            for arg in node.args.args:
                if arg.arg == "self":
                    continue
                if arg.annotation:
                    try:
                        annotation = ast.unparse(arg.annotation)
                    except Exception:
                        annotation = None
                else:
                    annotation = None
                if annotation is not None:
                    if annotation in ["int", "float"]:
                        arg_type = "numeric"
                    elif annotation == "str":
                        arg_type = "string"
                    elif annotation.startswith("List") or annotation == "list":
                        arg_type = "list"
                    elif annotation.startswith("Dict") or annotation == "dict":
                        arg_type = "dictionary"
                    else:
                        arg_type = infer_type(arg.arg)
                else:
                    arg_type = infer_type(arg.arg)
                func_info["args"].append({"name": arg.arg, "type": arg_type})
            functions.append(func_info)
    return functions

def generate_test_config(file_path):
    """
    対象ファイル内の各関数ごとにテスト設定を生成する。
    各テストケースは、引数名と値のマッピング（辞書形式）で生成。
    """
    functions = parse_functions_from_file(file_path)
    test_cases = []
    for func in functions:
        arg_names = [arg["name"] for arg in func["args"]]
        test_values = []
        for arg in func["args"]:
            values = get_test_values(arg["type"])
            test_values.append(values)
        if test_values:
            base_case = {name: values[0] for name, values in zip(arg_names, test_values)}
        else:
            base_case = {}
        test_case = {
            "type": "ExecuteProgram",
            "settings": {
                "program_path": os.path.abspath(file_path),
                "command": func["name"],
                "arguments": base_case,
                "check_result": {
                    "expected": ""
                }
            }
        }
        test_cases.append(test_case)
        for i, values in enumerate(test_values):
            for v in values[1:]:
                args_case = base_case.copy()
                args_case[arg_names[i]] = v
                test_case_variant = {
                    "type": "ExecuteProgram",
                    "settings": {
                        "program_path": os.path.abspath(file_path),
                        "command": func["name"],
                        "arguments": args_case,
                        "check_result": {
                            "expected": ""
                        }
                    }
                }
                test_cases.append(test_case_variant)
    return test_cases

def execute_test_case(test_case):
    """
    テスト設定に従い、対象の関数を動的に呼び出す。
    また、実行前に関数名と引数（名前と値）の設定を表示する。
    """
    settings = test_case["settings"]
    module_path = settings["program_path"]
    function_name = settings["command"]
    arguments = settings["arguments"]

    print("=== Executing Test Case ===")
    print(f"Function: {function_name}({', '.join(f'{k}={v}' for k, v in arguments.items())})")
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func = getattr(module, function_name)
    result = func(**arguments)
    print("Result:", result)
    print("-" * 40)
    return result

def interactive_check(result):
    """実行結果を表示し、ユーザーに OK/NG を問い合わせる"""
    print("テスト実行結果:", result)
    while True:
        choice = input("結果はOKですか？ (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False

def run_tests(test_cases, update_expected=True):
    """
    テスト設定のリストに沿って関数を実行し、check_result による結果チェックを行う
    """
    for test_case in test_cases:
        settings = test_case["settings"]
        print("実行: {}({})".format(settings["command"], 
              ", ".join(f"{k}={v}" for k, v in settings["arguments"].items())))
        try:
            result = execute_test_case(test_case)
        except Exception as e:
            print("実行中にエラー発生:", e)
            continue

        if settings.get("check_result") is not None:
            expected = settings["check_result"].get("expected")
            if expected != "":
                if result == expected:
                    print("結果は期待値と一致しました。")
                else:
                    print("期待値と異なります！")
                    print("期待値:", expected, "実際の結果:", result)
            else:
                if interactive_check(result):
                    if update_expected:
                        settings["check_result"]["expected"] = result
                        print("期待値を更新しました。")
                else:
                    print("テストNG。設定ファイルの expected を確認・修正してください。")
        print("----")

def main():
    parser = argparse.ArgumentParser(description="自動テスト設定生成・実行プログラム (更新版)")
    # file 引数をオプショナルにして、指定がない場合はカレントフォルダ内の *.py ファイルを対象とする
    parser.add_argument("file", nargs="?", help="テスト対象の Python プログラムファイルのパス（未指定の場合はカレントフォルダ内の *.py ファイルが対象）")
    parser.add_argument("--generate", action="store_true", help="テスト設定 JSON を生成して標準出力またはファイルに出力")
    parser.add_argument("--execute", action="store_true", help="テスト設定に基づいて関数を実行")
    parser.add_argument("--config", help="実行に使用する JSON 設定ファイルのパス（指定した場合、実行後に更新）")
    parser.add_argument("--update", action="store_true", help="テスト実行で OK の場合、expected を自動更新")
    parser.add_argument("--output", help="生成したテスト設定を保存する JSON ファイルのパス")
    args = parser.parse_args()

    # 引数が指定されなかった場合、カレントフォルダ内の *.py ファイルを対象とする
    file_list = []
    if args.file:
        file_list.append(os.path.abspath(args.file))
    else:
        for f in os.listdir(os.getcwd()):
            if f.endswith(".py"):
                file_list.append(os.path.abspath(f))
        if not file_list:
            print("カレントフォルダに *.py ファイルが見つかりません。")
            sys.exit(1)

    # 各ファイルごとにテスト設定を生成
    all_test_cases = []
    for file_path in file_list:
        print(f"テスト設定を生成中: {file_path}")
        test_cases = generate_test_config(file_path)
        all_test_cases.extend(test_cases)

    if args.generate:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(all_test_cases, f, indent=4, ensure_ascii=False)
            print("テスト設定が {} に保存されました。".format(args.output))
        else:
            print(json.dumps(all_test_cases, indent=4, ensure_ascii=False))
    elif args.execute:
        if args.config:
            with open(args.config, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = all_test_cases
        run_tests(config, update_expected=args.update)
        if args.config:
            with open(args.config, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print("更新されたテスト設定が {} に保存されました。".format(args.config))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
