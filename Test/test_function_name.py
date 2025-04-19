import inspect
from typing import List, Any
def get_argument_names(func: Any, arg_values: List[Any]) -> str:
    """
    定義された引数名 (arg_names) と実行時に与えられた引数値 (arg_values) のリストから、
    "name1=value1, name2=value2, ..." という形式の文字列を生成する関数。

    - arg_values のほうが長い場合は、余分な値に対して "argN" (Nはインデックス+1) を割り当てる。
    - arg_names のほうが長い場合は、対応する値がない引数は名前のみ表示する。

    Parameters:
        arg_names (list): 関数定義から取得した引数名のリスト
        arg_values (list): 実行時に渡される引数値のリスト

    Returns:
        str: "name1=value1, name2=value2, ..." という形式の文字列
    """
    result = []
    sig = inspect.signature(func)
    arg_names = list(sig.parameters.keys())
    n_defined = len(arg_names)
    n_values = len(arg_values)
    
    # 定義された引数名と提供された値がある部分
    for i in range(min(n_defined, n_values)):
        result.append(f"{arg_names[i]}={arg_values[i]}")
    
    # 引数値のほうが長い場合：余分な値に対して "argN" を割り当てる
    if n_values > n_defined:
        for i in range(n_defined, n_values):
            result.append(f"arg{i+1}={arg_values[i]}")
    
    # 定義された引数名のほうが長い場合：対応する値がない引数は名前だけ表示
    if n_defined > n_values:
        for i in range(n_values, n_defined):
            result.append(arg_names[i])
    
    return ", ".join(result)

def sample_function1(arg1, arg2):
    return arg1 + arg2
def sample_function2(arg1, arg2,arg3):
    return arg1 + arg2 + arg3
    
def sample_function3(arg1, arg2,arg3,arg4):
    return arg1 + arg2 + arg3 + arg4
def sample_function4():
    return 1

# --- テスト用の関数 ---
def test_get_argument_names():
    test_cases = [
        # 同じ数の場合
        (sample_function1, [1, 2]),
        # 引数値が多い場合
        (sample_function1, [1, 2, 3, 4]),
        # 定義された引数が多い場合
        (sample_function3, [10, 20]),
        # 両方空の場合
        (sample_function4, []),
        # 定義は空で値だけある場合
        (sample_function4, [100, 200])
    ]
    for func, arg_values in test_cases:
        formatted = get_argument_names(func, arg_values)
        print(f"{func.__name__}({formatted})")

if __name__ == "__main__":
    # 一般的なテスト関数の例
    test_get_argument_names()
