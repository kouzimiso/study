import re

class Parser:

    def SplitByDictionary(self,text,data_dictioanry):
        regular_expression = ""
        for key in data_dictioanry.keys():
            if regular_expression == "":
                regular_expression="(" + key
            else:
                regular_expression = regular_expression + "|" +key
        regular_expression = regular_expression + ")"
        text_list =re.split(regular_expression , text)
        if "" in text_list:
            text_list.remove("")
        return text_list
