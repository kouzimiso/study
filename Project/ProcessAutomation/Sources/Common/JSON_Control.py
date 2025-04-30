import json
import os
import traceback
import LogMessage
import DictionaryControl
import datetime
import re
import tokenize
import io
import ast

def WriteDictionary(file_path,data_dictionary):
    file = open(file_path,'w', encoding='utf-8')
    json.dump(data_dictionary, file,  ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
    file.close()

def ToString(data_dictionary=None):
    if data_dictionary == None:
        data_dictionary ={}
    return json.dumps(data_dictionary)
    
def ReadDictionary(file_path,data_dictionary=None,details = None):
    if data_dictionary == None:
        data_dictionary ={}
    if details == None :
        details = {"success":True}
    if os.path.isfile(file_path):
        try:
            file = open(file_path,'r', encoding='utf-8')

            temp_dictionary = json.load(file)
            data_dictionary.update(temp_dictionary)
        except FileNotFoundError as e:
            error_dictionary =LogMessage.Get_Error_Dictionary()
            #type(e).__name__ ,"result_value":str(e) ,"traceback" : traceback.format_exc()
            details.update({"success":False ,"message":"FileNotFoundError" , "level" :"ERROR","error":error_dictionary})
            
        except json.JSONDecodeError as e:
            error_dictionary =LogMessage.Get_Error_Dictionary()
            details.update({"success":False ,"message":"JSONDecodeError" , "level" :"ERROR","error":error_dictionary})
            
        except Exception as e:
            error_dictionary =LogMessage.Get_Error_Dictionary()
            details.update({"success":False ,"message":"Exception" , "level" :"ERROR","error":error_dictionary})
        file.close()
    else:
        details.update({"success":False ,"message":"FileNotFoundError", "level" :"ERROR","error":"The specifeed file is nothing"})
        
    return data_dictionary

def JSONToDictionary(data_json,data_dictionary = None, details = None):
    temp_dictionary = {}  # temp_dictionaryを初期化
    if data_dictionary == None:
        data_dictionary ={}
    if details == None :
        details = {}
    try:
        temp_dictionary = json.loads(data_json)
        data_dictionary.update(temp_dictionary)
                    
    except json.JSONDecodeError as e:
        error_dictionary =LogMessage.Get_Error_Dictionary()
        details.update({"success":False ,"message":"JSONDecodeError" , "level" :"ERROR","error":error_dictionary})
              
    except Exception as e:
        error_dictionary =LogMessage.Get_Error_Dictionary()
        details.update({"success":False ,"message":"Exception" , "level" :"ERROR","error":error_dictionary})
    return temp_dictionary

def MergeJSONFiles(base_file_path,merge_file_path,merge_key,new_merge_key):
        # JSONデータの読み込み
    base_data = ReadDictionary(base_file_path)
    merge_data_content = ReadDictionary(merge_file_path)
    if new_merge_key == "":
        new_merge_key = merge_key

    # データのマージ
    try:
        merged_data = DictionaryControl.MergeDictionayKeyAndValue(base_data, merge_data_content, merge_key, new_merge_key)
    except KeyError as e:
        print(f"Error: {e}")
        return base_data
    return merged_data


def normalize_JSON_string(json_string):
    """JSON文字列を正規化する"""
    json_string = json_string.replace("'", '"')
    return re.sub(r'(\w+):', r'"\1":', json_string)

def parse_JSON(json_string):
    """JSON文字列をパースする"""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        normalized_string = normalize_JSON_string(json_string)
        return json.loads(normalized_string)

def extract_dicts_from_text(text):
    """文章から辞書データを抽出し、辞書リストと本文を分離する"""
    normalized_text = normalize_JSON_string(text)  # 抽出前に正規化
    pattern = r"\{[^{}]+\}"  # 簡易的な辞書の抽出（ネストには非対応）
    matches = re.findall(pattern, normalized_text)

    extracted_dicts = {
        f"dict{i+1}": parse_JSON(match) for i, match in enumerate(matches)
    }

    return extracted_dicts

def replace_dicts_with_placeholders(text, extracted_dicts):
    """本文内の辞書データを {dictX} のプレースホルダーに置換する"""
    normalized_text = normalize_JSON_string(text)  # 置換前に正規化
    for key, value in extracted_dicts.items():
        normalized_value = json.dumps(value, ensure_ascii=False)
        normalized_text = normalized_text.replace(normalized_value, f"{{{key}}}")
    return normalized_text

def construct_dictionary_structure(text,extract_dicts=False):
    "本文を受け取り、JSON構造を作成する"
    escape_text = escape_for_dictionary(text)
    if extract_dicts:
        extracted_dicts = extract_dicts_from_text(escape_text)
        body_text = replace_dicts_with_placeholders(escape_text, extracted_dicts)
        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d %H:%M:%S %f")[:-3],
            "text": body_text,
            "references": extracted_dicts  # 簡略化されたreferences
        }
    else:

        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "text": escape_text
        }

