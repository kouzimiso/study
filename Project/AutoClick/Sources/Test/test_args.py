import json
import sys


DEFAULT_DATA = {"file_path": "./execute.png", "user": "iwao", "number": 2, "bool": True}


def string_to_bool(string_bool):
    """
    文字列をBool値に変換する関数。
    """
    if string_bool.lower() == "true":
        return True
    elif string_bool.lower() == "false":
        return False
    else:
        raise ValueError("Invalid value for boolean.")


def validate_input(input_value, input_type, default_value):
    """
    入力値を検証する関数。
    """
    if input_value == "":
        return default_value
    try:
        if input_type == bool:
            return string_to_bool(input_value)
        else:
            return input_type(input_value)
    except ValueError:
        print(f"Invalid value for {input_type.__name__}. Please input a valid value.")
        return validate_input(input(), input_type, default_value)

def user_input(key,default_value):
    while True:
        print(f"Please input {key} (Default: {default_value}): ", end="")
        user_input = input()
        value_type = type(default_value)
        input_value = validate_input(user_input, value_type, default_value)
        if isinstance(input_value, value_type):
            break
    return input_value

def get_args(default_data):
    """
    引数を受け取って辞書を返す関数。
    引数がない場合はユーザーからの入力を受け取る。
    """
    try:
        # 引数をJSON形式から辞書形式に変換
        args = json.loads(sys.argv[1])
    except (IndexError, ValueError, TypeError, json.JSONDecodeError):
        # 引数がない場合やJSON形式に変換できない場合はユーザーからの入力を受け取る
        args = {}
        for key, default_value in default_data.items():
            args[key]=user_input(key,default_value)
    # デフォルト値を上書き
    for key, value in default_data.items():
        if key not in args:
            args[key] = value
    return args


args = get_args(DEFAULT_DATA)
print(args)
