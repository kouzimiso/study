#Task実行計画はPlanListsで管理される
#PlanListはUserが容易に用意できる一般的な形式で管理する。
#PlanListsはdictionary、PlanListはlist、Planはdictionary。
#本Planが用意する機能はPlanListsの形式を編集・操作するための物です。
class Plan:
    name:str
    actions: list
    
    def ExecuteTask(self,name,plan):
        print("ExecuteTask:"+ name)
        if(plan.type==""):
            print("Execute")
