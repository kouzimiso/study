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
import json_control

class Task(threading.Thread):
    status : auto.RUN_STATUS 
    name : str = ""
    result_name : str = ""
    information : dict = {}
    condition : dict = None
    plan_lists : dict = None

    #子task情報
    task_name : str = ""
    task_type : str = ""
    task_setting : str = ""
    task_condition : str = ""
    task_status : str = ""

    

    #Task動作Mode(Check/AutoNext)
    step_check_mode : bool = False

    #Log情報
    log_file_path_list : list = None
    log_print_standard_output : bool = False
    message_lists = {}


    def __init__(self,file_path="",plan_lists = None,setting = {}):
        self.status = auto.RUN_STATUS.INITIAL
        #Logの初期設定が無い事についての仮の処理
        self.logger=log.Logs(setting)

        if file_path is None:
            self.plan_lists = plan_lists
        else:
            self.plan_lists = json_control.ReadDictionary(file_path)
            self.TaskStatusChange("Read PlanLists:" + file_path)

    def Run(self, name ,condition = None,plan_lists=None , information = None):
        self.name = name
        #Arguments check
        if plan_lists == None:
            plan_lists = self.plan_lists
        if information == None:
            information = self.information
        if name in plan_lists:
            self.TaskStatusChange("Start Check")
            judge = Judge.Judge()
            flag_judge = judge.Result(condition , information)
            self.TaskStatusChange("Judge" , str(flag_judge))
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
        self.task_name = plan_list_name
        type_data = type(plan_lists)
        #plan_list = plan_lists.get(plan_list_name)
        try:
            plan_list = plan_lists[plan_list_name]
            self.TaskStatusChange("Plan Read",plan_list_name)
        except:
            plan_list = None
            self.TaskStatusChange("No Plan")

        if plan_list is not None:
            for plan in plan_list:
                self.TaskRead(plan)
                self.TaskStatusChange("Plan RunCheck ")
                judge = Judge.Judge()
                flag_judge = judge.Result(self.task_condition,self.information)
                self.TaskStatusChange("Gudge" , str(flag_judge))
                #step毎に次へ進むか確認するmodeの設定を読みだす
                self.step_check_mode = self.task_setting.get("step_check_mode")
                if self.step_check_mode:
                    input_text = Task.WaitInput(self.task_name + " Condition Judge:" + str(flag_judge) +"\nRun Task? n(no)/other(yes)")
                    if input_text == "n" or input_text == "no":
                        flag_judge = False
                
                if flag_judge:
                    if self.task_type == "RunPlanLists":
                        plan_list_names_new = self.task_setting["plan_lists"]
                        #PlanListsをFilePathから読み込み、RunPlanListsで指定した名前のPlanを実行する。
                        plan_list_filepath = self.task_setting.get("file_path")
                        if plan_list_filepath is None:
                            self.TaskStatusChange("Run PlanLists")
                            self.RunPlanLists(plan_list_names_new,plan_lists)
                        else:
                            read_plan_lists = json_control.ReadDictionary(plan_list_filepath)
                            self.TaskStatusChange("Run PlanLists" , plan_list_filepath)
                            self.RunPlanLists(plan_list_names_new,read_plan_lists)                       
                    else:
                        action = Action.Action()
                        self.TaskStatusChange("Run PlanList", plan_list_name)
                        self.information[self.result_name] = action.Execute(self.task_type , self.task_setting) 
                        
        self.TaskStatusChange("End")

    ####専用命令####
    def TaskStatusChange(self , status , detail = ""):
        self.task_status=status
        message ={}
        message["task"]= self.name + "." +self.task_name
        message["type"]=self.task_type
        message["status"]=self.task_status
        if detail != "":
            message[detail] = detail

        self.logger.log(message)
        if status =="End":
            self.task_name = ""
            self.task_type = ""
            self.task_setting = ""
            self.task_condition = ""

    def TaskRead(self,plan):
        name = plan.get("name")
        if name is None:
            name = ""
        self.task_name=name
        self.result_name = plan.get("result_name","Result_"+self.task_name)
        self.task_type = plan.get("type","")
        self.task_setting = plan.get("settings",{})
        self.task_condition = plan.get("condition_list",[])
        self.logger=log.Logs(self.task_setting)

    def WaitInput(text):
        input_text = input(text)
        return input_text


