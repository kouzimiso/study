#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import pefile
from typing import Dict, Any, List, Optional
import subprocess
import ctypes
from pythonnet import load
load("mono")
import clr
try:
    clr.AddReference("System.Reflection")
except Exception as e:
    print(f"System.Reflection アセンブリの参照に失敗しました: {e}")
from System.Reflection import Assembly

import System
clr.AddReference("System")
from System import Object,String
from System.Collections.Generic import Dictionary as NetDictionary
from System.Collections.Generic import List as NetList

def get_default_csc_path() -> str:
    """
    デフォルトの CSC のパスを返す。
    デフォルトは %SystemRoot%\Microsoft.NET\Framework\v4.0.30319\csc.exe 。
    """
    system_root = os.environ.get("SystemRoot", "C:\\Windows")
    return os.path.join(system_root, "Microsoft.NET", "Framework", "v4.0.30319", "csc.exe")

def compile_source_to_dll(cs_file: str, output_dll: str="test.dll", build_method: str = "csc",
                          csc_path: str = None, references: list = None) -> bool:
    """
    指定された C# ソースファイルを DLL 化する関数。
    build_method が "csc" の場合、CSC の実行ファイル（直接パス指定）を用いてコンパイルする。
    build_method が "msbuild" の場合は、csproj ファイルなどを想定して MSBuild を使用する（簡易実装）。
    追加の参照 DLL は references リストで指定する。
    """
    if build_method == "csc":
        if csc_path is None:
            csc_path = get_default_csc_path()
        compile_command = [csc_path, "/target:library", f"/out:{os.path.abspath(output_dll)}", os.path.abspath(cs_file)]
        if references:
            for ref in references:
                compile_command.append(f'/reference:"{ref}"')
    elif build_method == "msbuild":
        compile_command = ["msbuild", cs_file]
    else:
        raise ValueError(f"Unsupported build method: {build_method}")
    
    print("Compiling C# source with command:", " ".join(compile_command))
    try:
        result = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                shell=False, text=True)
    except FileNotFoundError as e:
        print("Build tool not found:", e)
        return False

    if result.returncode != 0:
        print("Compilation failed:")
        print(result.stdout)
        print(result.stderr)
        return False

    if not os.path.exists(output_dll):
        print(f"Compilation succeeded but {output_dll} not found.")
        return False

    print(f"Compilation succeeded: {output_dll} created.")
    return True

def load_native_dll(dll_path: str) -> object:
    """ネイティブDLLをロードする純粋関数"""
    import ctypes
    abs_dll_path = os.path.abspath(dll_path)
    try:
        return ctypes.WinDLL(abs_dll_path)
    except OSError as e:
        raise OSError(f"Failed to load native DLL {dll_path}: {e}")

def is_native_dll(file_path: str) -> bool:
    """DLLがネイティブかマネージドかを判別する純粋関数"""
    try:
        pe = pefile.PE(file_path)
        return hasattr(pe, 'DIRECTORY_ENTRY_EXPORT')
    except pefile.PEFormatError:
        return False

def load_dll(file_path):
    if is_native_dll(file_path):
        return load_native_dll(file_path)
    else:
        return load_managed_dll(file_path)
def get_dll_function_info(dll_path: str):
    if is_native_dll(dll_path):
            return get_native_function_info(dll_path)
    else:
        try:
            loaded_file = load_dll(dll_path)
        except Exception as e:
            print(f"DLL情報の取得中にエラーが発生しました: {e}")
            return []
        return get_managed_function_info(loaded_file)
    

def load_managed_dll(dll_path: str) -> object:
    """マネージドDLLをロードする純粋関数"""
    try:
        return Assembly.LoadFrom(os.path.abspath(dll_path))
    except Exception as e:
        print(f"マネージド DLL のロードに失敗しました: {e}")
        return None
def create_instance(assembly, class_name, *args):
    """
    DLLから引数ありのコンストラクタを持つクラスのインスタンスを作成します。

    Args:
        dll_path (str): DLLファイルのパス。
        class_name (str): インスタンス化するクラスの完全修飾名。
        *args: コンストラクタに渡す引数。

    Returns:
        object: クラスのインスタンス。
    """
    try:
        type = assembly.GetType(class_name)
        if type:
            if args:
                # 引数ありのコンストラクタを使用
                constructor = type.GetConstructor([arg.__class__ for arg in args])
                if constructor:
                    return constructor.Invoke(args)
                else:
                    raise ValueError("指定された引数に一致するコンストラクタが見つかりません。")
            else:
                constructor = type.GetConstructor([])  # 空の引数リストで引数なしコンストラクタを取得
                if constructor:
                    return constructor.Invoke([])  # 空の引数リストでコンストラクタを呼び出す
                else:
                    raise ValueError("引数なしのコンストラクタが見つかりません。")
        else:
            raise ValueError(f"クラスが見つかりません: {class_name}")
    except Exception as e:
        raise RuntimeError(f"インスタンスの作成に失敗しました: {e}")

