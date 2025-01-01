class Model:
    def __init__(self):
        self._data = {}

    def set_data(self, key, value):
        self._data[key] = value
        self.notify_changes(key)

    def get_data(self, key):
        return self._data.get(key)

    def notify_changes(self, key):
        # 辞書データの変更を通知するメソッド
        #ViewModelで上書きした関数が実行される。
        #ViewModelで上書きしない場合に本関数が実行される。
        pass

class ViewModel:
    def __init__(self, model):
        self.model = model
        self.model.notify_changes = self.on_data_changed

    def on_data_changed(self, key):
        # Modelからの変更通知を受け取って、ViewModelを更新する
        value = self.model.get_data(key)
        self.update_view(key, value)

    def update_view(self, key, value):
        # ViewModelのビューを更新するメソッド
        print(f"Received update: Key={key}, Value={value}")

# テスト用のコード
model = Model()
viewModel = ViewModel(model)

# データの変更
model.set_data('key1', 'value1')
