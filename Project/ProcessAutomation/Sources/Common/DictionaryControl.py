# -*- coding: utf-8 -*-
import copy
import FunctionUtility

def get_value_from_dict(data, keys, default=""):
    """辞書から指定したキーの値を取得。キーが存在しない場合はデフォルト値を返す。"""
    if isinstance(data, dict):
        if isinstance(keys, list):
            for key in keys:
                if key in data:
                    return data.get(key, default)
        elif isinstance(keys, str):
            return data.get(keys, default)
    return data

def WriteDictionaryBySettings(settings, write_dictionary, return_data):
    """
    設定に基づいてデータを処理し、新しいデータ構造を返す純粋関数。

    Args:
        settings (dict): 書き込み設定の辞書 (key: 保存先, value: データキー)。
        write_dictionary (dict): 入力データの辞書 (key: データキー, value: データ値)。
        return_data: write_dictionaryを追加してreturnするdata

    Returns:
        dict: 更新されたデータ構造。
    """
    if isinstance(settings,str):
        key = settings
        return_data[key] = write_dictionary
    elif isinstance(settings,dict):
        for key,data_key in settings.items():
            if data_key in write_dictionary:
                return_data[key] = write_dictionary[data_key]
    return return_data
def RestructureData(source_data, copy_data, restructure_settings):
    #先頭はDictionary,List,Stringで場合分けする
    if isinstance(copy_data, dict):
        for read_key, value in copy_data.items():
            #DictionaryのvalueはDictionary,List,Stringで場合分けする
            if isinstance(value, dict):
                #DictionaryのkeyはStringのみ
                copy_data[read_key] = RestructureData(source_data , value, restructure_settings)
            elif isinstance(value, list):
                copy_data[read_key]= [RestructureData(source_data,item, restructure_settings) for item in value]
            else:
                read_data = ReadDictionaryBySetting(source_data,read_key,restructure_settings)
                if read_data is not None:
                    copy_data[read_key] = read_data
    elif isinstance(copy_data, list):
        for read_key in copy_data:
            if isinstance(read_key, list):
                copy_data[read_key] = [RestructureData(item,read_key, restructure_settings) for item in value]
            elif read_key in restructure_settings:
                read_data = ReadDictionaryBySetting(source_data,read_key,restructure_settings)
                if read_data is not None:
                    copy_data[read_key] = read_data
    else:
        read_key = copy_data
        read_data = ReadDictionaryBySetting(source_data,read_key,restructure_settings)
        if read_data is not None:
            copy_data = read_data
    return copy_data

def ReadDictionaryBySetting(source_data,read_key,restructure_settings):
    key_path = GetKeyPathFromSetting(read_key, restructure_settings)
    if key_path is not None:
        value = ReadValueFromDictionary(source_data, key_path)
        return value
    return None
def GetKeyPathFromSetting(read_key, read_setting):
    if read_key in read_setting:
        return read_setting[read_key]
    else:
        return None
    
def ReadValueFromDictionary(data, key_path,separator="."):
    path_components = key_path.split(separator)
    for path_component in path_components:
        if path_component in data:
            data = data[path_component]
        else:
            return None
    return data

def MergeDictionayWithDepth(source, new, depth):
    """
    辞書を指定された層数までマージ。

    :param source: 元の辞書
    :param new: 更新する辞書
    :param depth: 辞書の層数
    :return: マージ後の辞書
    """
    if depth <= 0 or not isinstance(source, dict) or not isinstance(new, dict):
        # 深さ0または非辞書型のデータは新しいデータで上書き
        return new

    result = source.copy()
    for key, value in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 再帰的に深さを減らしながらマージ
            result[key] = MergeDictionayWithDepth(result[key], value, depth - 1)
        else:
            # 既存のキーが辞書でない場合は新しい値を設定
            result[key] = value

    return result
def MergeDictionayKeyAndValue(base_data,merge_data,merge_key,new_merge_key):
    """
    ベースデータにマージデータを結合する。
    :param base_data: 結合先のデータ
    :param merge_data: 結合元のデータ
    :param merge_key: 結合元のキー
    :param new_merge_key: 結合後に使用するキー (空白の場合はmerge_keyを使用)
    :return: 結合後のデータ
    """
    new_merge_key = new_merge_key.strip() or merge_key
    key_data = merge_data.get(merge_key,"")
    result_data = base_data.copy()
    result_data[new_merge_key] = key_data
    return result_data

