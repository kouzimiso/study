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
        if information is None:
            information = self.information
        result = self.Results_ByDictionaryInformation(conditions,information,self.default_result)
        return result


    def Results_ByDictionaryInformation(self , conditions , information , default_result=True):
        if conditions is None:
            return default_result
        if information is None:
            return default_result
        print("####Judge.Result")
        result = default_result
        if conditions is not None:
            for condition in conditions:
                result = self.Result_ByDictionaryInformation(condition,information)
                if result == False:
                    return False
            return True
        print("####Judge.Result:condition is none")        
        return default_result
    
    def Result_ByDictionaryInformation(self , condition , information):
        print("######仮の判断処理#####")
        condition_or_list = condition.split(",") 
        for condition_item in condition_or_list:
            print("######仮の判断処理#####")
            condition_parts_list =re.split("(==|<=|>=|<>|<|=|>)", condition_item)
            print(condition_parts_list)
            left_data = self.TextChangeToData_ByDefaultAndDictionary(condition_parts_list[0],information)
            right_data = self.TextChangeToData_ByDefaultAndDictionary(condition_parts_list[2],information)
            if left_data == right_data :
                print("#########True##############")
                return True
        print("#########False##############")
        return False

    def TextChangeToData_ByDefaultAndDictionary(self , text , information):
        if text == "True":
            return True
        if text == "False":
            return False
        return information.get(text)