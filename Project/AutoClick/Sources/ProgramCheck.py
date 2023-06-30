import cProfile
import test_RunTest_json

def my_function():
    test_RunTest_json.main()
    
cProfile.run('my_function()')
