#辞書と配列が混在したデータを比較する関数。
def DeepCompare(data1, data2):
    # データの型が異なる場合、直ちに等しくないと判断
    if type(data1) != type(data2):
        return False

    # 辞書を比較する場合
    if isinstance(data1, dict):
        # キーの数が異なる場合、直ちに等しくないと判断
        if len(data1) != len(data2):
            return False

        for key in data1:
            if key not in data2:
                return False
            if not deep_compare(data1[key], data2[key]):
                return False

        return True

    # リストまたはタプルを比較する場合
    elif isinstance(data1, (list, tuple)):
        # 要素数が異なる場合、直ちに等しくないと判断
        if len(data1) != len(data2):
            return False

        for item1, item2 in zip(data1, data2):
            if not deep_compare(item1, item2):
                return False

        return True

    # それ以外の型（int、str、floatなど）の場合は、値が等しいかどうかを比較
    else:
        return data1 == data2
