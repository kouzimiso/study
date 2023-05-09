import enum
import sys
import threading
import datetime
import time
sys.path.append("../Common")
sys.path.append("../../Common")
import Action
import Auto
import Judge
import Log
import JSON_Control
import UserInterface


class Task(threading.Thread):
    status : Auto.RUN_STATUS 
    name : str = ""
    result_name : str = ""
    information : dict = {}
    condition : dict = None
    plan_lists : dict = None
    settings:dict = {}

    execute_start_time: datetime = datetime.datetime.now()
    execute_end_time: datetime = datetime.datetime.now()

    #子task情報
    task_name : str = ""
    task_path : list =[]
    task_type : str = ""
    task_settings : str = ""
    task_condition : str = ""
    task_status : str = ""



    #Task動作Mode(Check/AutoNext)
    step_check_mode : bool = False

    #Log情報
    log_file_path_list : list = None
    log_print_standard_output : bool = False
    message_lists = {}

    def __init__(self,file_path="",plan_lists = None,setting = {}):
        self.status = Auto.RUN_STATUS.INITIAL
        #Logの初期設定が無い事についての仮の処理
        self.logger=Log.Logs(setting)

        if file_path is None:
            self.plan_lists = plan_lists
        else:
            self.plan_lists = JSON_Control.ReadDictionary(file_path)
            self.TaskStatusChange("Read PlanLists:" + file_path)

    def Run(self, name ,condition = None,plan_lists=None , information = None):
        if plan_lists is None:
            plan_lists=self.plan_lists
        if information is None:
            information = self.information
        self.name = name
        #Arguments check
        planlist_type = type(plan_lists)
        if planlist_type is dict:
            run_plan_lists=plan_lists
        else:
            print( planlist_type)
            run_plan_lists = {name : plan_lists}
        self.settings = plan_lists.get("settings",{})
        if name in run_plan_lists:
            self.TaskStatusChange("Start Check")
            #self.logger.Setup_logging(self.task_settings)
            judge_instance = Judge.Judge(self.settings)
            flag_judge = judge_instance.Result(condition , information)
            self.TaskStatusChange("Judge" , {"result":flag_judge})
            if flag_judge:
                self.status = Auto.RUN_STATUS.RUN
                self.RunPlanLists(name,run_plan_lists)

        return self.information

    #plan_list_names:実行するplan_listの名前
    #plan_lists:plan_listsの設定
    def RunPlanLists(self , plan_list_names ,plan_lists,details={}):
        if type(plan_list_names) is list:
            for plan_list_name in plan_list_names:
                self.RunPlanList(plan_list_name,plan_lists,details)
        else:
            plan_list_name = plan_list_names
            self.RunPlanList(plan_list_name,plan_lists,details)

 
    def RunPlanList(self , plan_list_name ,plan_lists,details={}):
        self.task_name = plan_list_name
        #plan_list = plan_lists.get(plan_list_name)
        try:
            plan_list = plan_lists[plan_list_name]
            details["plan_list_name"]=plan_list_name
            self.TaskStatusChange("Plan Read",details)
        except:
            plan_list = None
            self.TaskStatusChange("No Plan")
        if plan_list is not None:
            for plan in plan_list:
                result_taskread = self.TaskRead(plan)
                if result_taskread:
                    judge_instance = Judge.Judge(self.task_settings,self.information)
                    judge_details={}
                    flag_judge = judge_instance.Result(self.task_condition , result_details = judge_details)
                    self.TaskStatusChange("Judge" , details = judge_details )
                    #step毎に次へ進むか確認するmodeの設定を読みだす
                    self.step_check_mode = self.task_settings.get("step_check_mode")
                    if self.step_check_mode:
                        details_stepcheck={}
                        if self.task_type == "RunPlanLists":
                            details_stepcheck = {"plan_lists": self.task_settings.get("plan_lists","No plan_lists")}
                        step_check_comment = self.task_settings.get("step_check_comment","")                   
                        if step_check_comment != "":
                            print (step_check_comment)
                        flag_judge = self.StepCheck(flag_judge,details_stepcheck)
                    if flag_judge:
                        retry = True
                        while retry:
                            result = self.ExecutePlanList(plan_list_name ,plan_lists,details)
                            retry_check = self.task_settings.get("retry_check",False)
                            if retry_check == True and result == False:
                                input_text = self.RetryCheck("□Retry Task? y(yes)/other(no)")
                                if input_text == "y":   
                                    retry = True
                                else:
                                    retry = False
                            else:
                                retry = False                        
                sleep_time = self.task_settings.get("sleep_time",0)
                time.sleep(sleep_time)
        self.TaskStatusChange("End",details)

    ####専用命令 Step####
    def Get_SettingData(self , data_name , default_data="",option_errorinput= False):
        data = self.task_settings.get(data_name)
        value = default_data
        if data == None:
            if option_errorinput:
                setting={
                    "label" : "Please Input Data.",
                    "data_name" : data_name,
                    "default_data" :default_data
                }
                editor = UserInterface.ValueEditor()
                value = editor.input_data(setting)
        return value

    def StepCheck(self,flag_judge , details = {}):
        input_text = self.WaitInput("□Run Task("+ self.task_name +")? n(no)/other(yes)",details)
        if input_text == "n" or input_text == "no":
            flag_judge = False
        return flag_judge
        
    def ExecutePlanList(self , plan_list_name ,plan_lists,details={}):
        result_details = {}
        self.execute_start_time = datetime.datetime.now()
        if self.task_type == "RunPlanLists":
            plan_list_names_new = self.task_settings["plan_lists"]
            #PlanListsをFilePathから読み込み、RunPlanListsで指定した名前のPlanを実行する。
            plan_list_filepath = self.task_settings.get("file_path","")
            if plan_list_filepath == "" :
                self.TaskStatusChange("Run PlanLists",details)
                self.RunPlanLists(plan_list_names_new,plan_lists)
            else:
                read_plan_lists = JSON_Control.ReadDictionary(plan_list_filepath,details=details)
                details["file_path"] = plan_list_filepath
                if details.get("result") == False:
                    self.logger.error("" , details)
                    input("please push and skip")
                self.TaskStatusChange("Run PlanLists file" , details)
                self.RunPlanLists(plan_list_names_new,read_plan_lists)  
                result_details = {"file_path" : plan_list_filepath}
        # task levelの情報にAccessできるJudge
        elif self.task_type == "Judge":
            judge_instance = Judge.Judge(self.task_settings,self.information)
            condition_list = self.task_settings.get("condition_list",[])
            flag_judge = judge_instance.Result(condition_list = condition_list , information = self.information)
            self.information[self.result_name] = {"result" : flag_judge}
            result_details = {"result" : flag_judge,"condition_list":condition_list}
        # task levelの情報にAccessできるLog    
        elif self.task_type == "Log":
            message = self.task_settings.get("message")
            level = self.task_settings.get("level")
            self.logger.log(message,level)
            result_details = {"result" : True}
        elif self.task_type == "PrintInformation":
            print(self.information)
            
        else:
            setting = self.task_settings
            task_type = self.task_type
            action = Action.Action(setting)
            details["plan_list_name"] = plan_list_name
            self.TaskStatusChange("Run PlanList", details)
            result_details = action.Execute(task_type , setting) 
            self.information[self.result_name] = result_details
        interval_time = self.execute_start_time - self.execute_end_time 
        self.execute_end_time = datetime.datetime.now()
        execution_time = self.execute_end_time - self.execute_start_time 

        task_details = {"type": self.task_type,"result_name":self.result_name}
        task_details.update(result_details)
        task_details.update(details)
        task_details["interval_time"] = str(interval_time)
        task_details["execution_time"] = str(execution_time)
        self.TaskStatusChange("Task end" , task_details)
        return task_details.get("result",False)

    ####専用命令####
    def TaskStatusChange(self , status ,  details = {}):
        self.task_status=status
        detail_dictionary ={}
        task_list = details.get("task_list",   [ self.name ,self.task_name])
        if task_list[-1] != self.task_name:
            task_list.append(self.task_name)
            details = task_list
        detail_dictionary["task"]= ".".join(task_list)
        detail_dictionary["type"]=self.task_type
        detail_dictionary["status"]=self.task_status
        if type(details) is not dict:
            detail_dictionary["detail"] = details
        else:
            detail_dictionary.update(details)

        self.logger.log("TaskStatusChange","INFO",details=detail_dictionary)
        if status =="End":
            self.task_name = ""
            self.task_type = ""
            self.task_settings = {}
            self.task_condition = []

    def TaskRead(self,plan):
        if type(plan) is not dict:
            self.logger.log("The Plan that was read is not in the Dictionary format. ","ERROR",details=details)
            return False
        name = plan.get("name")
        if name is None:
            name = ""
        self.task_name=name
        self.result_name = plan.get("result_name","")
        if(self.result_name == ""):
            self.result_name = "Result_"+self.task_name
        self.task_type = plan.get("type","")
        self.task_settings = plan.get("settings",{})
        self.task_condition = plan.get("condition_list",[])
        self.logger=Log.Logs(self.task_settings)
        details = plan
        self.logger.log("Task Read","DEBUG",details=details)
        return True


    def WaitInput(self,text,details = {}):
        if type(details) is dict:
            if details == {}:
                details_text = ""
            else:
                details_text = JSON_Control.ToString(details)
        elif type(details) is list:
            details_text=",".join(details)
        else:
            details_text =details

        if details_text == "":
            input_text = input(text)
        else:
            input_text = input(details_text +"\n"+ text)
        return input_text
    def RetryCheck(self,text):
        input_text = input(text)
        return input_text


