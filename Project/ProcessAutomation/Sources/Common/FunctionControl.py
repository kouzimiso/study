import ast
import inspect
import random
import json
import importlib.util
import os
import sys
import JSON_Control
from typing import List, Any
import ListControl
import DLLControl
import clr
import re
import itertools
import copy
import SharedMemory
import SettingUtility
import ClassControl
import DictionaryControl
import traceback

def get_file_type(file_path: str) -> str:
    """ファイルパスからファイルタイプを判別する純粋関数"""
    _, ext = os.path.splitext(file_path)
    return ext.lower()

def load_python_file(file_path: str) -> ast.Module:
    """Pythonファイルをロードする純粋関数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return ast.parse(file.read())
    except FileNotFoundError:
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    except SyntaxError as e:
        raise SyntaxError(f"ファイルの構文エラー: {file_path}, エラー: {e}")
    
def get_function_info(file_path: str, options: dict={}) -> list:
    file_type = get_file_type(file_path)
    """ロードされたファイルから関数情報を取得する純粋関数"""
    function_informations = []
    if file_type == '.cs':
        file_name, ext = os.path.splitext(file_path)
        dll_path = file_name + ".dll"
        references = options.get("references","")
        DLLControl.compile_source_to_dll(file_path, dll_path, references=references)
        # DLL側のメソッド情報を取得
        function_informations = DLLControl.get_dll_function_info(dll_path)
        program_path = dll_path
    elif file_type == '.dll':
        function_informations = DLLControl.get_dll_function_info(file_path)
        program_path = file_path
    elif file_type == '.py':
        loaded_file = load_python_file(file_path)
        # Pythonの関数情報を取得
        function_informations = get_python_function_info(loaded_file)
        program_path = file_path
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    for function_information in function_informations:
        function_information["program_path"] = program_path
    return function_informations

def get_python_function_info(module: ast.Module) -> list:
    """Pythonファイルから関数情報を取得する純粋関数"""
    function_infos = []
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef):
            # クラス内の __init__ はクラスの初期化情報として別途扱うため除外
            if node.name == "__init__":
                continue
            function_name = node.name
            arguments = [arg.arg for arg in node.args.args]
            function_infos.append({
                "function_name": function_name,
                "class_name": "",  # 関数の場合は空文字列
                "argument_names": arguments,
                "argument_types": [None] * len(arguments)  # Pythonでは型ヒントがない場合、Noneとする
            })
    return function_infos

def get_python_class_init_info(module: ast.Module) -> list:
    """
    Pythonファイルからクラス定義を探し、コンストラクタ(__init__)の引数情報を取得する。
    クラスの初期化テストとして、テスト設定に "type" を "InstantiateClass" として追加する。
    """
    constructor_infos = []
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            # クラス内から __init__ を探す
            init_args = []
            init_types = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    # 第一引数 self を除く
                    init_args = [arg.arg for arg in item.args.args[1:]]
                    init_types = [None] * len(init_args)
                    break
            # コンストラクタ情報をテストケースとして追加（存在しなくても、デフォルトコンストラクタのテスト）
            constructor_infos.append({
                "function_name": "__init__",
                "class_name": class_name,
                "argument_names": init_args,
                "argument_types": init_types,
                "is_constructor": True  # フラグでコンストラクタであることを明示
            })
    return constructor_infos

# ====================================================
# 1. 型推論＆テスト値生成（設定ベース・マッチ数対応）
# ====================================================
def infer_possible_types_and_values(arg_name, arg_index, scenario, settings,arg_type = None):
    """
    指定シナリオ（"normal" や "value_error"）の設定から、
    引数名と引数位置を考慮して、マッチするルール候補を全件取得する。

    設定例:
      settings = {
          "normal": {
            "match_count": 2,
            "argument_rules": [ ... ]
          },
          "value_error": {
            "match_count": 2,
            "rules": [ ... ]
          }        
        "combination_mode": "cartesian"
      }
      
    ※ルール内で "arg_index" が設定されている場合、該当位置にのみ適用される。
    """
    scenario_conf = settings.get(scenario, {})
    max_matches = scenario_conf.get("match_count", 1)
    rules = scenario_conf.get("argument_rules", [])
    
    lower_name = arg_name.lower()
    candidates = []
    for rule in rules:
        if arg_type:
            if arg_type != rule.get("type"):
                continue
        # もし "arg_index" 指定があれば、該当でなければスキップ
        if "arg_index" in rule and rule["arg_index"] != arg_index:
            continue
        for pattern in rule.get("match", []):
            if re.search(pattern, lower_name):
                candidates.append((rule["type"], rule["value_list"]))
                break  # １ルール内でマッチしたら次のルールへ
        if len(candidates) >= max_matches:
            break
    if not candidates:
        return [("unknown", [None])]
    return candidates

def generate_argument_candidate_list(arg_name, arg_index, scenario, settings, argument_types=None):
    """
    引数名・位置・シナリオおよび設定に基づいて候補リストを作成する。
    argument_types が与えられている場合はそれを優先して値リスト（デフォルト値）を返す。
    
    結果は候補リスト [(型, 値), …] となり、各ルールの value_list から展開します。
    """
    candidates = []
    candidates = infer_possible_types_and_values(arg_name, arg_index, scenario, settings,argument_types)
    # 展開して (型, 値) の組リストを生成
    candidate_list = []
    for _type, values in candidates:
        for val in values:
            candidate_list.append((_type, val))
    return candidate_list

# ====================================================
# 2. 組み合わせ生成方法
# ====================================================
def generate_combinations(lists, mode="cartesian", random_sample_size=None):
    """
    組み合わせ生成。mode による対応は以下の通り:
      - "cartesian"：各引数のすべての値の直積をそのまま生成
      - "pairwise"：簡易ペアワイズ。最初の2引数間＋残りの直積
      - "random": 全組み合わせから指定数だけランダムサンプル抽出
      - "orthogonal": 直交配列表（簡易実装例：各リストから等間隔に選択）
    """
    if mode == "cartesian":
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
    elif mode == "random":
        all_comb = list(itertools.product(*lists))
        if random_sample_size and random_sample_size < len(all_comb):
            return random.sample(all_comb, random_sample_size)
        else:
            return all_comb
    elif mode == "orthogonal":
        result = []
        if not lists:
            return [[]]
        min_len = min(len(lst) for lst in lists if lst)
        for i in range(min_len):
            result.append(tuple(lst[i] for lst in lists))
        return result
    else:
        return []

# ====================================================
# 3. テストケース作成
# ====================================================

def generate_test_cases(function_informations, settings, 
                        combination_mode=None, random_sample_size=None):
    """
    ・function_informations に "methods" が存在すればクラスとして扱い、  
      コンストラクタ引数と各メソッド引数の候補を生成してテストケースを作成します。  
    ・各引数は、引数名、位置、型情報（あれば）と設定から候補リストを生成し、  
      その組み合わせによりテストケース（辞書）を作成します。
    
    settings からは、テストシナリオ（"scenarios"）や  
    組み合わせモード（"combination_mode"）が利用されます。
    """
    scenarios = settings.keys()
    if not combination_mode:
        combination_mode = settings.get("combination_mode", "cartesian")
        
    test_cases = []
    
    for info in function_informations:
        program_path = info.get("program_path", "")
        if "methods" in info:  # クラスの場合
            class_name = info.get("class_name", "")
            init_arg_names = info.get("init_argument_names", [])
            # 各シナリオごとのコンストラクタ引数候補
            init_candidates_by_scenario = {scenario: [] for scenario in scenarios}
            init_types = []  # 型情報（argument_types 指定または最初の候補）
            for index, arg in enumerate(init_arg_names):
                for scenario in scenarios:
                    argument_types = None
                    if info.get("init_argument_types", [None]*len(init_arg_names))[index]:
                        argument_types = info["init_argument_types"][index]
                    cand = generate_argument_candidate_list(arg, index, scenario, settings, argument_types=argument_types)
                    init_candidates_by_scenario[scenario].append(cand)
                # １シナリオ目の候補から採用
                if info.get("init_argument_types", [None]*len(init_arg_names))[index]:
                    init_types.append(info["init_argument_types"][index])
                else:
                    init_types.append(init_candidates_by_scenario[scenarios[0]][index][0][0])
            
            methods_info = info.get("methods", [])
            method_tests_lists_by_scenario = {scenario: [] for scenario in scenarios}
            
            for method in methods_info:
                method_name = method.get("method_name", "")
                m_arg_names = method.get("argument_names", [])
                m_candidates_by_scenario = {scenario: [] for scenario in scenarios}
                m_types = []
                for index, arg in enumerate(m_arg_names):
                    for scenario in scenarios:
                        argument_types = None
                        if method.get("argument_types", [None]*len(m_arg_names))[index]:
                            argument_types = method["argument_types"][index]
                        cand = generate_argument_candidate_list(arg, index, scenario, settings, argument_types=argument_types)
                        m_candidates_by_scenario[scenario].append(cand)
                    if method.get("argument_types", [None]*len(m_arg_names))[index]:
                        m_types.append(method["argument_types"][index])
                    else:
                        m_types.append(m_candidates_by_scenario[scenarios[0]][index][0][0])
                # 各シナリオごとに組み合わせ生成
                for scenario in scenarios:
                    m_comb = generate_combinations(m_candidates_by_scenario[scenario], mode=combination_mode, random_sample_size=random_sample_size)
                    method_tests = []
                    for comb in m_comb:
                        test_setting = {
                            "name":f"test_{scenario}_{method_name}",
                            "method_name": method_name,
                            "argument_names": m_arg_names,
                            "argument_types": m_types,
                            "arguments": [x[1] for x in comb],
                            "check_result": {},
                            "result": "result_" + method_name
                        }
                        method_tests.append(test_setting)
                    method_tests_lists_by_scenario[scenario].append(method_tests)
            
            # クラス全体のテストケース生成（コンストラクタとメソッドの直積）
            for scenario in scenarios:
                init_comb = generate_combinations(init_candidates_by_scenario[scenario], mode=combination_mode, random_sample_size=random_sample_size)
                if method_tests_lists_by_scenario[scenario]:
                    methods_all = list(itertools.product(*method_tests_lists_by_scenario[scenario]))
                else:
                    methods_all = [[]]
                for i_comb in init_comb:
                    for m_comb in methods_all:
                        test_case = {
                            "type": "ExecuteProgram",
                            "name":f"test_{scenario}_{class_name}_{program_path}",
                            "settings": {
                                "program_path": program_path,
                                "class_name": class_name,
                                "argument_names": init_arg_names,
                                "argument_types": init_types,
                                "arguments": [x[1] for x in i_comb],
                                "methods": list(m_comb),
                                "check_result": {},
                                "result": "result_" + class_name
                            }
                        }
                        test_cases.append(test_case)
        else:
            # グローバル関数の場合
            function_name = info.get("function_name", "")
            argument_names = info.get("argument_names", [])
            arg_candidates_by_scenario = {scenario: [] for scenario in scenarios}
            arg_types = []
            for index, arg in enumerate(argument_names):
                arg_type=""
                for scenario in scenarios:
                    argument_types = None
                    if info.get("argument_types", [None]*len(argument_names))[index]:
                        argument_types = info["argument_types"][index]
                for scenario in scenarios:
                    cand = generate_argument_candidate_list(arg, index, scenario , settings, argument_types=argument_types)
                    arg_candidates_by_scenario[scenario].append(cand)
                    if cand[0][0] != "unknown":
                        arg_type=cand[0][0]
                if info.get("argument_types", [None]*len(argument_names))[index]:
                    arg_types.append(info["argument_types"][index])
                else:
                    arg_types.append(arg_type)
            for scenario in scenarios:
                combinations = generate_combinations(arg_candidates_by_scenario[scenario], mode=combination_mode, random_sample_size=random_sample_size)
                for combination in combinations:
                    test_case = {
                        "type": "ExecuteProgram",
                        "name":f"test_{scenario}_{function_name}_{program_path}",
                        "settings": {
                            "program_path": program_path,
                            "function_name": function_name,
                            "class_name": info.get("class_name", ""),
                            "argument_names": argument_names,
                            "argument_types": arg_types,
                            "arguments": [x[1] for x in combination],
                            "check_result": {},
                            "result": "result_" + function_name
                        }
                    }
                    test_cases.append(test_case)
    return test_cases
# --- グローバル関数用テスト実行 ---
def execute_function(settings):
    program_path = settings.get("program_path", "")
    function_name = settings.get("function_name", "")
    class_name = settings.get("class_name", "")
    argument_values = settings.get("arguments", [])
    argument_names = settings.get("argument_names", [])
    argument_types = settings.get("argument_types", [])
    
    try:
        if program_path.lower().endswith(".dll"):
            # C#のDLLの場合
            assembly = DLLControl.load_dll(os.path.abspath(program_path))
            target_type = assembly.GetType(class_name)
            if target_type:
                method = target_type.GetMethod(function_name)
                if method:
                    argument_values = ListControl.replace_list_values(argument_values,settings) 
                    converted_args = [DLLControl.convert_python_to_cs(val, typ) for val, typ in zip(argument_values, argument_types)]
                    format_str = ",".join(ListControl.format_merge_multiple_list(
                        "{list3} {list1} = {list2}", "",
                        list1=argument_names, list2=converted_args, list3=argument_types))
                    print(f"{class_name}().{function_name}({format_str})")
                    if method.IsStatic:
                        result_value = method.Invoke(None, converted_args)
                    else:
                        # インスタンス生成（デフォルトコンストラクタ）してメソッド実行
                        instance = DLLControl.create_instance(assembly, class_name, *[])
                        result_value = instance.GetType().GetMethod(function_name).Invoke(instance, converted_args)
                    return result_value
                else:
                    raise AttributeError(f"メソッドが見つかりません: {function_name}")
            else:
                raise AttributeError(f"クラスが見つかりません: {class_name}")
        else:
            # Pythonファイルの場合
            spec = importlib.util.spec_from_file_location(function_name, program_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            function = getattr(module, function_name)
            argument_names = get_argument_names(function)
            argument_values = ListControl.replace_list_values(argument_values,settings) 
            format_str = ",".join(ListControl.format_merge_multiple_list(
                "{list1} = {list2}", "",
                list1=argument_names, list2=argument_values))
            print(f"Function: {function_name}({format_str})")
            result_value = function(*argument_values)
        return result_value
    except FileNotFoundError:
        raise Exception(f"ファイルが見つかりません: {os.path.abspath(program_path)}")
    except AttributeError as e:
        raise Exception(f"クラスのインスタンス化またはメソッド呼び出しに失敗しました: {e}")
    except Exception as e:
        raise Exception(f"execute_functionでエラーが発生しました: {e}")


# --- クラステスト用：インスタンス生成＋各メソッド実行 ---
def execute_class(settings):
    program_path = settings.get("program_path", "")
    class_name = settings.get("class_name", "")
    init_argument_names = settings.get("argument_names", [])
    init_argument_types = settings.get("argument_types", [])
    init_argument_values = settings.get("arguments", [])
    methods = settings.get("methods", [])
    
    try:
        if program_path.lower().endswith(".dll"):
            # C#のDLLの場合
            assembly = DLLControl.load_dll(os.path.abspath(program_path))
            target_type = assembly.GetType(class_name)
            if not target_type:
                raise AttributeError(f"クラスが見つかりません: {class_name}")
            converted_init_args = [DLLControl.convert_python_to_cs(val, typ) for val, typ in zip(init_argument_values, init_argument_types)]
            instance = DLLControl.create_instance(assembly, class_name, *converted_init_args)
            class_fmt = ",".join(ListControl.format_merge_multiple_list("{list3} {list1}={list2}", "", list1=init_argument_names, list2=converted_init_args,list3 = init_argument_types))
            
            # 各メソッド実行
            for method_setting in methods:
                method_name = method_setting.get("method_name", "")
                argument_names = method_setting.get("argument_names", [])
                argument_types = method_setting.get("argument_types", [])
                argument_values = method_setting.get("arguments", [])
                argument_values = ListControl.replace_list_values(argument_values,method_setting)
                fmt = ",".join(ListControl.format_merge_multiple_list("{list3} {list1}={list2}", "", list1=argument_names, list2=argument_values,list3 = argument_types))
                converted_m_args = [DLLControl.convert_python_to_cs(val, typ) for val, typ in zip(argument_values, argument_types)]
                print(f"{class_name}({class_fmt}).{method_name}({fmt})")
                method = instance.GetType().GetMethod(method_name)
                if not method:
                    raise AttributeError(f"メソッドが見つかりません: {method_name}")
                cs_result = method.Invoke(instance, converted_m_args)
                result = DLLControl.convert_cs_to_python(cs_result)
                method_setting = CheckResult(method_setting,result)

        else:
            # Pythonクラスの場合
            spec = importlib.util.spec_from_file_location(class_name, program_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            target = getattr(module, class_name)
            if not inspect.isclass(target):
                raise AttributeError(f"{class_name} is not a class")
            instance = target(*init_argument_values)
            print(f"{class_name} インスタンス生成: 引数 {list(zip(init_argument_names, init_argument_values))}")
            
            # 各メソッド実行
            for method_setting in methods:
                method_name = method_setting.get("method_name", "")
                argument_names = method_setting.get("argument_names", [])
                argument_types = method_setting.get("argument_types", [])
                argument_values = method_setting.get("arguments", [])
                argument_values = ListControl.replace_list_values(argument_values,method_setting)
                fmt = ",".join(ListControl.format_merge_multiple_list("{list1}={list2}", "", list1=argument_names, list2=argument_values))
                print(f"{class_name}.{method_name}({fmt})")
                if not hasattr(instance, method_name):
                    raise AttributeError(f"メソッドが見つかりません: {method_name}")
                method = getattr(instance, method_name)
                result = method(*argument_values)
                method_setting = CheckResult(method_setting,result)
        settings["methods"] = methods 
        return  settings         
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {program_path}")
    except AttributeError as e:
        print(f"クラスのインスタンス生成またはメソッド呼び出しに失敗しました: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


def create_instance(settings):
    program_path = settings.get("program_path", "")
    class_name = settings.get("class_name", "")
    init_argument_names = settings.get("argument_names", [])
    init_argument_types = settings.get("argument_types", [])
    init_argument_values = settings.get("arguments", [])
    
    if program_path.lower().endswith(".dll"):
        # C# の DLL の場合
        assembly = DLLControl.load_dll(os.path.abspath(program_path))
        target_type = assembly.GetType(class_name)
        if not target_type:
            raise AttributeError(f"クラスが見つかりません: {class_name}")
        init_argument_values = ListControl.replace_list_values(init_argument_values,settings)
        converted_init_args = [DLLControl.convert_python_to_cs(val, typ) for val, typ in zip(init_argument_values, init_argument_types)]
        instance = DLLControl.create_instance(assembly, class_name, *converted_init_args)
    else:
        # Python クラスの場合
        spec = importlib.util.spec_from_file_location(class_name, program_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        target = getattr(module, class_name)
        if not inspect.isclass(target):
            raise AttributeError(f"{class_name} is not a class")
        init_argument_values = ListControl.replace_list_values(init_argument_values,settings)
        instance = target(*init_argument_values)
    
    return instance

def execute_methods_cs(instance,  method_setting):
    method_name = method_setting.get("method_name", "")
    argument_types = method_setting.get("argument_types", [])
    argument_values = method_setting.get("arguments", [])
    
    converted_m_args = [DLLControl.convert_python_to_cs(val, typ) for val, typ in zip(argument_values, argument_types)]
    method = instance.GetType().GetMethod(method_name)
    if not method:
        raise AttributeError(f"メソッドが見つかりません: {method_name}")
    cs_result = method.Invoke(instance, converted_m_args)
    result = DLLControl.convert_cs_to_python(cs_result)
    return result

def execute_methods_python(instance,  method_setting):
    method_name = method_setting.get("method_name", "")
    argument_values = method_setting.get("arguments", [])
    if not hasattr(instance, method_name):
        raise AttributeError(f"メソッドが見つかりません: {method_name}")
    method = getattr(instance, method_name)
    result = method(*argument_values)
    method_setting = CheckResult(method_setting,result)
    return result




def method_format(method_setting):
    method_name = method_setting.get("method_name", "")
    argument_names = method_setting.get("argument_names", [])
    argument_types = method_setting.get("argument_types", [])
    argument_values = method_setting.get("arguments", [])

    fmt = ",".join(ListControl.format_merge_multiple_list("{list3} {list1}={list2}", "", list1=argument_names, list2=argument_values, list3=argument_types))
    return f"{method_name}({fmt})"

# --- テストケース全体の実行 ---
def ExecuteProgram(settings):
    """テストケースに基づいてプログラムを実行する"""
    class_name = settings.get("class_name", "")
    methods = settings.get("methods", [])
    program_path = settings.get("program_path", "")
    result_dictionary={}
    if methods:
        try:
            if program_path.lower().endswith(".dll"):
                instance = create_instance(settings)
                for i, method_setting in enumerate(methods):
                    fmt = method_format(method_setting)
                    print(f"{program_path}-{i} {class_name}.{fmt}")
                    try:
                        result_value = execute_methods_cs(instance, method_setting)
                    except Exception as e:
                        result_value = {"success": False, "error": str(e)}
                    methods[i] = CheckResult(method_setting, result_value)
                    result_settings = method_setting.get("result")
                    if result_settings:
                        WriteDatas(result_settings,result_dictionary,result_value)
            else:
                instance = create_instance(settings)
                for method_setting in methods:
                    fmt = method_format(method_setting)
                    print(f"{program_path}-{class_name}.{fmt}")
                    try:
                        result_value = execute_methods_python(instance, method_setting)
                    except Exception as e:
                        result_value ={"success":False,"error":str(e)}
                    method_setting = CheckResult(method_setting,result_value)
                    result_settings = method_setting.get("result")
                    if result_settings:
                        WriteDatas(result_settings,result_dictionary,result_value)
            return result_dictionary
        except FileNotFoundError:
            raise Exception(f"ファイルが見つかりません: {settings.get('program_path', '')}")
        except AttributeError as e:
            raise Exception(f"クラスのインスタンス生成またはメソッド呼び出しに失敗しました: {e}")
        except Exception as e:
            raise Exception(f"ExecuteProgramでエラーが発生しました: {e}")
    else:
        return execute_function(settings)
        
        
def write_test_cases(program_path, output_file_path, test_data_name, settings, options={}):
    function_informations = get_function_info(program_path, options)
    if not function_informations:
        return
    test_cases = generate_test_cases(function_informations, settings)
    test_plan_list = {test_data_name: test_cases}
    # JSONファイルに出力
    JSON_Control.WriteDictionary(output_file_path, test_plan_list)
    return test_plan_list

def get_argument_names(func: Any) -> list:
    """
    定義された引数名を取得する関数
    """
    sig = inspect.signature(func)
    arg_names = list(sig.parameters.keys())
    return arg_names

def normalize_program_output(output):
    """
    外部プログラムの戻り値 output を解析し、以下のキーを持つ辞書を返す:
      - "success": 実行の成否（True/False）
      - "result_value": 得られた結果または判断理由
      - "error": エラー情報（あれば）
    """
    if isinstance(output, dict):
        result = output.get("result_value", None)
        error = output.get("error", None)
        success_judge = False if error else True
        if result:
            result_dictionary = {
                "success": output.get("success", success_judge),
                "result_value": result,
            }
            result_dictionary.update(output)
            return result_dictionary
        else:
            if error:
                return {"success": output.get("success", success_judge), "result_value": output, "error": error}
            else:
                return {"success": output.get("success", success_judge), "result_value": output}
    elif isinstance(output, (tuple, list)):
        return {"success": True, "result_value": output}
    elif isinstance(output, bool):
        return {"success": True, "result_value": output, "error": None}
    elif isinstance(output, str):
        return {"success": True, "result_value": output, "error": None}
    else:
        return {"success": True, "result_value": output, "error": None}
def RunPlanLists(settings,data_store={},plan_lists={}):
    data_store = settings.get("data_store",data_store)
    plan_lists = settings.get("plan_lists",plan_lists)
    plan_lists_file_path = settings.get("plan_lists_file_path","")
    if plan_lists_file_path:
        details = {}
        read_plan_lists = JSON_Control.ReadDictionary(plan_lists_file_path,{},details=details)
        if details.get("success",True) == False:
            print(str(details))
            input("file error.please push and skip."+plan_lists_file_path)
        if read_plan_lists:
            plan_lists = read_plan_lists
    run_plan_name_list = settings.get("run_plan_name_list")
    if run_plan_name_list == "":
        details = {"success":False,"error":"run_plan_name_list is nothing."}
        return details
    if not isinstance(run_plan_name_list,list):
        run_plan_name_list = [run_plan_name_list]
    for run_plan_name in run_plan_name_list:        
        plan_list = plan_lists.get(run_plan_name,"")
        if plan_list:
            if not isinstance(plan_list,list):
                plan_list=[plan_list]
            for num,plan in enumerate(plan_list):
                plan_settings = {
                    "run_plan_name":run_plan_name,
                    "run_plan_number": num
                }
                if plan_lists_file_path:
                    plan_settings["plan_lists_file_path"] = plan_lists_file_path
                result = ExecutePlan(plan_settings,data_store,plan_lists)

        
def ExecutePlan(settings,data_store={},plan_lists={}):
    data_store = settings.get("data_store",data_store)
    plan_lists = settings.get("plan_lists",plan_lists)
    # 実行する設定の読込
    run_plan_name = settings.get("run_plan_name","")
    run_plan_number = settings.get("run_plan_number","")

    plan_list = plan_lists.get(run_plan_name)
    if not plan_list:
        return {"success":False,"error":"plan_list is nothing"}
    if not isinstance(plan_list,list):
        plan_list=[plan_list]
    try:
        plan = plan_list[run_plan_number]
    except Exception as e:
        return {"success":False,"error":"plan is nothing."+ str(e)}
    plan_copy = copy.deepcopy(plan)
    
    plan_type= plan_copy.get("type","Action")
    plan_settings = plan_copy.get("settings",{})        
    check_result = plan_settings.get("check_result",None)
    # 実行するPlan内容の表示
    if check_result is not None:
        plan_name =plan_copy.get("name","")
        message= "Plan:"+plan_name+"("+str(settings)+")" 
        print(message)
    # referenceの内容をdata_store,shared_memoryから参照して反映する。      
    apply_reference_values(plan_settings,data_store,shared_memory_file_path="")
    #関数を実行する
    try:
        current_module = inspect.getmodule(inspect.currentframe())
        loaded_function = ClassControl.load_function_from_module(current_module,plan_type)
        plan_settings_backup = copy.deepcopy(plan_settings)
        # シグネチャを解析して引数の個数をチェック
        sig = inspect.signature(loaded_function)
        parameter_names = list(sig.parameters.keys())
        parameter_number = len(parameter_names)
        # 引数の数に応じて関数を呼び出す
        if parameter_number == 3:
            result_value = loaded_function(plan_settings, data_store,plan_lists)
        elif parameter_number == 2:
            result_value = loaded_function(plan_settings, data_store)
        else:
            result_value = loaded_function(plan_settings)
    except Exception as e:
        message = str(e)
        result_value = {"success":False,"error": message}
        print(message)
    check_result = plan_settings.get("check_result",None)
    if check_result is not None:
        check_result_settings ={
            "result_value":result_value,
            "check_result":check_result                    
        }
        CheckResult(check_result_settings)
    # plan実行後のsettingsのFeed Back内容を反映する。
    result_diff = DictionaryControl.DiffDictionaries(plan_settings_backup,plan_settings)
    if result_diff:
        plan["settings"] = DictionaryControl.ChangeDictionary(result_diff,plan.get("settings",{}))
        plan_list_file_path = settings.get("plan_lists_file_path","")
        if plan_list_file_path:
            read_plan_lists = JSON_Control.ReadDictionary(plan_list_file_path,{})
            if read_plan_lists:
                read_plan_list = read_plan_lists.get(run_plan_name,[])
                if read_plan_list:
                    if isinstance(plan_list,list):
                        read_plan_list[run_plan_number] = plan
                    else:
                        read_plan_list = plan                        
                    JSON_Control.WriteDictionary(plan_list_file_path, read_plan_lists)

    result_settings = plan_settings.get("result")
    if result_settings:
        WriteDatas(result_settings,data_store,result_value)

def CheckResult(settings,result_value={}):
    check_result = settings.get("check_result", None)
    if check_result == None:
        return settings 
    if not result_value:
        result_value = settings.get("result_value")
    if check_result=={}:
        check_result["expected"] = result_value
        settings["check_result"] = check_result
        print(f"Write expected: {result_value}")

    elif check_result:
        expected = check_result.get("expected")
        if result_value == expected:
            print(f"OK Result: {result_value}")
        else:
            print(f"NG Result: {result_value}, expected: {expected}")
            user_input = input("OverWrite the expected result setting with the actual results? :(W) ")
            if user_input.upper() == "W":
                check_result["expected"] = result_value
                settings["check_result"] = check_result
    return settings 
def WriteDatas(settings,data_store,datas):
    if isinstance(settings,str):
        key = settings
        data_store[key] = datas
        print("WriteDatas("+key+":"+str(datas)+")")
    if isinstance(settings,dict):
        # 設定に基づいてデータを抽出して保存
        for key,data_key in settings.items():
            if data_key in datas:
                value =datas[data_key]
                data_store[key] = value
                print("WriteDatas("+key+":"+str(value)+")")

def apply_reference_values(settings,data_store,shared_memory_file_path=""):
    reference_list = settings.get("reference", [])
    if not reference_list:
        return settings
    if not isinstance(reference_list,list):
        reference_list =[reference_list]
    for reference in reference_list:
        if isinstance(reference,dict):
            source_type = reference.get("source_type","data_store")
            if source_type =="share_memory":
                shared_memory = SharedMemory.read_from_shared_memory(shared_memory_file_path,{})
                shared_memory_name = settings.get("shared_memory_name","shared_memory_name")
                shared_data=shared_memory.get(shared_memory_name,{})
                for key, reference_key in reference.items():
                    value = shared_data.get(reference_key, "")
                    if value:
                        settings[key] = value
                    else:
                        value = data_store.get(reference_key,"")
                        if value:
                            settings[key] = value
            elif source_type =="data_store":
                for key, reference_key in reference.items():
                    value = data_store.get(reference_key,"")
                    if value:
                        settings[key] = value

def main():
    plan_lists = {
        "test_plan":[
            {
                "type":"ExecuteProgram",
                "settings":{
                    "arguments":["test_program_path", "output_filename", "data_name", "test_pattern", "options"],
                    "program_path" : "./Sources/Common/FunctionControl.py",
                    "test_program_path" : "./Sources/Common/DLLControl.py",
                    "function_name" : "write_test_cases",
                    "output_filename" : "Test_DLLControl.json",
                    "data_name" : "test",
                    "test_pattern":{
                        "normal": {
                            "match_count": 2, 
                            "argument_rules": [
                                {"type": "numeric", "match": ["num", ".+count", ".+size", ".+length"],
                                "value_list": [1, 2, 3, 4, 5, 6]},
                                {"type": "string", "match": ["name", "str"],
                                "value_list": ["name1", "name2", "name3"]},
                                {"type": "string", "match": ["text"],
                                "value_list": ["text1", "text2", "text3"]},
                                {"type": "string", "match": [".*dll_path"],
                                "value_list": ["../../../Tools/diff.dll", "../../../Tools/diff.dll", "../../../Tools/diff.dll"]},
                                {"type": "string", "match": [".*cs_file_path"],
                                "value_list": ["./Sources/Test/test1.cs", "./Sources/Test/test2.cs", "./Sources/Test/test3.cs"]},
                                {"type": "string", "match": [".*text_file_path"],
                                "value_list": ["./Sources/Test/test1.txt", "./Sources/Test/test2.txt", "./Sources/Test/test3.txt"]},
                                # C#向けルール例                
                                {"type": "int", "match": ["id"], "value_list": [10, 20, 30]},
                                {"type": "bool", "match": ["flag", "is_"], "value_list": [True, False]},
                                {"type": "DateTime", "match": ["date", "time"],"value_list": ["2023-10-27T10:00:00", "1970-01-01T00:00:00"]},
                                {"type": "string[]", "match": ["array"], "value_list": [["a"], ["test", "sample"]]},
                                {"type": "Dictionary<string,string>", "match": ["array"], "value_list": [["a"], ["test", "sample"]]},
                                {"type": "Dictionary`2", "match": ["array"], "value_list": [["a"], ["test", "sample"]]}
                            ]
                        },
                        "value_error": {
                            "match_count": 2, 
                            "argument_rules": [
                                {"type": "numeric", "match": ["num", ".+count", ".+size", ".+length"],
                                "value_list": [None, None, None, None, None, None]},
                                {"type": "string", "match": ["name", "str", "text"],
                                "value_list": [1, 2, 3]},
                                # C# 向けエラー例
                                {"type": "int", "match": ["id"], "value_list": [None]},
                                {"type": "bool", "match": ["flag", "is_"], "value_list": [None]},
                                {"type": "string[]", "match": ["array"], "value_list": [["a"], ["test", "sample"]]},
                                {"type": "Dictionary<string,string>", "match": ["array"], "value_list": [["a"], ["test", "sample"]]},
                                {"type": "Dictionary`2", "match": ["array"], "value_list": [["a"], ["test", "sample"]]}
                            ]
                        }
                    },
                    "scenarios":["normal", "value_error"],
                    "combination_mode":"cartesian",
                    "options" : {"references": [".\\Reference\\Newtonsoft.Json.13.0.3\\lib\\net35\\Newtonsoft.Json.dll"]}
                }
            },
            {
                "type":"RunPlanLists",
                "settings" :{
                    "plan_lists_file_path":"Test_DLLControl.json",
                    "run_plan_name_list":"test",
                    "data_store" : {"key1":"value1","key2":"value2"}
                }
            }
        ]
    }

    
    # Pythonのテスト
    settings = {
        "plan_lists": plan_lists,
        "run_plan_name_list": "test_plan",
    }
        
    RunPlanLists(settings)

    # DLL のテスト
    plan_lists["test_plan"][0]["settings"]["test_program_path"]= "../../../Tools/diff.dll"
    plan_lists["test_plan"][0]["settings"]["output_filename"]= "Test_dll.json"
    plan_lists["test_plan"][0]["settings"]["data_name"]= "test_dll"
    plan_lists["test_plan"][1]["settings"]["plan_lists_file_path"]= "Test_dll.json"
    plan_lists["test_plan"][1]["settings"]["run_plan_name_list"]= "test_dll"

    RunPlanLists(settings)

      
if __name__ == "__main__":
    main()
