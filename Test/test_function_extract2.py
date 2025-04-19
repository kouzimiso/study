import re
import itertools
import json

# -----------------------------
# コンフィグからテスト値生成／型推論を行う関数群
# -----------------------------

def infer_type_and_values(arg_name, arg_index, scenario, config):
    """
    引数名とインデックス、テストシナリオから、
    設定に基づいて型情報とテスト値（value_list）を推論する。
    
    config例:
    {
       "normal": [
         {"type": "numeric", "match": ["num", ".+count", ".+size", ".+length"], "value_list": [1,2,3,4,5,6]},
         {"type": "string", "match": ["name", "str"], "value_list": ["name1","name2","name3"]},
         {"type": "string", "match": ["text"], "value_list": ["text1","text2","text3"], "arg_index": 1}  # ※1番目以降（0オリジンなのでarg_index==1は第2引数）
       ],
       "value_error": [
         {"type": "numeric", "match": ["num", ".+count", ".+size", ".+length"], "value_list": [None, None, None, None, None, None]},
         {"type": "string", "match": ["name", "str", "text"], "value_list": [1,2,3]}
       ]
    }
    
    ※ruleに"arg_index"が指定されている場合は該当する引数位置のみ反映する。
    """
    scenario_rules = config.get(scenario, [])
    lower_name = arg_name.lower()
    # 優先順位順にルールをチェック
    for rule in scenario_rules:
        # もし"arg_index"が設定されている場合、対象でなければスキップ
        if "arg_index" in rule and rule["arg_index"] != arg_index:
            continue
        for pattern in rule.get("match", []):
            if re.search(pattern, lower_name):
                # マッチしたルールの型と値リストを返す
                return rule["type"], rule["value_list"]
    # 何にもマッチしなかった場合のデフォルト（unknownの場合はNoneのみ）
    return "unknown", [None]

def generate_argument_values_from_config(arg_name, arg_index, scenario, config):
    """
    引数名と位置、シナリオ、コンフィグに基づき、該当するテスト値リストを返す
    """
    _type, value_list = infer_type_and_values(arg_name, arg_index, scenario, config)
    return _type, value_list

# -----------------------------
# 組み合わせ生成（直積 / ペアワイズ）
# -----------------------------
def generate_combinations(lists, mode="cartesian"):
    """
    組み合わせ生成  
    mode: 
      - "cartesian": 各引数の全ての値の直積を生成
      - "pairwise": シンプルなペアワイズ組み合わせの例（先頭2引数の直積＋残りの直積）
    """
    if mode == "cartesian":
        if not lists:
            return [[]]
        return list(itertools.product(*lists))
    elif mode == "pairwise":
        if not lists:
            return [[]]
        elif len(lists) == 1:
            return [[item] for item in lists[0]]
        else:
            first_pair = list(itertools.product(lists[0], lists[1]))
            remaining = lists[2:]
            if remaining:
                rest_combs = list(itertools.product(*remaining))
                return [fp + rest for fp in first_pair for rest in rest_combs]
            else:
                return first_pair
    else:
        return []

# -----------------------------
# テストケース作成
# -----------------------------
def create_test_case(test_info, scenario):
    """
    テストケース辞書にテスト名を付与して返す
    """
    test_info["test_name"] = f"test_{test_info.get('result', 'unknown')}_{scenario}"
    return test_info

