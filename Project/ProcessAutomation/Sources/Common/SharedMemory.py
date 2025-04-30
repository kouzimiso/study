import multiprocessing
import mmap
import pickle
import os
import portalocker
import DictionaryControl
import platform

class SharedMemory:
    def __init__(self):
        self.data = multiprocessing.Manager().dict()

    def write(self, key, value):
        self.data[key] = value

    def read(self, key):
        return self.data.get(key)

    def clear(self):
        self.data.clear()

    def clear_key(self, key):
        if key in self.data:
            del self.data[key]

    def read_all_data(self):
        return dict(self.data)
    
class SharedMemory_MMap:
    def __init__(self,file_path = "shared_memory.shm"):
        self.MAP_FILE_NAME = file_path

    def write(self, key, value):
        write_to_shared_memory(self.MAP_FILE_NAME,key,value)

    def read(self, key):
        return read_key_from_shared_memory(self.MAP_FILE_NAME,key)

    def clear(self):
        clear_shared_memory(self.MAP_FILE_NAME)

    def clear_key(self, key):
        clear_key_from_shared_memory(self.MAP_FILE_NAME,key)

    def read_all_data(self):
        return read_from_shared_memory(self.MAP_FILE_NAME)
    
def write_process(shared_memory,key,value):
    shared_memory.write(key,value)

def read_process(shared_memory,name):
    data = shared_memory.read(name)
    print(data)



# データシリアライズ・デシリアライズ
def serialize_data(data):
    return pickle.dumps(data)

def deserialize_data(serialized_data):
    try:
        return pickle.loads(serialized_data) if serialized_data else {}
    except (pickle.UnpicklingError, EOFError):
        return {}

# ファイルサイズ確認と調整
def ensure_file_size(file, data_size):
    file_size = os.path.getsize(file.name)
    if data_size > file_size:
        file.seek(data_size - 1)
        file.write(b'\x00')

def initialize_file_if_missing(file_path, min_size):
    """ファイルが存在しない場合に作成して初期化"""
    if not os.path.exists(file_path):
        with open(file_path, "wb") as file:
            file.truncate(min_size)

def ensure_file_size(file, size):
    """ファイルサイズを指定サイズ以上に調整"""
    file.seek(0, os.SEEK_END)
    current_size = file.tell()
    if current_size < size:
        file.truncate(size)
def read_from_mmap(file, size):
    """メモリマップからデータを読み取る"""
    with mmap.mmap(file.fileno(), size) as mm:
        return mm.read()

def write_to_mmap(file, data):
    """メモリマップにデータを書き込む"""
    data_size = len(data)
    
    # ファイルサイズを確保する
    ensure_file_size(file, data_size)
    
    # macOS とそれ以外で処理を分岐
    if platform.system() == "Darwin":  # macOS の場合
        file.flush()
        with open(file.name, 'r+b') as f:
            # mmap を新たに作成しデータを書き込む
            mm = mmap.mmap(f.fileno(), data_size)
            mm.seek(0)
            mm.write(data)
            mm.flush()
            mm.close()
    else:  # Linux などの場合
        with mmap.mmap(file.fileno(), data_size) as mm:
            mm.resize(data_size)
            mm.seek(0)
            mm.write(data)
            mm.flush()


def lock_and_execute(file_path, lock_mode, action, *args):
    """ファイルをロックして処理を実行"""
    with open(file_path, "r+b") as file:
        portalocker.lock(file, lock_mode)
        try:
            return action(file, *args)
        finally:
            portalocker.unlock(file)

        
def read_shared_memory_action(file, size):
    """共有メモリからデータを読み込むアクション"""
    serialized_data = read_from_mmap(file, size)
    return deserialize_data(serialized_data)

def write_shared_memory_action(file, key, value, size):
    """共有メモリにデータを書き込むアクション"""
    source_data = deserialize_data(read_from_mmap(file, size))
    source_data[key] = value
    new_data = serialize_data(source_data)
    write_to_mmap(file, new_data)

def update_shared_memory_action(file, new_data, depth, size):
    """
    ファイルのメモリマップを操作して、指定された層数までデータを更新。

    :param file: ファイルオブジェクト
    :param new_data: 書き込む新しい辞書データ
    :param depth: 辞書の層数（深さ）
    :param size: ファイルサイズ
    """
    source_data = deserialize_data(read_from_mmap(file, size))

    # 辞書のマージ処理（指定の深さまで更新）
    updated_data = DictionaryControl.MergeDictionayWithDepth(source_data, new_data, depth)

    # 更新後のデータを直列化して書き込む
    new_serialized_data = serialize_data(updated_data)
    write_to_mmap(file, new_serialized_data)


def write_dictionary_to_memory_action(file, dictionary, size):
    """辞書全体を共有メモリに書き込むアクション"""
    source_data = deserialize_data(read_from_mmap(file, size))
    source_data.update(dictionary)
    new_data = serialize_data(source_data)
    write_to_mmap(file, new_data)


def read_from_shared_memory(file_path,default_value={}):
    """共有メモリからデータを読み込む"""
    if not os.path.exists(file_path):
        return default_value
    size = os.path.getsize(file_path)
    return lock_and_execute(file_path, portalocker.LOCK_SH, read_shared_memory_action, size)

