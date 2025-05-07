import copy

def modify_get_value(settings):
    datas = settings.get("datas",{})
    datas["data_a"] = 2  # 呼び出し元に影響あり（ミュータブル操作）

def modify_inner_value(settings):
    settings["datas"]["data_a"] = 3  # 呼び出し元に影響あり

def overwrite_inner_dict(settings):
    settings["datas"] = {"data_a": 4}  # 呼び出し元に影響あり（辞書の再代入）

def overwrite_settings(settings):
    settings = {"datas": {"data_a": 5}}  # 呼び出し元に影響なし（settingsの再代入）

def overwrite_settings_copy1(settings):
    settings_copy = settings.copy()
    settings_copy["datas"]["data_a"] = 6  # 呼び出し元に影響あり（浅いコピーでは、トップレベルのオブジェクトはコピーされますが、内部のミュータブルなオブジェクト（この場合は辞書 datas）は元のオブジェクトを参照したままになります）

def overwrite_settings_copy2(settings):
    settings_copy = settings.copy()
    settings_copy["datas2"] = 7 # 呼び出し元に影響なし（settingsはコピーできているので、settingsの変更は元に影響しない。）

def overwrite_settings_deepcopy(settings):
    settings_copy = copy.deepcopy(settings)
    settings_copy["datas"]["data_a"] = 8  # 呼び出し元に影響なし（deepcopy）

def update_inner_dict(settings):
    settings["datas"].update({"data_a": 9})  # 呼び出し元に影響あり（updateは中身を直接変更）

def overwrite_inner_dict_with_update(settings):
    new_dict = {}
    new_dict.update({"data_a": 10})
    settings["datas"] = new_dict  # 呼び出し元に影響あり（結局再代入）

def overwrite_value(settings):
    settings = 11 # 関数内での再代入

def try_modify_tuple(data_tuple):
    try:
        data_tuple[0] = 100 # イミュータブルなのでエラーになる
    except TypeError as e:
        print(f"タプルの直接変更を試みましたがエラー: {e}")

def change_tuple_indirectly_concat(data_tuple):
    try:
        new_tuple = data_tuple[:1] + (100,) + data_tuple[2:]
        return new_tuple
    except TypeError as e:
        print(f"タプルの変更（連結）でエラー: {e}")
        return data_tuple

def change_tuple_indirectly_list(data_tuple):
    try:
        data_list = list(data_tuple)
        data_list[1] = 200
        new_tuple = tuple(data_list)
        return new_tuple
    except TypeError as e:
        print(f"タプルの変更（リスト変換）でエラー: {e}")
        return data_tuple

def main():
    print("--- ミュータブルなオブジェクト (辞書) の場合 ---")
    settings = {"datas": {"data_a": 1}}
    print("初期値:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    modify_get_value(settings)
    print("getした値を変更:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    modify_inner_value(settings)
    print("内部の値を変更:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    overwrite_inner_dict(settings)
    print("内部の辞書を上書き:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    overwrite_settings(settings)
    print("settingsを上書き:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    overwrite_settings_copy1(settings)
    print("settingsの浅いコピーを変更:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    overwrite_settings_copy2(settings)
    print("settingsの浅いコピーに新しいキーを追加:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    overwrite_settings_deepcopy(settings)
    print("settingsのdeepcopyを変更:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    update_inner_dict(settings)
    print("updateで中身変更:", settings)

    settings = {"datas": {"data_a": 1}} # settingsをリセット
    overwrite_inner_dict_with_update(settings)
    print("updateで作った辞書で上書き:", settings)

    print("\n--- イミュータブルなオブジェクト (数値) の場合 ---")
    num = 1
    print("初期値:", num)
    overwrite_value(num)
    print("数値を上書きしたつもり:", num)

    print("\n--- イミュータブルなオブジェクト (文字列) の場合 ---")
    text = "ABC"
    print("初期値:", text)
    overwrite_value(text) # 関数内では再代入されるが、元の変数は変わらない
    print("文字列を上書きしたつもり:", text)

    print("\n--- イミュータブルなオブジェクト (タプル) の場合 ---")
    data = (1, 2, 3)
    print("初期値:", data)
    try_modify_tuple(data)
    result = change_tuple_indirectly_concat(data)
    print("連結後のタプル:", result)
    print("連結後のタプル(引数への変更なし):", data)
    result = change_tuple_indirectly_list(data)
    print("リスト変換後のタプル:", result)
    print("リスト変換後のタプル(引数への変更なし):", data)

if __name__ == "__main__":
    main()