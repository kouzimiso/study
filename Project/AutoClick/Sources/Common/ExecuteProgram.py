import subprocess
import os
import sys
sys.path.append("./Common")
sys.path.append("../Common")
sys.path.append("../../Common")
import LogMessage
import json

def ExecuteProgram(setting_dictionary):
    program_path = setting_dictionary.get("program_path","")
    if not os.path.exists(program_path):
        error_dictionary = LogMessage.Get_Error_Dictionary(False , error_type = "FileNotExistError" , error_message = "The file is not exist")
        json_dictionary = error_dictionary
        return json_dictionary
    loop01 = 1
    args_list = []
    if not "argument" + str(loop01) in setting_dictionary:
        args_list.append(json.dumps(setting_dictionary)) 
    else:       
        while "argument" + str(loop01) in setting_dictionary:
            args_list.append(setting_dictionary.get(setting_dictionary.get("argument" + str(loop01) ,"") ,""))
            loop01 = loop01 + 1
    # プログラムを起動
    result = subprocess.run([program_path] + args_list , capture_output = True , text = True)
    output = result.stdout #.decode('utf-8')
    try:
        json_dictionary = json.loads(output)
    except json.JSONDecodeError:
        json_dictionary = {"result" : output }

    return json_dictionary

