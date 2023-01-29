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

def StartUp(plan_list_name,file_path):
    task = Task.Task(file_path)
    task.Run(plan_list_name)
        

def main():
    #init()
    StartUp("Start","RunGame.txt")


if __name__ == "__main__":
    sys.exit(main())
