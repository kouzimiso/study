import json
import mmap
import os
from typing import List, Dict, Any, Union

def load_json_file(file_path: str) -> Dict[str, Any]:
    """JSONファイルを辞書形式で読み込む関数"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_shared_memory_file(file_path: str) -> Dict[str, Any]:
    """共有メモリファイルを辞書形式で読み込む関数"""
    with open(file_path, "r+b") as f:
        # ファイルをメモリにマッピング
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            data = mm.read().decode("utf-8")  # デコードして文字列に変換
            return json.loads(data)  # JSONデータとして辞書に変換

def load_from_file(file_path: str) -> Dict[str, Any]:
    """ファイル拡張子に応じて適切な方法でファイルを読み込む関数"""
    _, ext = os.path.splitext(file_path)
    if ext == '.json':
        return load_json_file(file_path)
    elif ext == '.shm':
        return load_shared_memory_file(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def resolve_variable(
    var_name: str,
    data_sources: List[Union[Dict[str, Any], str]]
) -> Any:
    """
    変数を解決する関数。data_sources は辞書やファイルパスを含むリストで、
    順番に参照して最初に見つかった値を返す。
    """
    if isinstance(data_sources, list) == False:
        data_sources=[data_sources]  
      
    for source in data_sources:
        if isinstance(source, dict):  # 辞書の場合
            if var_name in source:
                return source[var_name]
        elif isinstance(source, str):  # ファイルパスの場合
            try:
                file_data = load_from_file(source)
                if var_name in file_data:
                    return file_data[var_name]
            except (FileNotFoundError, ValueError) as e:
                print(f"Error accessing file {source}: {e}")
        else:
            raise ValueError("Unsupported source type. Must be a dict or file path.")
    return var_name
    #raise ValueError(f"Variable '{var_name}' not found in any source.")

# 使用例
local_vars = {'value1': 2, 'value2': 3}
shared_memory = {'value3': 20}
json_file = 'Sources\Test\config.json'  # JSONファイルに保存されている変数群
shared_memory_file = 'data.shm'  # 共有メモリファイル

# 参照元リスト（ローカル、共有メモリ、設定ファイルの順に探す）
data_sources = [local_vars, shared_memory, json_file, shared_memory_file]

# 変数を解決
print(resolve_variable("value1", data_sources))  # 例: ローカル変数
print(resolve_variable("value3", data_sources))  # 例: 共有メモリ
print(resolve_variable("value4", data_sources))  # 例: ファイル内の変数
