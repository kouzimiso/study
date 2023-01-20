## $python ##
import datetime
import os
import sys
import dataclasses

sys.path.append("../Common")
sys.path.append("../../Common")
import FileControl
import weekday

@dataclasses.dataclass
class Judge:
    conditions:list = None
    information:dict = None

    def __init__(self , condition_dictionary = None) :
        if condition_dictionary != None:
            self.conditions = condition_dictionary.get("conditions")
    
    def Result(self , conditions = None ,information = None):
        if conditions is None:
            if self.conditions is None:
                conditions = self.conditions
        print("####Judge.Result")
        if conditions is not None:
            for condition in conditions:
                print(condition)
                return True
        print("####Judge.Result:condition is none")        
        return True