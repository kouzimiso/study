import subprocess

external_program_path = '/path/to/external/program'

def run_external_program(external_program_path,args={}):
    # 外部プログラムのパスを指定
    # 引数を文字列に変換
    args_str = ' '.join([str(arg) for arg in args])
    # 外部プログラムを起動し、標準出力を取得
    result = subprocess.run([external_program_path, args_str], stdout=subprocess.PIPE)
    # 標準出力を辞書に変換して返す
    return eval(result.stdout.decode())

# 外部プログラムに渡す引数を設定
args = {'key1': 'value1', 'key2': 'value2'}

# 外部プログラムを実行し、戻り値を受け取る
result_dict = run_external_program(external_program_path,args)

# 受け取った辞書を使って処理を続ける
for key, value in result_dict.items():
    print(key, value)
