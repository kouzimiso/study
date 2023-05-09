import subprocess
import os
import sys
sys.path.append("./Common")
sys.path.append("../Common")
sys.path.append("../../Common")
import LogMessage
import json



def test():
    #subprocess.run(["notepad"])
    #result = subprocess.run(["ls","-l"], capture_output=True, text=True,stderr=subprocess.PIPE)
    #result = subprocess.run(["ls","-l"], capture_output=True, text=True)
    #print(result.stdout)
 
    result = subprocess.run(["cmd" , "/c" , "dir"] , capture_output = True , text = True)
    print(result.stdout)

    result = subprocess.run(["cmd", "/c", "echo Hello, world!"] , capture_output = True , text = True)
    print(result.stdout)

    # PowerShellを起動する場合
    result = subprocess.run(["powershell" , "-Command" , "Write-Host 'Hello, world!'"] , capture_output = True , text = True)
    print(result.stdout)


def ExecuteProgram(setting_dictionary):
    program_path = setting_dictionary.get("program_path","")
    if not os.path.exists(program_path):
        error_dictionary = LogMessage.Get_Error_Dictionary(False , error_type = "FileNotExistError" , error_message = "The file is not exist")
        json_dictionary = json.dumps(error_dictionary)
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

    
if __name__ == "__main__":
    test()
    setting_dictionary = {"argument1" : "name" , "argument2" : "address" , "argument3" : "tell",
                 "name" : "sato" , "address" : "taiwan" , "tell" : "090-1234-5678",
                 "program_path" : r"./jsonprint.exe"}             
    #             "program_path" : r"C:/Users/kouzi/Dropbox/Works_Shibaura/Nowworks/Auto/AutoClick/Sources/Test/jsonprint.exe"}

    result = ExecuteProgram(setting_dictionary)
    print(result)

    setting_dictionary = {"name" : "sato" , "address" : "taiwan" , "tell" : "090-1234-5678",
                 "program_path" : r"./jsonprint.exe"}             
    #             "program_path" : r"C:/Users/kouzi/Dropbox/Works_Shibaura/Nowworks/Auto/AutoClick/Sources/Test/jsonprint.exe"}

    result = ExecuteProgram(setting_dictionary)
    print(result)
