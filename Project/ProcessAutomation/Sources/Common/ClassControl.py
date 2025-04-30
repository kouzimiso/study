#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import inspect
import importlib
from typing import Dict, Any, List, Optional
import Process

def update_from_dict(class_instance, defaultvalue_dictionary):
    for key, value in defaultvalue_dictionary.items():
        if hasattr(class_instance, key):
            setattr(class_instance, key, value)
        else:
            raise ValueError(f"{key} is not a valid member of the Judge class")


def list_class_members(file_name, class_name):
    try:
        # ファイルを読み込む
        with open(file_name, 'r') as file:
            code = file.read()

        # コードを実行し、クラスを取得
        namespace = {}
        exec(code, namespace)
        if class_name in namespace:
            class_obj = namespace[class_name]
            obj = class_obj()

            # クラスのメソッドとメンバをリストアップ
            class_members = [member for member in dir(obj) if not callable(getattr(obj, member)) and not member.startswith("__")]
            class_methods = [member for member in dir(obj) if callable(getattr(obj, member))]

            print(f"クラス '{class_name}' のメンバ:")
            for member in class_members:
                print(member)

            print(f"\nクラス '{class_name}' のメソッド:")
            for method in class_methods:
                print(method)
        else:
            print(f"クラス '{class_name}' はファイル内で定義されていません。")
    except FileNotFoundError:
        print(f"指定したファイル '{file_name}' は見つかりません。")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用法: python list_class_members.py <File name> <class name>")
    else:
        file_name = sys.argv[1]
        class_name = sys.argv[2]
        list_class_members(file_name, class_name)
        

# Load the module from a given file path
def load_module(target):
    if os.path.isfile(target):  # ファイルパスの場合
        # Get the module name from the file name (without extension)
        module_name = os.path.splitext(os.path.basename(target))[0]
        
        # Load the module using importlib
        spec = importlib.util.spec_from_file_location(module_name, target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    else:
        try:
            return import_module_from_name(target)
        except ModuleNotFoundError:
            raise ImportError(f"Module '{target}' not found. Please check the name or install it.")

# Dynamically retrieve the class from the loaded module by type name
def get_class_from_module(module,class_name):
    # List all classes from the dynamically loaded popup module
    classes = inspect.getmembers(module, inspect.isclass)
    # Find the class that matches the class_name
    for name, cls in classes:
        if name == class_name:
            return cls
    return None

def get_class_from_module_name(module_name, class_name):
    module = import_module_from_name(module_name)
    return getattr(module, class_name)

def import_module_from_name(module_name: str) :
    """ 指定したモジュールをインポート。無ければインストールして再インポート """
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        raise ImportError(f"Module '{module_name}' import failed.: {str(e)}")

def install_module(install_module_name: str):
    """ 指定したモジュールを pip でインストール """ 
    try:
        Process.execute_external_program(sys.executable,["-m", "pip", "install", install_module_name])
    except  Exception as e:
        raise Exception(f"Failed to install module: {install_module_name}.") from e
        
# モジュールから関数を実行する関数
def load_function(module_name, function_name):
    # モジュールをロード
    module = load_module(module_name)
    return load_function_from_module(module, function_name)

# モジュールから関数を実行する関数
def load_function_from_module(module, function_name):
    # 関数を取得
    func = getattr(module, function_name, None)
    #if func is None:
    #    raise AttributeError(f"Function '{function_name}' not found in module '{module.__name__}'")
    
    # 関数を実行し、結果を返す
    return func

# ---------------------------
# テストプログラム
# ---------------------------
def main():
    print("=== Testing update_from_dict ===")
    # ダミークラス Judge の作成
    class Judge:
        def __init__(self):
            self.name = "default"
            self.score = 0

    judge_instance = Judge()
    update_dict = {"name": "Alice", "score": 95}
    update_from_dict(judge_instance, update_dict)
    print(f"Updated Judge: name={judge_instance.name}, score={judge_instance.score}")
    
    # 無効なキーの場合のテスト
    try:
        update_from_dict(judge_instance, {"invalid_key": 123})
    except ValueError as ve:
        print("Caught expected ValueError:", ve)

    print("\n=== Testing list_class_members ===")
    # 一時ファイルにダミークラス Dummy を定義
    dummy_file = "dummy_class.py"
    dummy_code = '''
class Dummy:
    def __init__(self):
        self.value = 10
    def method_one(self):
        return self.value
    def method_two(self):
        return self.value * 2
'''
    with open(dummy_file, "w", encoding="utf-8") as f:
        f.write(dummy_code)
    list_class_members(dummy_file, "Dummy")
    os.remove(dummy_file)

    print("\n=== Testing load_module (from file path) ===")
    # 一時モジュールファイル作成
    temp_module_file = "temp_module.py"
    temp_module_code = '''
def greet(name):
    return f"Hello, {name}!"
'''
    with open(temp_module_file, "w", encoding="utf-8") as f:
        f.write(temp_module_code)
    temp_module = load_module(temp_module_file)
    print("Greet function output:", temp_module.greet("World"))
    os.remove(temp_module_file)

    print("\n=== Testing get_class_from_module and get_class_from_module_name ===")
    # 一時ファイルにダミークラス Dummy を定義（再利用）
    dummy_file = "dummy_class.py"
    dummy_code = '''
class Dummy:
    def __init__(self):
        self.value = 20
    def get_value(self):
        return self.value
'''
    with open(dummy_file, "w", encoding="utf-8") as f:
        f.write(dummy_code)
    module_from_file = load_module(dummy_file)
    DummyClass = get_class_from_module(module_from_file, "Dummy")
    if DummyClass:
        instance = DummyClass()
        print("Dummy instance value:", instance.get_value())
    os.remove(dummy_file)

    print("\n=== Testing import_module_from_name and load_function ===")
    # 標準モジュール 'math' を使用して sqrt 関数を実行
    result = load_function("math", "sqrt", 16)
    print("sqrt(16) =", result)

    print("\n=== Testing load_function_from_module ===")
    import math
    ceil_func = load_function_from_module(math, "ceil")
    if ceil_func:
        print("ceil(3.2) =", ceil_func(3.2))
if __name__ == "__main__":
    main()