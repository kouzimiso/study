import os
import mmap
import pickle
import portalocker
import unittest
class SharedMemory_MMap:
    def __init__(self,file_path = "shared_memory.dat"):
        self.map_file_path = file_path

    def write(self, key, value):
        write_key_to_shared_memory(self.map_file_path,key,value)

    def read(self, key):
        return read_key_from_shared_memory(self.map_file_path,key)

    def clear(self):
        clear_shared_memory(self.map_file_path)

    def clear_key(self, key):
        clear_key_from_shared_memory(self.map_file_path,key)

    def get_all_data(self):
        return read_from_shared_memory(self.map_file_path)
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

# 共有メモリからデータを読み込む
def read_from_shared_memory(file_path):
    if not os.path.exists(file_path):
        return {}

    with open(file_path, mode="r+b") as file:
        portalocker.lock(file, portalocker.LOCK_SH)
        with mmap.mmap(file.fileno(), 0) as mm:
            serialized_data = mm.read()
            portalocker.unlock(file)
            return deserialize_data(serialized_data)
# 特定のキーの値を共有メモリから読み込む
def read_key_from_shared_memory(file_path, key):
    data = read_from_shared_memory(file_path)
    return data.get(key, None)

# 共有メモリにデータを書き込む
def write_key_to_shared_memory(file_path, key, value):
    # ファイルが存在しない場合は作成
    if not os.path.exists(file_path):
        with open(file_path, mode="w+b") as file:
            # 初期データとして空の辞書を書き込む
            initial_data = serialize_data({})
            file.write(initial_data)
            file.flush()

    with open(file_path, mode="r+b") as file:
        # 排他ロックを取得
        portalocker.lock(file, portalocker.LOCK_EX)
        
        # メモリマップのサイズ調整と読み書き操作
        try:
            # メモリマップを取得し、共有メモリを読み込む
            file_size = os.path.getsize(file_path)
            with mmap.mmap(file.fileno(), file_size) as mm:
                serialized_data = mm.read()
                existing_data = deserialize_data(serialized_data)
                
                # データの更新
                existing_data[key] = value
                new_serialized_data = serialize_data(existing_data)
                data_size = len(new_serialized_data)

                # ファイルサイズを確保して再度メモリマップ
                ensure_file_size(file, data_size)
                mm.resize(data_size)
                mm.seek(0)
                mm.write(new_serialized_data)
                mm.flush()        
        finally:
            # ロックを解除
            portalocker.unlock(file)

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
            existing_data = read_from_shared_memory(file_path)
            if key in existing_data:
                del existing_data[key]  # 指定したキーを削除
            serialized_data = serialize_data(existing_data)
            data_size = len(serialized_data)

            ensure_file_size(file, data_size)
            file.seek(0)
            with mmap.mmap(file.fileno(), data_size) as mm:
                mm.write(serialized_data)
                mm.flush()
        finally:
            portalocker.unlock(file)
            

# 共有メモリから特定のキーを削除
def remove_key_from_shared_memory(file_path, key):
    existing_data = read_from_shared_memory(file_path)
    if key in existing_data:
        del existing_data[key]
    serialized_data = serialize_data(existing_data)
    data_size = len(serialized_data)

    with open(file_path, mode="r+b") as file:
        portalocker.lock(file, portalocker.LOCK_EX)
        ensure_file_size(file, data_size)
        with mmap.mmap(file.fileno(), data_size) as mm:
            mm.seek(0)
            mm.write(serialized_data)
            mm.flush()
        portalocker.unlock(file)        

class TestSharedMemory(unittest.TestCase):
    
    def setUp(self):
        """テスト用の共有メモリファイルを作成する"""
        self.file_path = "test_shared_memory.dat"
        # テスト用に空のファイルを準備する
        with open(self.file_path, "wb") as f:
            f.write(b'\x00' * 1024)
    
    def tearDown(self):
        """テスト終了後に共有メモリファイルを削除する"""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_write_and_read(self):
        """書き込みと読み込みが正常に動作するかをテスト"""
        write_key_to_shared_memory(self.file_path, "username", "kouzimiso")
        result = read_key_from_shared_memory(self.file_path, "username")
        self.assertEqual(result, "kouzimiso")

    def test_overwrite_key(self):
        """既存のキーを上書きしても正しく動作するかをテスト"""
        write_key_to_shared_memory(self.file_path, "username", "kouzimiso")
        write_key_to_shared_memory(self.file_path, "username", "new_value")
        result = read_key_from_shared_memory(self.file_path, "username")
        self.assertEqual(result, "new_value")

    def test_clear_shared_memory(self):
        # 共有メモリに書き込む
        write_key_to_shared_memory(self.file_path,"key", "kouzimiso")

        # クリア処理を実行
        clear_shared_memory(self.file_path)

        # クリア後に値がないことを確認
        result = read_from_shared_memory("key")
        self.assertIn(result, [None, {}], "クリア後に値が残っています")

    def test_remove_key(self):
        """特定のキーが正しく削除されるかをテスト"""
        write_key_to_shared_memory(self.file_path, "username", "kouzimiso")
        remove_key_from_shared_memory(self.file_path, "username")
        result = read_key_from_shared_memory(self.file_path, "username")
        self.assertIsNone(result)

    def test_read_nonexistent_key(self):
        """存在しないキーに対する読み込みがNoneを返すかをテスト"""
        result = read_key_from_shared_memory(self.file_path, "nonexistent_key")
        self.assertIsNone(result)

# テストの実行
if __name__ == "__main__":
    unittest.main()

