import json
import os

def WriteDictionary(file_path,data_dictionary):
    file = open(file_path,'w', encoding='utf-8')
    json.dump(data_dictionary, file,  ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
    file.close()

def ToString(data_dictionary={}):
    return json.dumps(data_dictionary)
    
def ReadDictionary(file_path,data_dictionary={},details = {}):
    if os.path.isfile(file_path):
        file = open(file_path,'r', encoding='utf-8')
        temp_dictionary = json.load(file)
        #try:
        #    temp_dictionary = json.load(file)
        #except:
        #    details.update({"message":"" , "level" :"ERROR"})
        #    return data_dictionary
        data_dictionary.update(temp_dictionary)
        file.close()
    return data_dictionary