def get_managed_function_info(assembly: object) -> List[dict]:
    """
    マネージドDLLからクラス単位の情報を取得する純粋関数です。
    各クラスについて、インスタンス生成に使用するコンストラクタ情報（初期化引数名・型）と
    各メソッド情報（メソッド名、引数名、引数型）をひとつのレコードにまとめて返します。
    """
    function_infos = []
    try:
        for type in assembly.GetTypes():
            if not type.IsPublic:
                continue

            # クラス情報のベースを作成
            class_info = {
                "class_name": type.FullName,
                # コンストラクタ情報：ここでは、パラメータ数が最も多いコンストラクタを選択
                "argument_names": [],
                "argument_types": [],
                # メソッド情報：各メソッドの情報をリストにまとめる
                "methods": []
            }

            # コンストラクタ情報の取得（パブリックなコンストラクタを対象）
            constructors = type.GetConstructors()
            if constructors and len(constructors) > 0:
                # 複数ある場合、パラメータ数が最も多いコンストラクタを選択（必要に応じて変更可）
                chosen_ctor = max(constructors, key=lambda c: len(c.GetParameters()))
                ctor_params = [(param.Name, param.ParameterType.Name) for param in chosen_ctor.GetParameters()]
                class_info["init_argument_names"] = [p[0] for p in ctor_params]
                class_info["init_argument_types"] = [p[1] for p in ctor_params]
            # メソッド情報の取得（特殊メソッドは除外）
            for method in type.GetMethods():
                if method.IsSpecialName:
                    continue
                params = [(param.Name, param.ParameterType.Name) for param in method.GetParameters()]
                method_info = {
                    "method_name": method.Name,
                    "argument_names": [p[0] for p in params],
                    "argument_types": [p[1] for p in params]
                }
                class_info["methods"].append(method_info)
            
            function_infos.append(class_info)
    except Exception as e:
        print(f"関数情報の取得中にエラーが発生しました: {e}")
    return function_infos

def get_native_function_info(dll_path: object) -> list:
    """ネイティブDLLから関数情報を取得する純粋関数"""
    function_infos = []
    pe = pefile.PE(dll_path)
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if exp.name:
                function_name = exp.name.decode('utf-8')
                function_infos.append({
                    "class_name": None,  # ネイティブDLLにはクラスがないため None を追加
                    "function_name": function_name,
                    "argument_names": [],
                    "argument_types": []
                })
    return function_infos

def convert_python_to_cs(value, cs_type: str):
    """
    Python の値を C# 側で利用できる型に変換する関数。
    例として、cs_type が "String[]" または "System.String[]" の場合は、
    Python のリストを System.Array (System.String[]) に変換します。
    """
    try:
        if cs_type in ("int", "Int32"):
            return int(value) if value is not None else 0
        elif cs_type in ("double", "Double"):
            return float(value) if value is not None else 0.0
        elif cs_type in ("string", "String"):
            return str(value) if value is not None else ""
        elif cs_type in ("String[]", "System.String[]"):
            # value が None なら空の文字列配列を作成
            if value is None:
                return System.Array.CreateInstance(System.String, 0)
            # value がリストであれば、各要素を文字列に変換して配列化
            if isinstance(value, list):
                arr = System.Array.CreateInstance(System.String, len(value))
                for i, v in enumerate(value):
                    arr[i] = str(v)
                return arr
            else:
                # 単一値の場合も配列に変換
                arr = System.Array.CreateInstance(System.String, 1)
                arr[0] = str(value)
                return arr
        elif cs_type == "bool":
            return bool(value)
        elif cs_type == "Dictionary`2":                   
            net_dict = NetDictionary[ String, Object]()

            for key, item_value in value.items():
                net_dict[key] = item_value  # .NET Dictionary に値をセット
            return net_dict
        else:
            # その他の型については、そのまま返すか、必要に応じて拡張する
            return value
    except Exception as e:
        print(f"型変換エラー: {value} を {cs_type} に変換できません。エラー: {e}")
        return value
    
def to_dotnet_dict(py_dict):
    """ Python の辞書を .NET の Dictionary<String, Object> に変換 """
    net_dict = NetDictionary[String, Object]()
    
    for key, value in py_dict.items():
        if isinstance(value, dict):  # ネストされた dict は Dictionary<String, Object> に変換
            net_dict[key] = to_dotnet_dict(value)
        elif isinstance(value, list):  # Python のリストは .NET の List<Object> に変換
            net_list = List[Object]()
            for item in value:
                net_list.Add(item)
            net_dict[key] = net_list
        else:
            net_dict[key] = value  # そのまま格納（int, str, float, bool など）
    
    return net_dict

# .NET の型を取得
NET_DICT_TYPE = clr.GetClrType(NetDictionary[String, Object])
NET_LIST_TYPE = clr.GetClrType(NetList[Object])

def convert_cs_to_python(obj):
    """ .NET の Dictionary<String, Object> や List<Object> を Python の dict や list に変換 """
    if obj == None:
        return None
    obj_type = clr.GetClrType(type(obj))  # .NET の型を取得
    
    # obj の型をデバッグ用に出力
    print(f"Result type: {obj_type.FullName}")  # obj の型のフルネームを表示

    if obj_type == NET_DICT_TYPE:  # .NET Dictionary の場合
        py_dict = {}
        for key in obj.Keys:
            py_dict[key] = convert_cs_to_python(obj[key])  # 再帰的に変換
        return py_dict

    elif obj_type == NET_LIST_TYPE:  # .NET List の場合
        return [convert_cs_to_python(item) for item in obj]  # リスト内の要素を再帰的に変換

    elif obj_type.FullName =="System.Boolean":
        return obj
    elif obj_type.FullName =="Python.Runtime.PyInt":
        return obj
    elif obj_type.FullName =="System.String":
        return str(obj)
    elif obj_type.FullName =="System.RuntimeType":
        result = {
            "Error": obj_type.FullName+"can not convert this object type",
            "Result_type": obj_type.FullName  # クラスの完全修飾名
        }
        return result  # クラスの情報を返す
    else:
        result = {
            "Error":obj_type.FullName+"can not convert this object type",
            "Result_type": obj_type.FullName  # クラスの完全修飾名
        }
        return result