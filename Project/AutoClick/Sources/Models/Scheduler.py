## $python task scheduler ##
import sys
sys.path.append("./Common")
sys.path.append("../Common")
import auto
import json_control
import threading
import Task



file_path_setting="scheduler.json"

TaskThreads={}
class Schedule:
    Name : str
    Plans : list

    def AddPlan(plan):
        Plans.append(plan)

    def Execute():       
        for plan in Plans():
            print("plan.name")


def init():
    settings = {"Plans":{},"Actions":{}}
    settings = json_control.ReadDictionary(file_path_setting,settings)
    plans=settings["plans"]
    



    

        
def ExecuteSchedule(name,file_path=""):
    print("ExecuteTask"+ name)
    task_threads={}
    for plan in plans:
        print(plan.name)

def main():
    init()
    ExecuteSchedule(name,file_path="../../")


if __name__ == "__main__":
    sys.exit(main())
