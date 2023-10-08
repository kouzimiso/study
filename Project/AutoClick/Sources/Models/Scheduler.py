## $python task scheduler ##
import sys
sys.path.append("./Common")
sys.path.append("../Common")
import JSON_Control
import threading
import Task
import FunctionUtility



file_path_setting="Scheduler.json"
TaskThreads={}

class Schedule:
    Name : str
    Plans : list

    def AddPlan(self , plan):
        self.Plans.append(plan)

    def Execute(self):       
        for plan in self.Plans:
            print("plan.name")


def init():
    settings = {"Plans":{},"Actions":{}}
    settings = JSON_Control.ReadDictionary(file_path_setting,settings)
    plans=settings["plans"]

def StartUp(plan_list_name,file_path):
    task = Task.Task(file_path)
    task.Run(plan_list_name)
    return True
        
# Defaultの辞書Dataを設定
default_dictionary = {
    "plan_list_name": "Start",
    "file_path" : "../Setting/RunTest.json"
}
# 辞書設定の読込と機能実行
def Execute(settings_dictionary):
    #設定の読込
    plan_list_name = settings_dictionary.get("plan_list_name","")
    file_path = settings_dictionary.get("file_path","")
    #機能実行 
    result_dictionary = {}
    if(file_path != ""):
        result = StartUp(plan_list_name,file_path)
    else:
        result = False
    result_dictionary["result"] = result
    return result_dictionary

#command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    settings_dictionary = FunctionUtility.ArgumentGet(default_dictionary)
    result_dictionary = Execute(settings_dictionary)
    FunctionUtility.Result(result_dictionary)

if __name__ == '__main__':
    main()

