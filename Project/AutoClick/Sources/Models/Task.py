import enum
import os
import sys
import threading
import datetime
import time
import copy
sys.path.append("./Common")
sys.path.append("../Common")
sys.path.append("../../Common")
import Action
import Auto
import Judge
import Data
import Log
import JSON_Control
import FunctionUtility
import Dictionary

class Task(threading.Thread):
    name : str = ""
    default_settings :dict = {
        "file_path" : "../Setting/RunTest.json",
        "plan_list_name" : "Start",
        "plan_lists" : None,
        "settings" : {}
    }

    def __init__(self,file_path = "",plan_lists = None,settings = {}):
        context = {
            "plan_lists" : plan_lists,
            "settings" : settings
        }
        self.Set_ByContext(context)
        if file_path == "":
            self.plan_lists = plan_lists
            self.plan_lists_file_path = ""
        else:
            self.plan_lists = JSON_Control.ReadDictionary(file_path)
            self.plan_lists_file_path = file_path
            self.TaskStatusChange("Read_PlanLists:" + file_path)

            
    def Set_BySettingsDictionary(self,settings_dictionary):
        self.settings = {**self.default_settings, **settings_dictionary}       
        self.logger = Log.Logs(settings_dictionary)
        self.logger.log("Set_BySettingsDictionary")
        #設定の読込
        file_path = self.settings.get("file_path","")
        self.logger.log("file_path:" + file_path)
        #機能実行 
        result_dictionary = {}

        if (file_path != ""):
            self.plan_lists = JSON_Control.ReadDictionary(file_path)
            self.plan_lists_file_path = file_path
            self.TaskStatusChange("Read_PlanLists:" + file_path)
            self.logger.log("Read_PlanLists:" + file_path)
 
        result_dictionary["result"] = True
        return result_dictionary

    def ArgumentGet(self):
        settings_dictionary = FunctionUtility.ArgumentGet(self.default_settings,self.settings)
        self.settings = {**self.settings, **settings_dictionary}
        self.Set_BySettingsDictionary(self.settings)

    def Execute(self):
        plan_list_name = self.settings.get("plan_list_name","")
        self.Run(plan_list_name)

    def Run(self, plan_list_name ,condition = None,plan_lists = None , information = None):
        if plan_lists is None:
            plan_lists = self.plan_lists
        if information is None:
            information = self.information
        self.name = plan_list_name
        #Arguments check
        plan_lists_type = type(plan_lists)
        if plan_lists_type is dict:
            run_plan_lists = plan_lists
        else:
            print(plan_lists_type)
            run_plan_lists = {plan_list_name : plan_lists}
        self.settings = plan_lists.get("settings",{})
        if plan_list_name not in run_plan_lists:
            print("NG PlanList:"+plan_list_name)
            plan_list_name = self.SelectKey(run_plan_lists)
            run_plan_lists["plan_list_name"] = plan_list_name
        if plan_list_name in run_plan_lists:    
            self.TaskStatusChange("Start_Check")
            #self.logger.Setup_logging(self.task_settings)
            judge_instance = Judge.Judge(self.settings)
            flag_judge = judge_instance.Result(condition , information)
            self.TaskStatusChange("Judge" , {"result":flag_judge})
            if flag_judge:
                self.status = Auto.RUN_STATUS.RUN
                self.RunPlanLists(plan_list_name,run_plan_lists)
        return self.information
    
    def ExecuteByContextFile(self,context_file_path):
        context = JSON_Control.ReadDictionary(context_file_path,{},details = {})
        self.ExecuteByContext(context)

    def ExecuteByContext(self,context):
        self.Set_ByContext(self,context)
        self.Execute()

    def Write_ContextFile(self,context_file_path):
        context = self.Get_ByContext()
        JSON_Control.WriteDictionary(context_file_path,context,details = {})

    #動作再生のためのコンテキストを取得します。
    #本関数は目的を達している限り作法は考慮しない。
    def Get_ByContext(self):
        context = {}
        context["settings"] = self.settings
        context["plan_lists"] = self.plan_lists

        context["status"] = self.status
        context["name"] = self.name
        context["result_name"] = self.result_name
        context["information"] = self.information
        context["condition"] = self.condition
        context["plan_lists"] = self.plan_lists
        context["plan_lists_no"] = self.plan_lists_no
        context["settings"] = self.settings

        context["execute_start_time"] = self.execute_start_time
        context["execute_end_time"] = self.execute_end_time

        #子task情報
        context["plan_list_name"] = self.plan_list_name
        context["task_name"] = self.task_name
        context["task_path"] = self.task_path
        context["task_type"] = self.task_type
        context["task_settings"] = self.task_settings
        context["task_condition"] = self.task_condition
        context["task_status"] = self.task_status

        #Task動作Mode(Check/AutoNext)
        context["step_check_mode"] = self.step_check_mode

        #設定変更初期化
        context["change_settings_by_name"] = self.change_settings_by_name
        context["change_settings"] = self.change_settings
        context["filter_change_settings"] = self.filter_change_settings
        return context


    def Set_ByContext(self,context = {}):
        self.plan_lists = context.get("plan_lists",{})
        self.plan_lists_no = context.get("plan_lists_no",0)

        self.status = context.get("status",Auto.RUN_STATUS.INITIAL)
        self.name = context.get("name","task")
        self.result_name = context.get("result_name","")
        self.information  = context.get("information",{})
        self.condition  = context.get("condition",None)
        self.plan_lists  = context.get("plan_lists",None)
        self.settings = context.get("settings",{})

        self.execute_start_time: datetime = datetime.datetime.now()
        self.execute_end_time: datetime = datetime.datetime.now()

        #子task情報
        self.plan_list_name = context.get("plan_list_name","")
        self.task_name = context.get("task_name","")
        self.task_path = context.get("task_path",[])
        self.task_type = context.get("task_type","")
        self.task_settings = context.get("task_settings","")
        self.task_condition = context.get("task_condition","")
        self.task_status = context.get("task_status","")

        #Task動作Mode(Check/AutoNext)
        self.step_check_mode = context.get("step_check_mode",False)

        #Log設定
        self.logger = Log.Logs(self.settings)

        #設定変更初期化
        self.change_settings_by_name = context.get("change_settings_by_name",{})
        self.change_settings = context.get("change_settings_by_name",{})
        self.filter_change_settings = context.get("change_settings_by_name",[])

    def CopyPlanListsBySettings(self, settings, plan_lists, result_details):
        copy_plan_lists = settings.get("copy_plan_lists","")        
        if copy_plan_lists == "" :
            details = {"error":"CopyPlanListsBySettings copy_plan_lists is none."}
            return details
            

        #PlanListを読込む。
        plan_list_filepath = settings.get("file_path","")

        details = {}
        plan_lists_source = {}
        new_plan_lists = {}
        new_plan_list =[]
        if plan_list_filepath == "" :
            plan_lists_source = plan_lists
        else:
            #PlanListsをFilePathから読み込み、CopyPlanListsで指定した名前のPlanをCopyする。
            plan_lists_source = JSON_Control.ReadDictionary(plan_list_filepath,{},details = details)
            details["file_path"] = plan_list_filepath
        # copy_plan_lists copyの設定を読み込む
        if type(copy_plan_lists) is not list:
            copy_plan_lists = [copy_plan_lists]
        for copy_plan_list_setting in copy_plan_lists:
            source_plan_list_name = copy_plan_list_setting.get("source_plan_list_name","")
            copy_plan_list_name = copy_plan_list_setting.get("copy_plan_list_name","")
            change_plan_names = copy_plan_list_setting.get("change_plan_names","")
            if change_plan_names != "":
                new_plan_list = self.ChangePlanListNames( plan_lists_source ,source_plan_list_name, change_plan_names)
            else:
                new_plan_list =copy.deepcopy(plan_lists_source.get(source_plan_list_name,[]))
            if new_plan_list != []:
                #Copyするplan_listの設定を変更する。
                change_settings_by_name = copy_plan_list_setting.get("change_settings_by_name",{})
                if change_settings_by_name != {}:
                    if type(new_plan_list) is not list:
                        new_plan_list = [new_plan_list]
                    for new_plan in new_plan_list :
                        if type (new_plan) is dict :
                            name = new_plan.get("name","")
                            if type (change_settings_by_name) is dict :
                                change_settings = change_settings_by_name.get(name,{})
                                if change_settings != {}:
                                    new_plan["settings"].update(change_settings)
            if copy_plan_list_name != "":
                #Copy名前を変えて保存する。
                if plan_list_filepath !="":
                    new_plan_lists["plan_file_path"] = plan_list_filepath
                new_plan_lists[copy_plan_list_name] = copy.deepcopy(new_plan_list) 
        details["plan_lists"] = new_plan_lists
        return details 
    

    def ChangePlanListNames(self,  source_plan_lists ,source_plan_list_name,change_plan_names):
        source_plan_list = source_plan_lists.get(source_plan_list_name,[])
        new_plan_list = copy.deepcopy(source_plan_list)  
        # planのname情報の書き換え
        if type(new_plan_list) is not list:
            new_plan_list = [new_plan_list]
        for new_plan in new_plan_list:
            if type(new_plan) is dict:
                if "name" in new_plan:
                    name = new_plan.get("name","")
                    change_name = change_plan_names.get(name,"")
                    if change_name != "" :
                        new_plan["name"] = change_name
        return new_plan_list
    
    def RunPlanListsBySettings(self , settings ,plan_lists,details = {}):
        #実行するPlan_listの名前listを得る。
        plan_list_names_execute = settings.get("plan_lists","")
        if plan_list_names_execute == "":
            details = {"error":""}
            return details
        #PlanListを読込む。
        plan_list_filepath = settings.get("file_path","")
        if plan_list_filepath == "" :
            #RunPlanListsで指定した名前のPlanを実行する。
            self.TaskStatusChange("Run_PlanLists",details)
            plan_lists_execute = plan_lists
            self.read_plan_lists_file_path = ""

        else:
            #PlanListsをFilePathから読み込み、RunPlanListsで指定した名前のPlanを実行する。
            plan_lists_execute = JSON_Control.ReadDictionary(plan_list_filepath,{},details = details)
            self.read_plan_lists_file_path = plan_list_filepath
            details["file_path"] = plan_list_filepath
            if details.get("result") == False:
                self.logger.error("" , details)
                input("file error.please push and skip."+os.path.abspath(plan_list_filepath))
            self.TaskStatusChange("Run_PlanLists_file" , details)

        #Loop処理
        loop_condition = settings.get("loop_condition",False)
        loop_limit_count = settings.get("loop_limit_count",0)
        terminate_condition = settings.get("terminate_condition",False)
        flag_loop = True
        count = 0
        judge_details = {}
        while flag_loop:
            flag_loop = False
            if type(plan_list_names_execute) is list:
                for plan_list_name in plan_list_names_execute:
                    self.RunPlanList(plan_list_name,plan_lists_execute,details)
                    #中断条件が成立した場合は動作をやめて中断する。
                    flag_terminate = self.judgeLoopTerminate(terminate_condition ,settings, self.information,judge_details)
                    if flag_terminate :
                        details["message"] = plan_list_name+"terminate"+str(count)+"/"+str(loop_limit_count)
                        break
            else:
                plan_list_name = plan_list_names_execute
                self.RunPlanList(plan_list_name,plan_lists,details)
                 #中断条件が成立した場合は動作をやめて中断する。
                flag_terminate = self.judgeLoopTerminate(terminate_condition ,settings, self.information,judge_details)    
            #中断条件実行処理。
            if flag_terminate :
                #中断条件初期化
                delete_condition = settings.get("delete_condition_after_terminate","")
   
                self.information = self.deleteDictionaryKey(self.information,delete_condition)
                details["message"] = "judgeLoopTerminate Break" + plan_list_name + str(count) + "/" + str(loop_limit_count)
                break
            flag_loop = self.judgeLoop(loop_condition,settings,self.information,judge_details)
            count = count + 1
            if( loop_limit_count <= count):
                if 0 < loop_limit_count:
                    flag_loop = False
            details["message"] = plan_list_name+"judgeLoop"+str(count)+"/"+str(loop_limit_count)
        return details
    
    def deleteDictionaryKey(self,data_dictionary,delete_key_list):
        if type(delete_key_list ) == list:
            for delete_key in delete_key_list:
                if delete_key in data_dictionary:
                    del data_dictionary[delete_key]
        else:
            if delete_key_list in data_dictionary:
                del data_dictionary[delete_key_list]
        return data_dictionary


    def judgeLoopTerminate(self,terminate_condition,settings,information,judge_details):
        judge_instance = Judge.Judge(settings,information)
        flag_terminate = judge_instance.Result(terminate_condition , result_details = judge_details)
        return flag_terminate

    def judgeLoop(self,loop_condition,settings,information,judge_details):
        judge_instance = Judge.Judge(settings,information)
        flag_loop = judge_instance.Result(loop_condition , result_details = judge_details)
        return flag_loop
    
    def ChangeSettings(self , settings):
        reset = settings.get("reset_settings",False)
        if reset:
            self.change_settings = {}

        read_information = settings.get("read_information", {})
        for key,value in read_information.items():
            if isinstance(value, str) and value != "":
                information_value = self.information.get(key, "")
                if information_value == "":
                    self.change_settings[value] = information_value

        change_settings_by_name = settings.get("change_settings_by_name",{})
        self.change_settings_by_name.update(change_settings_by_name)

        change_settings = settings.get("change_settings",{})
        self.change_settings.update(change_settings)

        copy_settings = settings.get("copy_settings", {})
        for key, value in copy_settings.items():
            if isinstance(value, str) and value != "":
                self.change_settings[key] = self.change_settings.get(value, "")

        move_settings = settings.get("move_settings", {})
        for key,value in move_settings.items():
            if isinstance(value, str) and value != "":
                self.change_settings[key] = self.change_settings.get(value, "")
                del self.change_settings[value]

        filter_change_settings = settings.get("filter_change_settings", [])
        if isinstance(filter_change_settings, list):
            self.filter_change_settings = filter_change_settings

        return {"result": True, "settings" : self.change_settings , "change_settings_by_name": change_settings_by_name}

    def FilterDictionaryByKeys(self ,input_dictionary, keys):
        filtered_dictionary = {}
        for key in keys:
            if key in input_dictionary:
                filtered_dictionary[key] = input_dictionary[key]
        return filtered_dictionary

    #plan_list_names:実行するplan_listの名前
    #plan_lists:plan_listsの設定
    def RunPlanLists(self , plan_list_names ,plan_lists,details = None):
        if details == None:
            details = {}
        if type(plan_list_names) is list:
            for plan_list_name in plan_list_names:
                self.RunPlanList(plan_list_name,plan_lists,details)
        else:
            plan_list_name = plan_list_names
            self.RunPlanList(plan_list_name,plan_lists,details)

    def SelectKey(self,data_dictionary):
         while True:
            print("Please Select:")
            for key in data_dictionary.keys():
                print(key)

            choice = input("Enter the key name: ").strip()
            #selected_data = data_dictionary.get(choice)
            if choice in data_dictionary:
                return choice
            else:
                print("Invalid choice. Please try again.")

    def RunPlanList(self , plan_list_name ,plan_lists,details = None):
        if details == None:
            details = {}
        self.plan_list_name = plan_list_name
        #plan_list = plan_lists.get(plan_list_name)
        try:
            plan_list = plan_lists[plan_list_name]
        except:
            plan_list = None
            self.TaskStatusChange("No_Plan")
            self.logger.log("NG PlanList:" + plan_list_name)
            if self.task_settings.get("plan_list_name_check",False):
                plan_list_name = self.SelectKey(plan_lists)
                plan_list = plan_lists[plan_list_name]
        if plan_list =={}:
            self.logger("No Plan:" + plan_list_name)
        elif plan_list == None:
            self.logger("None PlanList:" + plan_list_name)
        else: 
            details["plan_list_name"] = plan_list_name
            self.TaskStatusChange("Plan_Read",details)
            flag_loop = True
            count = 0
            loop_limit_count = 0  
            while flag_loop == True:
                flag_loop = False 
                flag_terminate = False
                count = count + 1
                if isinstance(plan_list, list):
                    max_count = len(plan_list)  # リストの場合は要素数を取得
                elif isinstance(plan_list, dict):
                    max_count = 1  # 辞書の場合は1とする
                    plan_list=[plan_list]
                else:
                    # その他の場合のエラー処理
                    self.logger.log("plan_list should be a list or a dictionary.")

                # 共通の処理関数を呼び出す
                for plan_number in range(max_count):
                    plan = plan_list[plan_number]
                    if type(plan) is str:
                        self.RunPlanList(plan,self.plan_lists,details)
                        continue
                    #子のRunPlanList内で書き換えられる可能性があるので、再設定
                    self.plan_list_name = plan_list_name
                    self.plan_number = plan_number
                    result_task_read = self.TaskRead(plan)
                    if result_task_read:
                        judge_instance = Judge.Judge(self.task_settings,self.information)
                        judge_details = {}
                        flag_judge = judge_instance.Result(self.task_condition , result_details = judge_details)
                        self.TaskStatusChange("Judge" + judge_details.get("detail","") , details = judge_details )
                        #step毎にPlanを実行するか、Skipするか選択する。
                        self.step_check_mode = self.task_settings.get("step_check_mode")
                        if self.step_check_mode:
                            details_step_check = {}
                            if self.task_type == "RunPlanLists":
                                message_list = []
                                #stepの設定確認を実行する。
                                check_file_path = self.task_settings.get("file_path","")
                                if os.path.exists(check_file_path):
                                    message_list.append(f"{check_file_path} exists")
                                else:
                                    message_list.append(f"{check_file_path} does not exists")
                                check_run_plan_list = self.task_settings.get("plan_lists",{})
                                if check_file_path == "":
                                    check_plan_lists = self.plan_lists
                                else:
                                    check_plan_lists = JSON_Control.ReadDictionary(check_file_path,{},details = details)
                                for check_run_plan in check_run_plan_list:
                                    if not check_run_plan in check_plan_lists:
                                        message_list.append(check_run_plan + " is not in plan lists.")

                                details_step_check = {"plan_lists": check_plan_lists.get(self.plan_list_name,""), "message_list" :message_list}
                            step_check_comment = self.task_settings.get("step_check_comment","")                   
                            if step_check_comment != "":
                                print (step_check_comment)
                            flag_judge = self.StepCheck(flag_judge,details_step_check)
                        #条件が成立したらPlanを実行する。
                        if flag_judge:
                            retry = True
                            while retry:
                                self.TaskStatusChange("Run_Plan" ,details)
                                result = self.ExecutePlan(plan,plan_list_name ,plan_lists,details)
                                retry_check = self.task_settings.get("retry_check",False)
                                if retry_check == True and result == False:
                                    input_text = self.RetryCheck("□Retry Task? y(yes)/other(no)")
                                    if input_text == "y":   
                                        retry = True
                                    else:
                                        retry = False
                                else:
                                    retry = False
                                flag_loop = self.task_loop
                                flag_terminate = self.task_terminate
                                if flag_terminate:
                                    flag_loop = False
                                loop_limit_count = self.task_settings.get("loop_limit_count",0)
                                if( loop_limit_count <= count):
                                    if 0 < loop_limit_count:
                                        flag_loop = False
                                        count = 0
                                if flag_loop:
                                    break
                            if flag_loop:
                                break                        
                        else:
                            self.TaskStatusChange("Skip_Plan" )
                            self.information[self.result_name] = {}
                    sleep_time = self.task_settings.get("sleep_time",0)
                    if flag_terminate:
                        break
                    time.sleep(sleep_time)
        self.TaskStatusChange("End",details)

    ####専用命令 Step####
    def Get_SettingsData(self , data_name , default_data = "",option_error_input = False):
        data = self.task_settings.get(data_name)
        value = default_data
        if data == None:
            if option_error_input:
                setting = {
                    "label" : "Please Input Data.",
                    "data_name" : data_name,
                    "default_data" :default_data
                }
                #editor = UserInterface.ValueEditor()
                #value = editor.input_data(setting)
        return value

    def StepCheck(self,flag_judge , details = {}):
        input_text = self.WaitInput("□Run Task("+ self.task_name +")? n(no)/other(yes)",details)
        if input_text == "n" or input_text == "no":
            flag_judge = False
        return flag_judge
        
    def ExecutePlan(self , plan,plan_list_name ,plan_lists,details = {}):
        #planに関するDataはself.task***にて実行。planは形式的に読み込んでいるだけ。
        self.execute_start_time = datetime.datetime.now()
        self.task_loop = False 
        self.task_terminate = False
        arguments = {
            "settings" : self.task_settings,
            "plan_list_name" :plan_list_name,
            "plan_lists" : plan_lists,
            "result_details" : {}
        }

        result_name = self.result_name        
        function_dictionary = self.Get_FunctionDictionary()
        if self.task_type == "":
            self.task_type = "Action"
        try:
            result_details = function_dictionary[self.task_type](arguments)
        except :
            result_details = function_dictionary["Action"](arguments) 
        if result_name != "":
            self.information[result_name] = result_details

        check_result = self.task_settings.get("check_result",{})
        if check_result !={}:
            self.CheckPlan(check_result,result_details,plan_list_name,plan)
              
        interval_time = self.execute_start_time - self.execute_end_time 
        self.execute_end_time = datetime.datetime.now()
        execution_time = self.execute_end_time - self.execute_start_time 

        task_details = {"type": self.task_type,"result_name":self.result_name}
        task_details.update(result_details)
        task_details.update(details)
        task_details["interval_time"] = str(interval_time)
        task_details["execution_time"] = str(execution_time)
        self.TaskStatusChange("Task_end" , task_details)
        return task_details.get("result",False)
    
    def CheckPlan(self,check_result,result_details,plan_list_name,plan):
        result_compare = Data.DeepCompare(check_result,result_details)
        if result_compare:
            message = "Check result is OK." + plan_list_name + " " + self.task_name
            self.logger.log(message,"INFO", details = result_details)
        else:
            message = "Check result is NG.plan list:" + plan_list_name + " plan name:" + self.task_name
            details ={}
            details = {"expect":check_result,"result":result_details}
            #planの出所を調べる。
            #copyしたplanはplanの直下にplan_file_pathを記述している。
            plan_file_path = plan.get("plan_file_path","")
            if plan_file_path =="":
                if self.read_plan_lists_file_path != "":
                    #RunPlanListsで他のFileから一時的に読み込んでいる場合はread_plan_lists_file_pathに記述している。
                    plan_file_path = self.read_plan_lists_file_path
                else :
                    #読込やcopyをしていないならclassのplan_lists_file_pathに記述している。
                    plan_file_path = self.plan_lists_file_path
            
            if self.task_settings.get("check_result_ng_stop",False):

                print("□plan_file_path:"+ plan_file_path)
                print("□plan list:" + plan_list_name)
                print("□plan name:" + self.task_name)
                print(details)
                if plan_file_path == "":
                    input_text = input("□Please check the results.")
                else:
                    input_text = input("□Please check the results. If you want to change the confirmation results documented in the file, please press 'y'")
                    if input_text=="y":
                        change_plan_lists = JSON_Control.ReadDictionary(plan_file_path)
                        change_plan_list = change_plan_lists.get(plan_list_name,{})
                        try:
                            change_plan = change_plan_list[self.plan_number]
                            change_plan_settings=change_plan.get("settings",{})
                            change_plan_list_settings_check_result=change_plan_settings.get("check_result",None)
                            if change_plan_list_settings_check_result==None:
                                print("□No plan list.")
                            else:
                                if change_plan_list_settings_check_result == check_result:
                                    input("□Is it OK to change the check_result?(OK:y)")
                                    if input_text=="y":
                                        change_plan_list[self.plan_number]["settings"]["check_result"]=result_details
                                        JSON_Control.WriteDictionary(plan_file_path,change_plan_lists)
                                else:
                                    print("□system error.check_result is not same between memory and file.")
                        except:
                            print("□Plan list error.")




            self.logger.error(message , details = details)



    ####専用機能呼び出し####
    def Get_FunctionDictionary(self):
        self.function_dictionary = {
            "ExecuteByContextFile":self.Call_ExecuteByContextFile,
            "Write_ContextFile":self.Call_Write_ContextFile,
            "RunPlanListsByContext": self.Call_RunPlanListsByContext,
            "RunPlanLists":self.Call_RunPlanListsBySettings,
            "CopyPlanLists": self.Call_CopyPlanListsBySettings,
            "Judge":self.Call_Judge,
            "ChangeSettings" : self.Call_ChangeSettings,
            "Log": self.Call_Log,
            "CopyInformation":self.Call_CopyInformation,
            "PrintInformation":self.Call_PrintInformation,
            "Print": self.Call_Print,
            "Action" : self.Call_Action
        }
        return self.function_dictionary

    def Call_ExecuteByContextFile(self , arguments):
        settings = arguments.get("settings",{})
        file_path = settings.get("file_path",{})
        result_details = self.ExecuteByContextFile(file_path)
        return result_details

    def Call_Write_ContextFile(self , arguments):
        settings = arguments.get("settings",{})
        file_path = settings.get("file_path",{})
        result_details = self.Write_ContextFile(file_path)
        return result_details

    def Call_RunPlanListsByContext(self , arguments):
        context = arguments.get("context",{})
        result_details = arguments.get("result_details",{})
        result_details = self.RunPlanListsByContext(context,result_details)
        return result_details
    
    def Call_RunPlanListsBySettings(self , arguments):
        settings = arguments.get("settings",{})
        plan_lists = self.plan_lists #arguments.get("plan_lists",{})
        result_details = arguments.get("result_details",{})
        result_details = self.RunPlanListsBySettings(settings,plan_lists,result_details)
        return result_details
    
    def Call_CopyPlanListsBySettings(self , arguments):
        settings = arguments.get("settings",{})
        plan_lists = self.plan_lists #arguments.get("plan_lists",{})
        result_details = arguments.get("result_details",{})
        result_details = self.CopyPlanListsBySettings(settings,plan_lists,result_details)
        
        self.plan_lists.update(result_details.get("plan_lists",{}))
        return result_details

    def Call_Judge(self , arguments):
        settings = arguments.get("settings",{})
        result_details = arguments.get("result_details",{})
        # task levelの情報にAccessできるJudge
        judge_instance = Judge.Judge(settings,self.information)
        # 条件式の評価
        condition_list = settings.get("condition_list",[])
        flag_judge = judge_instance.Result(condition_list = condition_list , information = self.information,result_details=result_details)
        self.logger.Setup(self.task_settings)
        message = "Judge:"+str(flag_judge)+"detail:"+result_details.get("detail","")
        self.logger.log(message ,"ERROR", details = result_details)

        # Loop条件式の評価
        loop_condition = settings.get("loop_condition",False)
        self.task_loop = self.judgeLoop(loop_condition,settings,self.information,{})
        if self.task_loop:
            if result_details!={}:
                message = "Loop:"+str(self.task_loop)+"detail:"+str(result_details.get("detail",""))
                self.logger.log(message,details = result_details)

        # Terminate条件式の評価
        terminate_condition = settings.get("terminate_condition",False)
        self.task_terminate = self.judgeLoopTerminate(terminate_condition,settings,self.information,result_details)
        
        result_details["result"] = flag_judge
        result_details["condition_list"] = condition_list
        if self.task_terminate:
            if result_details!={}:
                message = "Terminate:"+str(self.task_loop)+"detail:"+str(result_details.get("detail",""))
                self.logger.log(message,details = result_details)
        return result_details
    
    def Call_ChangeSettings(self , arguments):
        settings = arguments.get("settings",{})
        result_details = self.ChangeSettings(settings)
        return result_details

    def Call_Log(self , arguments):
        settings = arguments.get("settings",{})
        # task levelの情報にAccessできるLog
        message = settings.get("message","")
        level = settings.get("level","")
        self.logger.log(message,level)
        result_details = {"result" : True}
        
        return result_details
    
    def Call_CopyInformation(self , arguments):
        settings = arguments.get("settings",{})
        result_details = Dictionary.RestructureData(self.Information.get("source_data_name",{}), settings["data_structure"], settings["restructure_settings"])
        return result_details

    def Call_PrintInformation(self , arguments):
        print(self.information)
        result_details = {"result" : True}
        return result_details
        
    def Call_Print(self , arguments):
        settings = arguments.get("settings",{})
        message = settings.get("message","")
        print(message)
        result_details =  {"result" : True , "message" : message}
        return result_details

    def Call_Action(self , arguments):
        settings = self.task_settings
        #settings = arguments.get("settings",{})
        plan_list_name = arguments.get("plan_list_name",{})
        result_details = arguments.get("result_details",{})

        task_type = self.task_type
        action = Action.Action(settings)
        result_details["plan_list_name"] = plan_list_name
        self.TaskStatusChange("Run_PlanList", result_details)
        result_details = action.Execute(task_type , settings) 
        return result_details
 
    def TaskStatusChange(self , status ,  details = {}):
        self.task_status = status
        detail_dictionary = {}
        task_list = details.get("task_list",[ self.name , self.task_name])
        if task_list[-1] != self.task_name:
            task_list.append(self.task_name)
            details = task_list
        detail_dictionary["task"] = ".".join(task_list)
        detail_dictionary["type"] = self.task_type
        detail_dictionary["status"] = self.task_status
        if type(details) is not dict:
            detail_dictionary["detail"] = details
        else:
            detail_dictionary.update(details)

        self.logger.log("TaskStatusChange "+self.task_status+" "+self.plan_list_name+" "+self.task_name  ,"INFO",details = detail_dictionary)
        if status == "End":
            self.task_name = ""
            self.task_type = ""
            self.task_settings = {}
            self.task_condition = []
            self.logger.MessageList_Write()

    def TaskRead(self,plan):
        if type(plan) is not dict:
            details = {}
            self.logger.log("The Plan that was read is not in the Dictionary format. ","ERROR",details = details)
            return False
        name = plan.get("name")
        if name is None:
            name = ""
        self.task_name = name
        #Task名を読み込む
        self.result_name = plan.get("result_name","")
        if(self.result_name == ""):
            self.result_name = "Result_"+self.task_name
        #機能typeを読み込む
        self.task_type = plan.get("type","")
        #設定を読み込む
        self.task_settings = plan.get("settings",{})
        #Task名毎の設定と共通設定を変更する
        if self.filter_change_settings == []:
            change_settings = self.change_settings
        else:
            change_settings = self.FilterDictionaryByKeys(self.change_settings, self.filter_change_settings)
        self.task_settings.update(change_settings)

        change_settings_by_name = self.change_settings_by_name.get(name,{})
        if change_settings_by_name != {}:
            self.task_settings.update(change_settings_by_name)

        self.task_condition = plan.get("condition_list",[])

        self.logger = Log.Logs(self.task_settings)
        details = plan
        #self.logger.log("Task Read","DEBUG",details = details)
        return True


    def WaitInput(self,text,details = {}):
        if type(details) is dict:
            if details == {}:
                details_text = ""
            else:
                details_text = JSON_Control.ToString(details)
        elif type(details) is list:
            details_text = ",".join(details)
        else:
            details_text  = details

        if details_text == "":
            input_text = input(text)
        else:
            input_text = input(details_text +"\n"+ text)
        return input_text
    
    def RetryCheck(self,text):
        input_text = input(text)
        return input_text

    #command lineから機能を利用する。
def main():
    # Command lineの引数を得てから機能を実行し、標準出力を出力IFとして動作する。
    # 単体として動作するように実行部のExecuteは辞書を入出力IFとして動作する。
    class_instance = Task()
    class_instance.ArgumentGet()
    result_dictionary = class_instance.Execute()
    FunctionUtility.Result(result_dictionary)
    
if __name__ == '__main__':
    main()

