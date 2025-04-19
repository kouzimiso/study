import inspect
import subprocess
import threading
import os
import ast

def get_function_signature(func, args, kwargs):
    """関数の引数情報を文字列で取得する"""
    signature = inspect.signature(func)
    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()
    arg_str = ", ".join(f"{name}={value}" for name, value in bound_args.arguments.items())
    return f"{func.__name__}({arg_str})"

def run_external_program(command, args, kwargs, use_thread=False, use_subprocess=False):
    """外部プログラムを起動する"""
    if use_subprocess:
        subprocess.run([command, *map(str, args), *[f"{k}={v}" for k, v in kwargs.items()]])
    elif use_thread:
        thread = threading.Thread(target=lambda: subprocess.run([command, *map(str, args), *[f"{k}={v}" for k, v in kwargs.items()]]))
        thread.start()
        thread.join()
    else:
        # ライブラリまたはPythonソースファイルの関数を直接呼び出す場合
        command(*args, **kwargs)

def parse_function_definition(func):
    """関数の定義を解析して関数名と引数情報を取得する"""
    source = inspect.getsource(func)
    tree = ast.parse(source)
    func_def = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    arg_names = [arg.arg for arg in func_def.args.args]
    return func_def.name, arg_names

def run_with_startup_info(command, args, kwargs, use_thread=False, use_subprocess=False):
    """起動情報を表示して外部プログラムを起動する"""
    signature_str = get_function_signature(command, args, kwargs)
    func_name, arg_names = parse_function_definition(command)
    print(f"Function Name: {func_name}")
    print("Arguments:")
    for arg_name in arg_names:
        value = kwargs.get(arg_name) if arg_name in kwargs else args[arg_names.index(arg_name)] if arg_names.index(arg_name) < len(args) else None
        print(f"  {arg_name}: {value}")
    print(f"起動情報: {signature_str}")
    run_external_program(command, args, kwargs, use_thread, use_subprocess)

# 実行例
def my_function(x, y=2):
    print(f"my_function: x={x}, y={y}")

run_with_startup_info(my_function, (1,), {"y": 3})

# サブプロセスで外部プログラムを起動する場合
run_with_startup_info(subprocess.run, (["notepad"],), {}, use_subprocess=True)

# スレッドで外部プログラムを起動する場合
run_with_startup_info(subprocess.run, (["notepad"],), {}, use_thread=True)