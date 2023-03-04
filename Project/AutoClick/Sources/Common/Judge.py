## $python ##
import datetime
import os
import sys
import dataclasses
import re

sys.path.append("../Common")
sys.path.append("../../Common")
import FileControl
import weekday
import auto

@dataclasses.dataclass
class Judge:
    conditions:list = None
    information:dict = None
    default_result:bool = True

    def __init__(self , conditions = None , information:dict = None , default_result=True) :
        self.setting(conditions  , information , default_result)

    def setting(self , conditions = None , information:dict = None , default_result=True) :
        if conditions is not None:
            self.conditions = conditions
        if information is not None:
            self.information = information


    def Result(self , conditions = None ,information = None):
        if conditions is None:
            conditions = self.conditions
        print("#####" + str(conditions))
        if information is None:
            information = self.information
        result = self.Results_ByDictionaryInformation(conditions,information,self.default_result)
        return result


    def Results_ByDictionaryInformation(self , conditions , information , default_result=True):
        if conditions is None:
            return default_result
        if conditions == "":
            return default_result
        if information is None:
            return default_result
        result = default_result
        if conditions is not None:
            if type(conditions) == list:
                for condition in conditions:
                    result = self.Result_ByDictionaryInformation(condition,information)
                    if result == False:
                        return False
            else:
                result = self.Result_ByDictionaryInformation(conditions,information)
                if result == False:
                    return False
            return True
        print("####Judge.Result:condition is none")        
        return default_result
    
    def Result_ByDictionaryInformation(self , condition , information):
        print("######仮のsplit分割処理#####")
        condition_or_list = condition.split(",") 
        for condition_item in condition_or_list:
            print("######仮の判断処理#####")
            condition_parts_list =re.split("(==|<=|>=|<>|<|=|>)", condition_item)
            print(condition_parts_list)
            left_data = self.TextChangeToData_ByDefaultAndDictionary(condition_parts_list[0],information,"result")
            right_data = self.TextChangeToData_ByDefaultAndDictionary(condition_parts_list[2],information,"result")
            print("#######left_data:"+str(left_data)+str(type(left_data))+" right_data:"+str(right_data)+str(type(right_data)))

            if left_data == right_data :
                print("#########True##############")
                return True
        print("#########False##############")
        return False

    #文字列をDictionaryのDataに置き換える。
    #***.****.**のように.の指定でDictionary内のDictionaryにアクセスする仕様。
    def TextChangeToData_ByDefaultAndDictionary(self , expression , data_dictionary, default_key = ""):
        #ENUMに置換する（一般性が無いので没。出力側でENUMを文字列に変換する。）
        #enum_data = auto.enum_dictionary.get(expression)
        #if enum_data is not None:
        #    return enum_data
        if expression == "True":
            return True
        if expression == "False":
            return False
        if expression == "None":
            return None
        return self.TextChangeToData_ByDictionary(expression , data_dictionary,default_key)
        
    def TextChangeToData_ByDictionary(self , expression , data_dictionary, default_key = ""):
        text_list = expression.split(".")
        temp_dictionary = data_dictionary
        print("TextChange split after type:"+str(type(text_list)))
        for text in text_list:
            temp_dictionary = temp_dictionary.get(text)
            print("temp_dictionary"+str(type(temp_dictionary)))
            print(temp_dictionary)
            if temp_dictionary is None :
                print("TextChangeToData_ByDictionary1")
                #Error:There is not the specified dictionary 
                #Dataがdictionary内に無い場合は引数は文字列比較と判断し、そのまま引数を返す。
                return expression
        if type(temp_dictionary) == dict:
            if default_key != "":
                return temp_dictionary.get(default_key)
                print("TextChangeToData_ByDictionary2")
            else:
                print("TextChangeToData_ByDictionary3")
                return expression
        elif temp_dictionary is not None:
            print("TextChangeToData_ByDictionary4")
            #指定されたDataがdictionaryではない場合は値を返す。
            return temp_dictionary
        else:
            return temp_dictionary
        