def add_text_to_dictionary(dictionary_data,title,text, add_data=None,extract_dicts=False):
    """文章をJSON形式に変換する"""
    json_structure = construct_dictionary_structure(text,extract_dicts)

    "dictionary_dataにデータを加える。"
    if add_data:
        json_structure.update(add_data)
    # 既存のJSONデータに新しいタイトルを追加
    dictionary_data[title] = json_structure
    return dictionary_data

def restore_dict(match):
    """マッチしたプレースホルダーを辞書の値に置き換える。"""
    key = match.group(1)
    if key in references:
        return json.dumps(references[key], ensure_ascii=False)  # JSON文字列に変換
    else:
        return match.group(0)

def restore_text_and_references(text, refs):
    """テキスト内のプレースホルダーを辞書の値で置き換える。"""
    global references  # グローバル変数を使用することを宣言
    references = refs
    restored_text = re.sub(r"\{(dict\d+)\}", restore_dict, text)
    return restored_text

def replace_list_values(original_list, replace_dict):
    """リスト内の要素を辞書の設定で置換（元のリストを変更しない）"""
    return list(map(lambda item: replace_dict.get(item, item), original_list))


def escape_for_dictionary(text):
    escaped_code = text.replace('\\', '\\\\').replace('"', '\\"')
    return json.dumps({"code": escaped_code}, ensure_ascii=False)

def unescape_for_dictionary(json_string):
    data = json.loads(json_string)
    escaped_code = data["code"]
    return escaped_code.replace('\\\\', '\\').replace('\\"', '"')

def main():
    try:
        with open("test.json", "r", encoding="utf-8") as f:
            dictionary_data = json.load(f)
    except FileNotFoundError:
        dictionary_data = {}
    # 使用例
    program_code = """
    この文章には {"name": "Alice", "age": 25} という辞書があります。
    また、別の辞書 {'city': 'Tokyo', 'country': 'Japan'} もあります。
    def my_function(text):
        print("Hello, " + text + "\\n")  # 改行文字を含む文字列
        return {"success": text}
    """
    json_string = escape_for_dictionary(program_code)
    print(json_string)

    restored_code = unescape_for_dictionary(json_string)
    print(restored_code)


    text = "この文章には {'name': 'Alice', 'age': 25} という辞書があります。\nまた、別の辞書 {'city': 'Tokyo', 'country': 'Japan'} もあります。"
    title ="サンプル記事"
    add_data = {"tags": ["テスト", "辞書処理"], "summary":"辞書をJSONに保存するサンプル"}
    dictionary_data = add_text_to_dictionary(dictionary_data,title,text,add_data,True )
    json_str = json.dumps(dictionary_data, ensure_ascii=False, indent=4)
    print(json_str)
    text = dictionary_data[title]["text"]
    references = dictionary_data[title]["references"]
    restored_text = restore_text_and_references(text,references)
    print(restored_text)

    list_data = ["A", "B", "C"]
    replace_setting = {"A": "D", "B": "E"}

    new_list = replace_list_values(list_data, replace_setting)
    print(new_list)  # ['D', 'E', 'C']
    # test.jsonへの書き込み
    with open("test.json", "w", encoding="utf-8") as f:
        json.dump(dictionary_data, f, ensure_ascii=False, indent=4)
if __name__ == '__main__':
    main()