def generate_test_cases(function_informations, type_config,
                        test_scenarios=["normal", "value_error"],
                        combination_mode="cartesian"):
    """
    各関数／クラスのテストケースを、設定に従って生成する。
    ・関数情報に "methods" キーがあればクラスとして扱い、
      コンストラクタと各メソッドのテスト設定をひとまとめにする。
    ・引数情報は、各引数毎に名前・位置でコンフィグから型とテスト値を取得する。
    """
    test_cases = []
    for info in function_informations:
        program_path = info.get("program_path", "")
        if "methods" in info:  # クラスの場合
            class_name = info.get("class_name", "")
            init_arg_names = info.get("init_argument_names", [])
            # コンストラクタ引数の設定：位置ごとに設定
            init_types = []
            init_values_sets_by_scenario = { scenario: [] for scenario in test_scenarios }
            for index, arg in enumerate(init_arg_names):
                for scenario in test_scenarios:
                    _type, values = generate_argument_values_from_config(arg, index, scenario, type_config)
                    # もし既に型情報が設定済みならそちらを優先する
                    if info.get("init_argument_types", [])[index]:
                        _type = info["init_argument_types"][index]
                    init_types.append(_type) if scenario==test_scenarios[0] else None
                    init_values_sets_by_scenario[scenario].append(values)
            
            methods_info = info.get("methods", [])
            # 各メソッドごとにテスト設定を生成
            method_tests_lists_by_scenario = { scenario: [] for scenario in test_scenarios }
            for method in methods_info:
                method_name = method.get("method_name", "")
                m_arg_names = method.get("argument_names", [])
                m_types = []
                m_values_sets_by_scenario = { scenario: [] for scenario in test_scenarios }
                for index, arg in enumerate(m_arg_names):
                    for scenario in test_scenarios:
                        _type, values = generate_argument_values_from_config(arg, index, scenario, type_config)
                        # もし明示的な型情報があればそちらを優先
                        if method.get("argument_types", [])[index]:
                            _type = method["argument_types"][index]
                        m_types.append(_type) if scenario==test_scenarios[0] else None
                        m_values_sets_by_scenario[scenario].append(values)
                # 各テストシナリオ毎に組み合わせを生成
                for scenario in test_scenarios:
                    m_combinations = generate_combinations(m_values_sets_by_scenario[scenario], mode=combination_mode)
                    method_tests = []
                    for comb in m_combinations:
                        test_setting = {
                            "method_name": method_name,
                            "argument_names": m_arg_names,
                            "argument_types": m_types,
                            "arguments": list(comb),
                            "check_result": {},
                            "result": "result_" + method_name
                        }
                        method_tests.append(create_test_case(test_setting, scenario))
                    method_tests_lists_by_scenario[scenario].append(method_tests)
            
            # クラスのテストケース生成：コンストラクタとメソッドの直積を生成
            for scenario in test_scenarios:
                init_combinations = generate_combinations(init_values_sets_by_scenario[scenario], mode=combination_mode)
                # メソッド毎のテストケース直積
                if method_tests_lists_by_scenario[scenario]:
                    methods_all = list(itertools.product(*method_tests_lists_by_scenario[scenario]))
                else:
                    methods_all = [[]]
                for init_comb in init_combinations:
                    for methods_comb in methods_all:
                        tc = {
                            "type": "ExecuteProgram",
                            "settings": {
                                "program_path": program_path,
                                "class_name": class_name,
                                "argument_names": init_arg_names,
                                "argument_types": init_types,
                                "arguments": list(init_comb),
                                "methods": list(methods_comb),
                                "check_result": {},
                                "result": "result_" + class_name
                            }
                        }
                        test_cases.append(create_test_case(tc, scenario))
        else:
            # グローバル関数の場合
            function_name = info.get("function_name", "")
            argument_names = info.get("argument_names", [])
            arg_types = []
            arg_values_sets_by_scenario = { scenario: [] for scenario in test_scenarios }
            for index, arg in enumerate(argument_names):
                for scenario in test_scenarios:
                    _type, values = generate_argument_values_from_config(arg, index, scenario, type_config)
                    # 明示的に型が設定されている場合はそちらを優先
                    if info.get("argument_types", [])[index]:
                        _type = info["argument_types"][index]
                    arg_types.append(_type) if scenario==test_scenarios[0] else None
                    arg_values_sets_by_scenario[scenario].append(values)
            for scenario in test_scenarios:
                combinations = generate_combinations(arg_values_sets_by_scenario[scenario], mode=combination_mode)
                for arg_values in combinations:
                    tc = {
                        "type": "ExecuteProgram",
                        "settings": {
                            "program_path": program_path,
                            "function_name": function_name,
                            "class_name": info.get("class_name", ""),
                            "argument_names": argument_names,
                            "argument_types": arg_types,
                            "arguments": list(arg_values),
                            "check_result": {},
                            "result": "result_" + function_name
                        }
                    }
                    test_cases.append(create_test_case(tc, scenario))
    return test_cases

# -----------------------------
# 組み合わせ方法のまとめ出力
# -----------------------------
def print_combination_methods():
    print("利用可能なテストケースの引数組み合わせ方法:")
    print("1. 全組み合わせ（Cartesian product）: 各引数のすべての値の直積")
    print("2. ペアワイズテスト: 複数引数の中で2引数ずつの組み合わせ＋残りの直積")
    print("※他にもランダムテストなどが考えられます。")

# -----------------------------
# サンプル実行
# -----------------------------
if __name__ == "__main__":
    # テストシナリオ毎の設定（型推論ルールおよびテスト値リスト）
    type_inference_rules = {
        "normal": [
            {"type": "numeric", "match": ["num", ".+count", ".+size", ".+length"], "value_list": [1,2,3,4,5,6]},
            {"type": "string", "match": ["name", "str"], "value_list": ["name1","name2","name3"]},
            # ここで、引数のインデックス（0オリジンで 1 → 第2引数）が指定されている
            {"type": "string", "match": ["text"], "value_list": ["text1","text2","text3"], "arg_index": 1}
        ],
        "value_error": [
            {"type": "numeric", "match": ["num", ".+count", ".+size", ".+length"], "value_list": [None, None, None, None, None, None]},
            {"type": "string", "match": ["name", "str", "text"], "value_list": [1,2,3]}
        ]
        # ※必要に応じて"another_error"等の設定も追加可能
    }
    
    # サンプルの関数／クラス情報
    function_informations = [
        {
            "program_path": "./sample_program.py",
            "function_name": "sample_function",
            "class_name": "",  # グローバル関数の場合
            "argument_names": ["count", "text"],
            "argument_types": [None, None]  # どちらも型情報はなく、設定により推論される
        },
        {
            "program_path": "./sample_class.py",
            "class_name": "SampleClass",
            "init_argument_names": ["size", "desc"],
            "init_argument_types": [None, "string"],
            "methods": [
                {
                    "method_name": "compute",
                    "argument_names": ["value", "data"],
                    "argument_types": [None, "list"]
                }
            ]
        }
    ]
    
    print("=== 組み合わせ方法一覧 ===")
    print_combination_methods()
    
    print("\n=== 生成したテストケース一覧 ===")
    test_cases = generate_test_cases(function_informations, type_inference_rules,
                                     test_scenarios=["normal", "value_error"],
                                     combination_mode="cartesian")
    print(json.dumps(test_cases, indent=2, ensure_ascii=False))
