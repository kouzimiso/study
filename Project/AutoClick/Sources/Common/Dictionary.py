# -*- coding: utf-8 -*-
import copy
import FunctionUtility

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

# Defaultの辞書Dataを設定
default_dictionary = {
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
    result_dictionary = {"result": True}
    copy_data = RestructureData(source_data,data_structure,restructure_settings)
    result_dictionary[data_name] = copy_data
    # 結果を表示
    #print(copy_data)
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    settings_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    result_dictionary = Execute(settings_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == '__main__':
    main()

