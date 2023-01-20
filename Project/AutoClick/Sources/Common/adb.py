import subprocess
import os



def Get_DeviceAddress():
    dev_str = subprocess.check_output(["nox_adb", "devices"])
    device_address = dev_str.decode("utf-8").splitlines()[1].split("\t")[0]
    return device_address

def Get_ScreenSize(device_address):
    res = subprocess.run("nox_adb -s %s shell wm size" %(device_address), shell=True, stdout=subprocess.PIPE)
    resol = res.stdout
    print(resol)
    
def ScreenCapture(device_address,file_path):    
    #スマホの画像をscreen captureする
    subprocess.call("nox_adb -s %s exec-out screencap -p > %s" % (device_address,file_path), shell=True)
    #subprocess.call("nox_adb %s exec-out screencap -p > %s" % (device_address,flle_img_screenshot), shell=True, cwd=img_dir)

def Tap(device_address, x, y):
    subprocess.call("nox_adb -s %s shell input touchscreen tap %d %d" % (device_address, x, y), \
        shell=True)
