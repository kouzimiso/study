import json
import sys


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
        if input_type == int:
            return int(input_value)
        if input_type == float:
            return float(input_value)
        else:
            return input_type(input_value)
    except ValueError:
        print(f"Invalid value for {input_type.__name__}. Please input a valid value.")
        return validate_input(input(), input_type, default_value)

def user_input(key,display_value,default_value=""):
    while True:
        print(f"Please input {key} (Default: {display_value}): ", end="")
        user_input = input()
        value_type = type(default_value)
        input_value = validate_input(user_input, value_type, default_value)
        if isinstance(input_value, value_type):
            break
    return input_value

#一般化したProgramの引数取得部
def ArgumentGet(default_dictionary, base_dictionary = {}):
    """
    引数を受け取って辞書を返す関数。
    引数がない場合はユーザーからの入力を受け取る。
    """
    try:
        # 引数をJSON形式から辞書形式に変換
        args = json.loads(sys.argv[1])
    except (IndexError, ValueError, TypeError, json.JSONDecodeError):
        # 引数がない場合やJSON形式に変換できない場合はユーザーからの入力を受け取る
        args = base_dictionary
        for key, default_value in default_dictionary.items():
            if  not key in base_dictionary:
                input_value = user_input(key,default_value,default_value)
                args[key]= input_value
    # デフォルト値を上書き
    for key, value in default_dictionary.items():
        if key not in args:
            args[key] = value
    return args

#一般化したProgramの出力部
#Json形式の文字列を標準出力することで他のProgramへ結果を伝える。
def Result(result_dictionary={}):
    result_json = json.dumps(result_dictionary)
    print(result_json)

def Execute(settings_dictionary):
    file_path = settings_dictionary.get("file_path","")
    if(file_path != ""):
        result = True
    else:
        result = False
    result_dictionary={"result" : result}
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Defaultの辞書Dataを設定。
    default_dictionary = {}

    # Command lineの引数を得てから機能を実行。
    # Executeは辞書をIFで動作する。Resultは標準出力をIFで動作する。
    settings_dictionary = ArgumentGet(default_dictionary)
    Execute(settings_dictionary)

    # Defaultの辞書Dataを設定。
    default_dictionary = {"file_path": "./execute.png","action":"test", "user": "iwao", "number": 2, "bool": True}
    option_dictionary = {"option": "option test"}
    # Command lineの引数を得てから機能を実行。
    # Executeは辞書をIFで動作する。Resultは標準出力をIFで動作する。
    settings_dictionary = ArgumentGet(default_dictionary)
    if settings_dictionary.get("action","") =="test":
        settings_dictionary = ArgumentGet(option_dictionary,settings_dictionary)
    result_dictionary = Execute(settings_dictionary)
    Result(result_dictionary)

if __name__ == '__main__':
    main()