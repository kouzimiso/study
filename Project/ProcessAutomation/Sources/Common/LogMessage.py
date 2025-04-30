import sys
import traceback
import json
import inspect

def Get_Error_Json(flag_trace = True, error_type ="",error_message="",error_level="ERROR"):
    result = Get_Error_Dictionary(flag_trace,error_type , error_message,error_level)
    return json.dumps(result)

def Get_Error_Dictionary(flag_trace = True, error_type ="",error_message="",error_level="ERROR"):
    error_information_dictionary = {}
    if flag_trace:
        exc_type , exc_value , exc_traceback = sys.exc_info()
        trace_dictionary = Get_Trace_Dictionary(exc_type , exc_value , exc_traceback)
        error_information_dictionary.update(trace_dictionary)
    if error_type != "":
        error_information_dictionary["type"] = error_type
    if error_level != "":
        error_information_dictionary["level"] = error_level
    if error_message != "":
        error_information_dictionary["message"] = error_message
    if error_information_dictionary.get("function","") == "":
        error_information_dictionary["function"] = inspect.stack()[1].function
    return error_information_dictionary
        
def Get_Trace_Dictionary(exc_type , exc_value , exc_traceback):
    if exc_type ==None:
        error_information_dictionary ={}
    else:
        error_information_dictionary ={
            'type': exc_type.__name__ , 
            'function': exc_traceback.tb_frame.f_code.co_name , 
            'lineno': exc_traceback.tb_lineno , 
            'filename': exc_traceback.tb_frame.f_code.co_filename,
            "traceback" : traceback.format_exc()
            
        }
        message = str(exc_value)
        if message:
            error_information_dictionary["message"] = message

    return error_information_dictionary

