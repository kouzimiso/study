## $python 画像自動Click ##
#設定したフォルダ内の画像を順番に画面表示から探し、クリックする。
import sys
import os
import datetime
import unittest


sys.path.append("./Common")
sys.path.append("./Models")
sys.path.append("./ViewModels")
sys.path.append("./Views")

import Log
import Scheduler

#Log関係
message_list=[]
logfile_path='../Log/log_test_auto.json'#準備必要問題:Folder

class Test(unittest.TestCase):
    def test_Auto5_JsonExecute(self):
        Scheduler.StartUp("Start","../Setting/RunTest.json")

#Main Program実行部
def main():

    unittest.main()

if __name__ == "__main__":
    sys.exit(main())
