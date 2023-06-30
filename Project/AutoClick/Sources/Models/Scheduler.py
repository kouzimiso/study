## $python task scheduler ##
import sys
sys.path.append("./Common")
sys.path.append("../Common")
import JSON_Control
import threading
import Task



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
        
def main():
    #init()
    StartUp("Start","../Setting/RunGame.json")

if __name__ == "__main__":
    sys.exit(main())
