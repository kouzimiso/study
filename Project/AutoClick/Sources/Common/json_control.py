import json


def WriteDictionary(file_path,data_dictionary):
    file = open(file_path,'w', encoding='utf-8')
    json.dump(data_dictionary, file)
    file.close()

def ReadDictionary(file_path,data_dictionary):
    file = open(file_path,'r', encoding='utf-8')
    data_dictionary = json.load(file)
    file.close()
    return data_dictionary