def write_to_shared_memory(file_path, key, value):
    """共有メモリにデータを書き込む"""
    initialize_file_if_missing(file_path, 1024)
    size = os.path.getsize(file_path)
    lock_and_execute(file_path, portalocker.LOCK_EX, write_shared_memory_action, key, value, size)

def update_dictionary_to_shared_memory(file_path, dictionary, depth=1):
    """
    共有メモリにデータを更新。
    指定された層数まで既存データを保持し、新しいデータを追加。

    :param file_path: 共有メモリファイルのパス
    :param new_data: 書き込む新しい辞書データ
    :param depth: 辞書の層数（深さ）
    """
    initialize_file_if_missing(file_path, 1024)
    size = os.path.getsize(file_path)
    lock_and_execute(file_path, portalocker.LOCK_EX, update_shared_memory_action, dictionary, depth, size)

def write_dictionary_to_shared_memory(file_path, dictionary):
    """辞書全体を共有メモリに書き込む"""
    initialize_file_if_missing(file_path, 1024)
    size = os.path.getsize(file_path)
    lock_and_execute(file_path, portalocker.LOCK_EX, write_dictionary_to_memory_action, dictionary, size)
                 
# 共有メモリ全体をクリア
def clear_shared_memory(file_path):
    with open(file_path, mode="r+b") as file:
        portalocker.lock(file, portalocker.LOCK_EX)
        try:
            # 空のデータを書き込む
            empty_data = serialize_data({})
            data_size = len(empty_data)

            ensure_file_size(file, data_size)
            file.seek(0)
            with mmap.mmap(file.fileno(), data_size) as mm:
                mm.write(empty_data)
                mm.flush()
        finally:
            portalocker.unlock(file)
            
# 共有メモリから特定のキーをクリア
def clear_key_from_shared_memory(file_path, key):
    with open(file_path, mode="r+b") as file:
        portalocker.lock(file, portalocker.LOCK_EX)
        try:
            source_data = read_from_shared_memory(file_path)
            if key in source_data:
                del source_data[key]  # 指定したキーを削除
            serialized_data = serialize_data(source_data)
            data_size = len(serialized_data)

            ensure_file_size(file, data_size)
            file.seek(0)
            with mmap.mmap(file.fileno(), data_size) as mm:
                mm.write(serialized_data)
                mm.flush()
        finally:
            portalocker.unlock(file)

            
# 特定のキーの値を共有メモリから読み込む
def read_key_from_shared_memory(file_path, key, default_value = None):
    data = read_from_shared_memory(file_path)
    return data.get(key, default_value)

# 共有メモリから特定のキーを削除
def remove_key_from_shared_memory(file_path, key):
    source_data = read_from_shared_memory(file_path)
    if key in source_data:
        del source_data[key]
    serialized_data = serialize_data(source_data)
    data_size = len(serialized_data)

    with open(file_path, mode="r+b") as file:
        portalocker.lock(file, portalocker.LOCK_EX)
        ensure_file_size(file, data_size)
        with mmap.mmap(file.fileno(), data_size) as mm:
            mm.seek(0)
            mm.write(serialized_data)
            mm.flush()
        portalocker.unlock(file)



if __name__ == "__main__":
    
    write_dictionary_to_shared_memory("shared_memory.shm",{"test1":"1"})
    write_dictionary_to_shared_memory("shared_memory.shm",{"test2":{"test2":"2"}})
    data = read_from_shared_memory("shared_memory.shm")
    print(data)
    update_dictionary_to_shared_memory("shared_memory.shm",{"test1":{"test3":"3"},"test2":{"test3":"3"},},2)
    data = read_from_shared_memory("shared_memory.shm")
    print(data)
    # マルチプロセスでのテスト
    shared_memory_multiprocessing = SharedMemory()
    shared_memory_csharp = SharedMemory_MMap()

    # マルチプロセスでの書き込み
    process1 = multiprocessing.Process(target=write_process, args=(shared_memory_multiprocessing,"task1",{"data":"test1","id":1}))
    process1.start()
    process1.join()

    # マルチプロセスでの読み込み
    process3 = multiprocessing.Process(target=read_process, args=(shared_memory_multiprocessing,"task1"))
    process3.start()
    process3.join()

    process2 = multiprocessing.Process(target=write_process,  args=(shared_memory_csharp,"task2",{"data":"test2","id":2}))
    process2.start()
    process2.join()

    process4 = multiprocessing.Process(target=read_process, args=(shared_memory_csharp,"task2"))
    process4.start()
    process4.join()
    
    # 共有メモリのデータ一覧を表示
    print("Shared Memory Multiprocessing:", shared_memory_multiprocessing.read_all_data())
    print("Shared Memory CSharp:", shared_memory_csharp.read_all_data())

    # 指定したキーの共有メモリを消去
    shared_memory_multiprocessing.clear_key("task1")
    shared_memory_csharp.clear_key("task2")

    # 共有メモリのデータ一覧を表示
    print("Shared Memory Multiprocessing:", shared_memory_multiprocessing.read_all_data())
    print("Shared Memory CSharp:", shared_memory_csharp.read_all_data())

    # 共有メモリを消去
    shared_memory_multiprocessing.clear()
    shared_memory_csharp.clear()
