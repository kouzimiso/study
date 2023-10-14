## $python ##
import datetime
import os
import sys
import dataclasses
import re

sys.path.append("../Common")
sys.path.append("../../Common")
import FileControl
import Auto
import Log
import ClassControl



@dataclasses.dataclass
class Judge:
    condition_list:list= None
    information:dict = None
    default_result:bool =True

    default_settings_dictionary={
        "condition_list":[],
        "information" : {},
        "default_result":True,
    }

    def __init__(self ,  settings_dictionary = {},information={}) :
        self.logger = Log.Logs(settings_dictionary)
        ClassControl.update_from_dict(self,self.default_settings_dictionary)
        self.Setup(settings_dictionary,information)

    def Setup(self , settings_dictionary , information = {} ) :
        self.logger.Setup(settings_dictionary)
        self.information = information
        if("condition_list" in settings_dictionary ):
            self.condition_list = settings_dictionary["condition_list"]
        if("default_result" in settings_dictionary ):
            self.default_result = settings_dictionary["default_result"]

    def Result(self , condition_list = None ,information = None,default_result = None , result_details ={}):
        if condition_list is None:
            condition_list = self.condition_list 
        if information is None:
            information = self.information
        if default_result is None:
            default_result = self.default_result
        if type(condition_list) is bool:
            return condition_list

        result = self.Results_ByDictionaryInformation(condition_list,information,default_result,result_details)
        return result


    def Results_ByDictionaryInformation(self , condition_list , information  , default_result = None,result_details ={}):
        if condition_list is None:
            result_details.update( { "result": None ,"detail": str(default_result)+":Judge result condition is none","level" : "INFO"})
            return default_result
        elif condition_list == "":
            result_details.update( { "result": default_result ,"detail": str(default_result)+":Judge result condition is a blank","level" : "INFO"})
            return default_result
        elif information is None:
            result_details.update(  { "result": default_result, "detail" : str(default_result)+":Judge result information is none","level" : "INFO"})
            return default_result
        else:
            result = default_result
            trace_list=[]
            if type(condition_list) == list:
                if condition_list ==[]:
                    result_details.update({ "result": default_result, "detail" : str(default_result)+":Judge result condition is blank","level" : "INFO"})
                    return default_result
                for condition in condition_list:
                    trace_list_or=[]
                    result = self.Result_ByDictionaryInformation(condition,information,trace_list = trace_list_or)
                    join_trace_list_or = "("+",".join(trace_list_or)+")"
                    if result == False:
                        trace_list.append(join_trace_list_or)
                        result_details.update({ "result": False, "detail" :"Judge result false." + join_trace_list_or,"level" : "INFO" })
                        return False
                    trace_list.append(join_trace_list_or)
            else:
                if condition_list == "":
                    result_details.update({"result": default_result, "detail" :  str(default_result)+":Judge result condition is blank","level" : "INFO"})
                    return default_result
                result = self.Result_ByDictionaryInformation(condition_list,information,trace_list =trace_list)
                if result == False:
                    result_details.update({"result": False , "detail" :  "Judge result false("+ ",".join(trace_list) + ")","level" : "INFO"})
                    return False
            result_details.update({"result": True , "detail" : "Judge result true("+",".join(trace_list)+")","level" : "INFO"})
            return True
        
    def Result_ByDictionaryInformation(self , condition , information,trace_list=[]):
        ######仮のsplit分割処理#####
        condition_or_list = condition.split(",") 
        details={}
        for condition_item in condition_or_list:
            ######仮の判断処理#####
            condition_parts_list =re.split("(==|<=|>=|<>|<|=|>)", condition_item)
            
            trace_list_parts=[]
            left_condition = condition_parts_list[0].strip()
            left_data = self.TextChangeToData_ByDefaultAndDictionary(left_condition,information,"result",trace_list = trace_list_parts)
            sign = condition_parts_list[1].strip()
            trace_list_parts.append(sign)
            right_condition = condition_parts_list[2].strip()
            right_data = self.TextChangeToData_ByDefaultAndDictionary(right_condition,information,"result",trace_list =  trace_list_parts)
            details["condition"] = condition_item
            details[left_condition]= str(type(left_data))
            details[right_condition] = str(type(right_data))
            
            if left_data == right_data :
                trace_list.append(condition_item+":True("+" ".join(trace_list_parts)+")")
                return True
            trace_list.append(condition_item+":False("+" ".join(trace_list_parts)+")")
        details["condition"] = condition_item
        return False

    #文字列をDictionaryのDataに置き換える。
    #***.****.**のように.の指定でDictionary内のDictionaryにアクセスする仕様。
    def TextChangeToData_ByDefaultAndDictionary(self , expression , data_dictionary, default_key = "",trace_list=[]):
        #ENUMに置換する（一般性が無いので没。出力側でENUMを文字列に変換する。）
        #enum_data = Auto.enum_dictionary.get(expression)
        #if enum_data is not None:
        #    return enum_data
        if expression == "True" or expression == "true":
            trace_list.append(expression+"(True)")
            return True
        if expression == "False" or  expression == "false":
            trace_list.append(expression+"(False)")
            return False
        if expression == "None":
            trace_list.append(expression+"(None)")
            return None
        result = self.TextChangeToData_ByDictionary(expression , data_dictionary,default_key,trace_list = trace_list)
        return result
        
    def TextChangeToData_ByDictionary(self , expression , data_dictionary, default_key = "",trace_list=[]):
        text_list = expression.split(".")
        temp_dictionary = data_dictionary
        details ={"text_list":text_list }
        for text in text_list:
            temp_dictionary = temp_dictionary.get(text)
            details["text"]= text
            details["value"]= temp_dictionary
            details["text_type"]= str(type(temp_dictionary))
            #self.logger.log("ChangeToData","INFO",details=details)
            if temp_dictionary is None :
                #Error:There is not the specified dictionary 
                #Dataがdictionary内に無い場合は引数は文字列比較と判断し、そのまま引数を返す。
                trace_list.append(expression+"(It is not in the dictionary)")
                return expression
        if type(temp_dictionary) == dict:
            if default_key != "":
                value = temp_dictionary.get(default_key)
                trace_list.append(expression+"(" + str(value) + ":by Default key="+default_key+")")
                return value
            else:
                trace_list.append(expression+"(Change data is false)")
                return expression
        elif temp_dictionary is not None:
            #指定されたDataがdictionaryではない場合は値を返す。
            trace_list.append(expression+"("+ str(temp_dictionary) + ")")
            return temp_dictionary
        else:
            #self.logger.log("ChangeToData None","INFO",details=details)
            trace_list.append(expression+"(Change data is None)")
            return temp_dictionary
        
