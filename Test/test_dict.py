import copy

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
                            value_to_set = change.get("value")
                            if operation == "change" and value_to_set is None:
                                print(f"警告: 'change' 操作に必要な 'value' がありません: {change}")
                                continue
                            if value_to_set is not None:
                                if isinstance(current, dict):
                                    current[key] = value_to_set
                                elif isinstance(current, list) and isinstance(key, int) and key <= len(current):
                                    if key == len(current):
                                        current.append(value_to_set)
                                    else:
                                        current[key] = value_to_set
                                else:
                                    print(f"警告: 最後のターゲットが無効です: {target_path}")
                            elif operation == "add":
                                print(f"警告: 'add' 操作に必要な 'value' がありません: {change}")
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

# 使用例 (修正されたテストケースを含む)
data = {}
change_settings = [
    {"operation": "add", "target": ["A", "B", "C"], "value": "value_c"},
    {"operation": "add", "target": ["A", "B", "D"], "value": "value_d"},
    {"operation": "add", "target": ["A", "E", 0], "value": "value_e0"},
    {"operation": "add", "target": ["A", "E", 1], "value": "value_e1"},
    {"operation": "change", "target": ["A", "B", "C"], "value": "updated_value_c"},
    {"operation": "delete", "target": ["A", "B", "D"]},
    {"operation": "add", "target": ["F", 0, "G"], "value": "value_g"},
    {"operation": "add", "target": ["F", 1], "value": "value_f1"},
    {"operation": "change", "target": ["F", 0, "G"], "value": "updated_value_g"},
]

updated_data = ChangeDictionary(change_settings, data)
print(updated_data)

data2 = {"existing_key": 1}
change_settings2 = [
    {"operation": "add", "target": ["existing_key", "nested"], "value": 2},
]
updated_data2 = ChangeDictionary(change_settings2, data2)
print(updated_data2)

data3 = {"top_level": "string"}
change_settings3 = [
    {"operation": "add", "target": ["top_level", "nested_key"], "value": "nested_value"}
]
updated_data3 = ChangeDictionary(change_settings3, data3)
print(updated_data3)