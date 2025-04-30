def read(settings,item,default=""):
    return settings.get(item, default)

def write(settings,item,value):
    settings[item] = value

def read2(settings,item1,item2,default=""):
    return settings.get(item1, {}).get(item2, default)

def write2(settings,item1,item2,value):
    # キーが存在しない場合の初期化
    if item1 not in settings:
        settings[item1] = {}
    settings[item1][item2] = value

def exist2(settings,item1,item2,value):
    read_value = read2(settings,item1,item2,None)
    if read_value:
        if type(read_value) is list:
            if value in read_value:
                return True
            else:
                return False
        else:
            if value == read_value:
                return True
            else:
                return False
    else:
        return False

def altanete_set_reset2(settings,item1,item2,value):
    read_value = read2(settings,item1,item2,None)
    if read_value:
        if type(read_value) is list:
            if value in read_value:
                read_value.remove(value)
            else:
                read_value.append(value)
        else:
            if value == read_value:
                read_value = None
            else:
                read_value = [read_value,value]
    else:
        read_value = value
    write2(settings,item1,item2,read_value)
