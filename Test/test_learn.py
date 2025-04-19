import os
import json
import pickle

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # GPUを無視する設定
import tensorflow as tf
# GPUを無視する設定
tf.config.set_visible_devices([], 'GPU')
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Embedding, Input, concatenate
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.models import Model
from keras.callbacks import EarlyStopping

class Learning:
    def __init__(self):
        self.tokenizer = None
        self.model = None

    def preprocess_data(self, texts):
        encoded_texts = self.tokenizer.texts_to_sequences(texts)
        max_length = max([len(text) for text in encoded_texts])
        padded_texts = pad_sequences(encoded_texts, maxlen=max_length, padding='post')
        return padded_texts, max_length

    def build_input_layer(self , vocab_size , input_length):
        layer_input = Input(shape=(input_length,))
        layer_embedding = Embedding(vocab_size, 128, input_length=input_length)(layer_input)
        layer_lstm1 = LSTM(128, return_sequences=True)(layer_embedding)
        layer_lstm2 = LSTM(64)(layer_lstm1)
        return layer_input,layer_lstm2
        
    def build_model(self,input_layer_list,lstm_layer):

        concatenated = concatenate(lstm_layer)
        dense = Dense(64, activation='relu')(concatenated)
        output = Dense(1, activation='sigmoid')(dense)

        model = Model(inputs=input_layer_list, outputs=output)
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def tokenization(self, texts):
        self.tokenizer = Tokenizer()
        self.tokenizer.fit_on_texts(texts)

    def train(self, train_data, target_accuracy):
        conditions = [d["condition"] for d in train_data]
        datetimes = [d["datetime"] for d in train_data]
        results = [d['result'] for d in train_data]

        all_texts = conditions + datetimes
        self.tokenization(all_texts)
        vocab_size = len(self.tokenizer.word_index) + 1

        padded_conditions, max_length_conditions = self.preprocess_data(conditions)
        padded_datetimes, max_length_datetimes = self.preprocess_data(datetimes)

        X_train_cond, X_test_cond, X_train_dt, X_test_dt, y_train, y_test = train_test_split(
            padded_conditions, padded_datetimes, results, test_size=0.2, random_state=42
        )

        y_train = np.array(y_train, dtype=np.float32)
        y_test = np.array(y_test, dtype=np.float32)
        conditions_input_layer_list , conditions_lstm_layer = self.build_input_layer(vocab_size,max_length_conditions)
        datetimes_input_layer_list , datetimes_lstm_layer = self.build_input_layer(vocab_size,max_length_datetimes)
        input_layer_list=[conditions_input_layer_list,datetimes_input_layer_list]
        lstm_layer =[conditions_lstm_layer,datetimes_lstm_layer]
        self.model = self.build_model( input_layer_list , lstm_layer)

        # EarlyStopping コールバックを定義
        early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

        # 学習ループ
        epochs_without_improvement = 0
        while True:
            self.model.fit(
                [X_train_cond, X_train_dt], y_train,
                epochs=1, batch_size=32,
                validation_data=([X_test_cond, X_test_dt], y_test),
                callbacks=[early_stopping]
            )
            loss, accuracy = self.model.evaluate([X_test_cond, X_test_dt], y_test)
            print(f"Validation Accuracy: {accuracy}")
            if accuracy >= target_accuracy:
                break
            else:
                epochs_without_improvement += 1
                if epochs_without_improvement >= 5:  # 5エポック連続で改善されない場合、学習を中止
                    print("Validation accuracy did not improve for 5 consecutive epochs. Stopping training.")
                    break

        return self.model


    def check_condition(self, condition, datetime_str):
        padded_condition = pad_sequences(self.tokenizer.texts_to_sequences([condition]), maxlen=self.model.input_shape[0][1], padding='post')
        padded_datetime = pad_sequences(self.tokenizer.texts_to_sequences([datetime_str]), maxlen=self.model.input_shape[1][1], padding='post')
        
        prediction = self.model.predict([padded_condition, padded_datetime])
        return prediction[0][0] > 0.5
    
    def save_tokenizer(self, file_path):
        with open(file_path, 'wb') as handle:
            pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_tokenizer(self,file_path):
        with open(file_path, 'rb') as handle:
            self.tokenizer = pickle.load(handle)
            

def main():
    learning = Learning()
    choice = input("Do you want to train the model? (y/n): ")
    data_file_path = "./Sources/Models/train_data.json"
    trained_model_path = 'trained_model'
    tokenizer_path = 'ytokenizer.pkl'
    
    if choice == 'y':
        with open(data_file_path, 'r', encoding='utf-8') as f:
            train_data = json.load(f)
        # 学習を実行
        trained_model = learning.train(train_data, target_accuracy=0.9)  # 目標の正解率を指定してください
        trained_model.save(trained_model_path)
        learning.save_tokenizer(tokenizer_path)
    
    loaded_model = tf.keras.models.load_model(trained_model_path)
    learning.model = loaded_model
    learning.load_tokenizer(tokenizer_path)

    # テストデータで予測を行う
    test_conditions = [
        ("2024/5/25～2024/5/26", "2024/5/25", True),
        ("金曜日～日曜日", "2024/5/25", True),
        ("5:20～17:20", "2024/5/24 10:00", True),
        ("月曜日～水曜日", "2024/5/23", True),
        ("9:13～11:21", "2024/5/24 13:00", False),
        ("10:00～12:00", "13:00", False),
        ("2024/5/25 10:00～12:00", "11:00", True),  # 追加のテストデータ
        ("2024/4/25 10:13～10:20", "10:17", True),  # 追加のテストデータ
    ]

    for condition, datetime_str, expected in test_conditions:
        result = learning.check_condition(condition, datetime_str)
        print(f"Condition: {condition}, Datetime: {datetime_str}, Expected: {expected}, Result: {result}, Test Passed: {result == expected}")

if __name__ == '__main__':
    main()