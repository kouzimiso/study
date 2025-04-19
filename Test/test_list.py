from typing import List, Union, Dict
import re


def format_merge_multiple_list(
    format_string: str, 
    placeholder_format: Union[str, List[Union[str, None]]] = "list{index}_",
    **str_lists: List[str]
) -> List[str]:
    """
    複数のリストを指定フォーマットで結合し、足りない部分を補完する汎用関数。

    :param format_string: 変数を含むフォーマット文字列 (例: "{list1}={list2},{list3},{list4}")
    :param placeholder_format: 
        - 文字列の場合: 余分な値に割り当てるプレースホルダーのフォーマット (例: "list{index}")
        - リストの場合: 各引数ごとに異なるプレースホルダーを指定可能 (例: ["list1{index}", "list2{index}", None])
        - None の場合: 余った値を出力しない
    :param str_lists: 任意の数のリスト（例: list1=[...], list2=[...]）
    :return: フォーマット済みの引数リスト
    """
    result = []
    max_length = max(map(len, str_lists.values())) if str_lists else 0

    # プレースホルダーのリストが指定されていなければ、すべて同じフォーマットを使用
    if isinstance(placeholder_format, str):
        placeholder_format = [placeholder_format] * len(str_lists)
    
    list_keys = list(str_lists.keys())

    for i in range(max_length):
        formatted_lists = {}

        for idx, key in enumerate(list_keys):
            values = str_lists[key]
            if i < len(values):
                formatted_lists[key] = values[i]  # 値がある場合
            else:
                if idx < len(placeholder_format) and placeholder_format[idx] is not None:
                    formatted_lists[key] = placeholder_format[idx].format(index=i+1)  # プレースホルダーを使用

        # `format()` を適用
        formatted_str = format_string.format(**{k: v for k, v in formatted_lists.items() if v is not None})
        result.append(formatted_str)

    return result


# ---- 使用例 ----
list1 = ["A", "B"]
list2 = ["X"]
list3 = ["1", "2", "3"]
list4 = ["a", ]

print(format_merge_multiple_list(
    format_string="{list1}={list2},{list3},{list4}", 
    placeholder_format="list{index}", 
    list1=list1,
    list2=list2,
    list3=list3,
    list4=list4  # ここが空
))

print(format_merge_multiple_list(
    "{lista}={list2},{list3},{list4}", 
    ["list1_{index}", "list2_{index}", "list3_{index}", ""], 
    lista=list1,
    list2=list2,
    list3=list3,
    list4=list4  # ここが空
))

# 出力:
# ['A=X,1', 'B=list2{2},2', 'list1{3}=list2{3},3']