from typing import Any, Dict, Optional

def GetDiff(source_data: Dict[str, Any], compared_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """元データと変更後データの差分を計算する"""
    return {
        "added": GetDiffAdded(source_data, compared_data),
        "changed": GetDiffChanged(source_data, compared_data),
        "deleted": GetDiffDeleted(source_data, compared_data)
    }


def GetDiffAdded(source_data: Dict[str, Any], compared_data: Dict[str, Any]) -> Dict[str, Any]:
    """追加されたデータを取得"""
    return {k: v for k, v in compared_data.items() if k not in source_data}


def GetDiffChanged(source_data: Dict[str, Any], compared_data: Dict[str, Any]) -> Dict[str, Any]:
    """変更されたデータを取得"""
    return {
        k: {"from": source_data[k], "to": compared_data[k]}
        if not (isinstance(source_data[k], dict) and isinstance(compared_data[k], dict))
        else GetDiffChanged(source_data[k], compared_data[k])
        for k in source_data.keys() & compared_data.keys()
        if source_data[k] != compared_data[k]
    }


def GetDiffDeleted(source_data: Dict[str, Any], compared_data: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    """削除されたデータを取得（削除されたキーを None で表現）"""
    return {k: None for k in source_data.keys() - compared_data.keys()}

def ReplaceCircularReference(obj, seen=None, path="root"):
    if seen is None:
        seen = {}

    obj_id = id(obj)
    if obj_id in seen:  # 循環参照が発生した場合
        return f"CIRCULAR_REFERENCE -> {seen[obj_id]}"  # どのパスで循環しているか記録
    
    seen[obj_id] = path  # 現在のオブジェクトのパスを記録

    if isinstance(obj, dict):
        return {key: ReplaceCircularReference(value, seen, f"{path}.{key}") for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ReplaceCircularReference(item, seen, f"{path}[{index}]") for index, item in enumerate(obj)]
    elif isinstance(obj, tuple):
        return tuple(ReplaceCircularReference(item, seen, f"{path}({index})") for index, item in enumerate(obj))
    else:
        return obj  # それ以外の型はそのまま返す


def DiffDictionaries(dict1, dict2, path=None):
    """
    2つの辞書の差分を change_settings の書式で表します（値の変更を含む）。

    Args:
        dict1 (dict): 比較元の辞書。
        dict2 (dict): 比較先の辞書。
        path (list, optional): 現在のパス (内部用). Defaults to None.

    Returns:
        list: change_settings 形式の差分リスト（値の変更を含む）。
    """
    changes = []
    if path is None:
        path = []

    for key in dict1:
        current_path = path + [key]
        if key not in dict2:
            changes.append({"operation": "delete", "target": current_path})
        elif dict1[key] != dict2[key]:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                changes.extend(DiffDictionaries(dict1[key], dict2[key], current_path))
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                len1 = len(dict1[key])
                len2 = len(dict2[key])
                max_len = max(len1, len2)
                for i in range(max_len):
                    current_list_path = current_path + [i]
                    if i >= len1:
                        changes.append({"operation": "add", "target": current_list_path, "value": dict2[key][i]})
                    elif i >= len2:
                        changes.append({"operation": "delete", "target": current_list_path})
                    elif dict1[key][i] != dict2[key][i]:
                        changes.append({"operation": "change", "target": current_list_path, "value": dict2[key][i]})
            else:
                changes.append({"operation": "change", "target": current_path, "value": dict2[key]})

    for key in dict2:
        if key not in dict1:
            changes.append({"operation": "add", "target": path + [key], "value": dict2[key]})

    return changes

def ChangeDictionary(change_settings, data):
    """
    change_settings の書式に基づいて辞書に差分を適用し、途中のパスが存在しない場合は作成します。
    途中の要素が辞書やリストでない場合は上書きします。

    Args:
        change_settings (list): change_settings 形式の差分リスト（値の変更を含む）。
        data (dict): 適用対象の辞書。

    Returns:
        dict: 差分が適用された新しい辞書。
    """
    new_data = copy.deepcopy(data)

    for change in change_settings:
        operation = change.get("operation")
        target_path = change.get("target")

        if not operation or not target_path:
            print(f"警告: 不正な設定項目があります: {change}")
            continue

        try:
            current = new_data
            for i in range(len(target_path)):
                key = target_path[i]
                if i < len(target_path) - 1:  # 最後の要素でない場合 (途中のパス)
                    next_key = target_path[i + 1]
                    if isinstance(current, dict):
                        if key not in current:
                            if isinstance(next_key, int):
                                current[key] = []
                            else:
                                current[key] = {}
                        elif not isinstance(current[key], (dict, list)):
                            # 途中の要素が辞書やリストでない場合は上書き
                            if isinstance(next_key, int):
                                current[key] = []
                            else:
                                current[key] = {}
                        current = current[key]
                    elif isinstance(current, list):
                        if not isinstance(key, int) or key < 0:
                            print(f"警告: リストのインデックスが無効です: {target_path[:i+1]}")
                            current = None
                            break
                        if key >= len(current):
                            # リストのインデックスが範囲外の場合は拡張
                            if isinstance(next_key, int):
                                current.extend([[]] * (key - len(current) + 1))
                            else:
                                current.extend([{}] * (key - len(current) + 1))
                        elif not isinstance(current[key], (dict, list)):
                            # 途中の要素が辞書やリストでない場合は上書き
                            if isinstance(next_key, int):
                                current[key] = []
                            else:
                                current[key] = {}
                        current = current[key]
                    else:
                        print(f"警告: 途中のパスが無効です (dict/listではありません): {target_path[:i+1]}")
                        current = None
                        break
                else:  # 最後の要素の場合
                    if current is not None:
                        if operation == "add" or operation == "change":
                            value_to_set = change.get("value",None)
                            if isinstance(current, dict):
                                current[key] = value_to_set
                            elif isinstance(current, list) and isinstance(key, int) and key <= len(current):
                                if key == len(current):
                                    current.append(value_to_set)
                                else:
                                    current[key] = value_to_set
                            else:
                                print(f"警告: 最後のターゲットが無効です: {target_path}")
                        elif operation == "delete":
                            if isinstance(current, dict) and key in current:
                                del current[key]
                            elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
                                del current[key]
                            else:
                                print(f"警告: 削除対象が見つかりません: {target_path}")
                        else:
                            print(f"警告: 不明な操作です: {operation}")

        except Exception as e:
            print(f"エラーが発生しました: {e}, 設定: {change}")

    return new_data
# Defaultの辞書Dataを設定
default_settings = {
    "action" : "COPY",
    "data_name": "data_name",
    "source_data": {
        "source1_name": {"X": 11, "Y": 1},
        "source2_name": {"X": 12, "Y": 2},
        "source3_name": {"X": 13, "Y": 3}
    },
    "data_structure": {
        "data1": {
            "copy1_name": "",
            "copy2_name": "",
            "copy3_name": "",
            "new_data": {
                "point1": ["source1_x", "source1_y"],
                "point2": ["source2_x", "source2_y"],
                "comment": "restructureの設定は深い層の辞書Dataのkeyを探し値にコピーし、配列の場合は要素を探して要素に上書きします。にも適用されます。名称には注意が必要です。",
                "not_oder_data": {"not_order1": ["aa", "bb", "CC"], "not_order2": [1, 2, 3, 4], "Comment": "指示の無い項目は残す。"}
            }
        },
        "data2":{}
    },
    "restructure_settings": {
        "copy1_name" : "source1_name",
        "copy2_name" : "source2_name",
        "copy3_name" : "source3_name",
        "source1_x": "Result_A.X",
        "source1_y": "Result_A.Y",
        "source2_x": "Result_B.X",
        "source2_y": "Result_B.Y",
    }
}
# 辞書設定の読込と機能実行
def Execute(settings_dictionary):
    #設定の読込
    data_name =  settings_dictionary.get("data_name","")
    source_data = settings_dictionary.get("source_data",{})
    data_structure = settings_dictionary.get("data_structure",{})
    restructure_settings = settings_dictionary.get("restructure_settings",{})
    #機能実行 
    result_dictionary = {"success": True}
    copy_data = RestructureData(source_data,data_structure,restructure_settings)
    result_dictionary[data_name] = copy_data
    # 結果を表示
    #print(copy_data)
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    settings_dictionary = FunctionUtility.ArgumentGet(default_settings)
    result_dictionary = Execute(settings_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == '__main__':
    main()

