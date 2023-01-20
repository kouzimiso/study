import enum
import sys
sys.path.append("../Common")
sys.path.append("../../Common")
import auto
import Recognition

#文字列のAction名と設定辞書で動作するだけの関数
class Action:
    def __init__(self) -> None:
        pass

    def Execute(self, type = "" , setting_dictionary = None):
        result_dictionary={}
        if (type == "Recognition"):
            recognition = Recognition.Recognition(setting_dictionary)
            result_dictionary=recognition.Execute()

        return result_dictionary


