import json
import os
import traceback
import LogMessage
def WriteDictionary(file_path,data_dictionary):
    file = open(file_path,'w', encoding='utf-8')
    json.dump(data_dictionary, file,  ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
    file.close()

def ToString(data_dictionary={}):
    return json.dumps(data_dictionary)
    
def ReadDictionary(file_path,data_dictionary={},details = {}):
    if os.path.isfile(file_path):
        try:
            file = open(file_path,'r', encoding='utf-8')

            temp_dictionary = json.load(file)
            data_dictionary.update(temp_dictionary)
        except FileNotFoundError as e:
            error_dictionary =LogMessage.Get_Error_Dictionary()
            #type(e).__name__ ,"detail":str(e) ,"traceback" : traceback.format_exc()
            details.update({"result":False ,"message":"FileNotFoundError" , "level" :"ERROR","error":error_dictionary})
            
        except json.JSONDecodeError as e:
            error_dictionary =LogMessage.Get_Error_Dictionary()
            details.update({"result":False ,"message":"JSONDecodeError" , "level" :"ERROR","error":error_dictionary})
            
        except Exception as e:
            error_dictionary =LogMessage.Get_Error_Dictionary()
            details.update({"result":False ,"message":"Exception" , "level" :"ERROR","error":error_dictionary})
        file.close()
    else:
        details.update({"result":False ,"message":"FileNotFoundError", "level" :"ERROR"})
        
    return data_dictionary

def JsonToDictionary(data_json,data_dictionary={},details = {}):
    try:
        temp_dictionary = json.load(data_json)
        data_dictionary.update(temp_dictionary)
                    
    except json.JSONDecodeError as e:
        error_dictionary =LogMessage.Get_Error_Dictionary()
        details.update({"result":False ,"message":"JSONDecodeError" , "level" :"ERROR","error":error_dictionary})
              
    except Exception as e:
        error_dictionary =LogMessage.Get_Error_Dictionary()
        details.update({"result":False ,"message":"Exception" , "level" :"ERROR","error":error_dictionary})
    return temp_dictionary
