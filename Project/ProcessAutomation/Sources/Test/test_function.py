import re
from typing import List, Union, Any
# サンプルのソースコード
source_code = """
with open(file_name, "r", encoding="utf-8") as f:
    text = f.read()
    print(text)
"""

# 置換設定
replace_settings = {
    "target": ' with open(file_path, "r", encoding=encoding_type) as f:\n   result = f.read()',
    "source_priority_word_list": ["file_path", "encoding_type", "result"],
    "ignore_word_list": [" ", "\t","\n"],
    "sign_list": ["(",")","=",","],
    "replace_word": "result = read_file(file_name , encoding_type)"
}
def split_text_including_delimiters(text: str, delimiters: List[str]) -> List[str]:
    """
    文字列を区切り文字を含めて分割する純粋関数

    Args:
        text (str): 分割対象の文字列
        delimiters (List[str]): 区切り文字のリスト

    Returns:
        List[str]: 分割された文字列のリスト
    """
    parts = []
    start = 0
    for i, char in enumerate(text):
        if char in delimiters:
            parts.append(text[start:i])
            parts.append(char)
            start = i + 1
    parts.append(text[start:])
    return parts

def split_including_delimiters(source: Union[str, List[str]], delimiters: List[str]) -> List[Any]:
    """
    文字列または文字列リストを複数の区切り文字を含めて分割する純粋関数

    Args:
        text (Union[str, List[str]]): 分割対象の文字列または文字列リスト
        delimiters (List[str]): 区切り文字のリスト

    Returns:
        List[Any]: 分割された要素のリスト (文字列またはリスト)
    """

    if isinstance(source, str):
        return split_text_including_delimiters(source, delimiters)
    elif isinstance(source, list):
        item = []
        for text in source:
            item.extend(split_text_including_delimiters(text, delimiters))
        return item
    else:
        raise TypeError("Input must be a string or a list of strings.")

def multi_split(text, delimiters):
    """
    複数の区切り文字を1つに統一し、重複する区切り文字を単一にして文字列を分割する関数

    Args:
        text (str): 分割対象の文字列
        delimiters (list): 区切り文字のリスト
        unified_delimiter (str, optional): 統一する区切り文字 (デフォルト: " ")

    Returns:
        list: 分割された文字列のリスト
    """
    for delimiter in delimiters:
        unified_delimiter = delimiter
        if unified_delimiter != "":
            break
    # 正規表現パターンを作成
    pattern = "|".join(map(re.escape, delimiters))

    # 区切り文字を統一し、重複する区切り文字を単一にする
    normalized_text = re.sub(r"(" + pattern + ")+", unified_delimiter, text)

    # 文字列を分割
    result = normalized_text.split(unified_delimiter)

    # 空文字列を取り除く
    result = list(filter(None, result))

    return result

# 文字列を置換する関数
def replace_function_call(source_code, replace_settings):
    target = replace_settings["target"]
    source_priority_word_list = replace_settings["source_priority_word_list"]#置換時にsourceの情報を優先して残すList
    ignore_word_list = replace_settings["ignore_word_list"]
    sign_list = replace_settings["sign_list"]
    replace_word = replace_settings["replace_word"]#置換後の文字列(ただし、source_priority_word_listに含まれる文字列はsourceの情報に置き換えられる）


    # targetをignore_word_listとsource_priority_word_listで区切ってリストを作成
    
    splited_source_list = split_including_delimiters(source_code,ignore_word_list)
    splited_source_list = split_including_delimiters(splited_source_list,sign_list)
    splited_target_list = multi_split(target,ignore_word_list)
    splited_target_list=split_including_delimiters(splited_target_list,sign_list)
    splited_target_list=split_including_delimiters(splited_target_list,source_priority_word_list)

    # target_listの各文字列を順に一致させていく
    source_priority_word_dict = {}
    complete_list=[]
    #replace_wordを補正した文字列を作成
    temp_replace_word =""
    temp_list=[]
    match_list=[]
    index = 0
    target_index = len(splited_target_list)
    for source in splited_source_list:
        word = splited_target_list[index]
        if source == word:
            temp_list.append(source)
            match_list.append(source)
            index += 1
            if word in source_priority_word_list:
                match_value = source_priority_word_dict.get(word,None)
                if match_value is None:
                    source_priority_word_dict[word]=source
                elif match_value != source:
                    #一致しなかった場合、判定中のtemp_listはcomplete_listに加える
                    complete_list.extend(temp_list)
                    #source_priority_word_dictは初期化する。
                    source_priority_word_dict={}
                    temp_list=[]
                    match_list=[]
                    index = 0
        elif source in ignore_word_list:
            if temp_list == []:
                complete_list.append(source)
            else:
                temp_list.append(source)
        elif source =="":
            continue


        elif word in source_priority_word_list:
            #source_priority_word_listと一致した場合、temp_listにsourceの文字列を追加
            temp_list.append(source)
            match_list.append(source)
            index += 1
            match_value = source_priority_word_dict.get(word,None)
            if match_value is None:
                source_priority_word_dict[word]=source
            elif match_value != source:
                #一致しなかった場合、判定中のtemp_listはcomplete_listに加える
                complete_list.extend(temp_list)
                #source_priority_word_dictは初期化する。
                source_priority_word_dict={}
                temp_list=[]
                match_list=[]
                index = 0
        
        else:
            #一致しなかった場合、判定中のtemp_listはcomplete_listに加える
            temp_list.append(source)
            complete_list.extend(temp_list)
            #source_priority_word_dictは初期化する。
            source_priority_word_dict={}
            temp_list=[]
            match_list=[]
            index = 0
        match_index=len(match_list)
        if match_index == target_index:
            #replace_wordを補正するため、コピーした文字列を作成
            temp_replace_word=replace_word    
            #replace_wordに含まれるsource_priority_word_dictのkeyをvalueで置換
            for word, value in source_priority_word_dict.items():
                temp_replace_word = temp_replace_word.replace(word, value)
            complete_list.append(temp_replace_word)
            source_priority_word_dict={}
            temp_list=[]
            match_list=[]
            index = 0

    
    return "".join(complete_list)


# 置換後のコードを取得
modified_code = replace_function_call(source_code, replace_settings)

# 結果を出力
print(modified_code)