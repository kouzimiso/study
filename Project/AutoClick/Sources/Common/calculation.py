


def differential_rating_value(list_value1,list_value2,list_rate,label=[]):
    result=0
    loop=0
    for value1,value2,rate in zip(list_value1,list_value2,list_rate):
        diff = float(value1) - float(value2)
        result= result + diff * rate
        if label[loop:loop+1]:
            print(lavel[loop]+"("+ str(round(rate,2))+"):" + str(diff) +"\t("+str(value1) +" -> "+ str(value2) +")")
        loop+1
    return result
        
