import enum
import sys
import threading
sys.path.append("../Common")
sys.path.append("../../Common")
import Plan
import Action
import Judge
import log
import auto
          

class Task(threading.Thread):
    status: auto.RUN_STATUS 
    information: dict = {}
    condition: dict = None
    plan_lists: dict = None
    task_name: str = ""
    task_type: str = ""
    task_setting: str = ""
    task_condition: str = ""
    task_status: str = ""

    def __init__(self,plan_lists=None):
        self.plan_lists=plan_lists
        self.status = auto.RUN_STATUS.INITIAL

    def Run(self, name ,condition = None,plan_lists=None):
        if plan_lists == None:
            plan_lists=self.plan_lists
        if name in plan_lists:
            judge = Judge.Judge()
            flag_judge = judge.Result(condition)
            if flag_judge:
                self.status = auto.RUN_STATUS.RUN
                self.RunPlanLists(name,plan_lists)

    def RunPlanLists(self , plan_list_names ,plan_lists):
        if type(plan_list_names) is list:
            for plan_list_name in plan_list_names:
                self.RunPlanList(plan_list_name,plan_lists)
        else:
            plan_list_name = plan_list_names
            self.RunPlanList(plan_list_name,plan_lists)

 
    def RunPlanList(self , plan_list_name ,plan_lists):
        type_data = type(plan_lists)
        #plan_list = plan_lists.get(plan_list_name)
        try:
            plan_list = plan_lists[plan_list_name]
            self.TaskStatusChange("Plan check")
        except:
            plan_list = None
            self.TaskStatusChange("No Plan")

        if plan_list is not None:
            for plan in plan_list:
                self.TaskRead(plan)
                self.TaskStatusChange("Run judge")
                judge = Judge.Judge()
                flag_judge = judge.Result(self.task_condition,self.information)
                if flag_judge:
                    if self.task_type=="RunPlanLists":
                        self.TaskStatusChange("Call")
                        plan_list_names_new=self.task_setting["RunPlanLists"]
                        self.RunPlanLists(plan_list_names_new,plan_lists)
                    else:
                        self.task_status="Run"
                        action = Action.Action()
                        result_name = "Result."+self.task_name
                        self.information[result_name] = action.Execute(self.task_type , self.task_setting) 
                         

        self.TaskStatusChange("End")
    ####専用命令####
    def TaskStatusChange(self,status):
        self.task_status=status
        print("Task:" + self.task_name +" status:" + self.task_status + " type:" + self.task_type )
        if status =="End":
            self.task_name = ""
            self.task_type = ""
            self.task_setting = ""
            self.task_condition = ""
    
    def TaskRead(self,plan):
        name = plan.get("name")
        if name is None:
            name=""
        self.task_name=name
        self.task_type = plan.get("type")
        self.task_setting = plan["setting"]
        self.task_condition = plan.get("condition")

