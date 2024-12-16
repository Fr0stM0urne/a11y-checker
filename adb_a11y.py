import time, subprocess, os, random, re
import xml.etree.ElementTree as ET
from uiautomator import device as uiAutoDevice

class adb_a11y:
    def __init__(self, deviceID):
        self.deviceID = deviceID
        self.actions = ["previous", "next", "perform_click_action"]
        pass

    def input_text(self, text_input):
        os.system(f"adb -s {self.deviceID} shell input text {text_input}")

    def ally_action(self, action):
        if action == "print_node_tree":
            print("Printing node tree...")
            time.sleep(2)
        os.system(f"adb -s {self.deviceID} shell am broadcast  -a com.a11y.adb.{action}")

    def install_apk(self, apkPath):
        print("Installing apk...")
        os.system(f"adb -s {self.deviceID} install -g {apkPath}")

    def generate_test_input(self):
        devOrntCmd = "adb -s " + self.deviceID + " shell dumpsys input | grep 'SurfaceOrientation' |  awk '{ print $2 }'"
        ornt = subprocess.check_output(devOrntCmd, shell=True)
        ornt = ornt.decode("utf-8")
        # randSwipe = "adb -s " + devID + " shell input touchscreen swipe "+ x +" "+ y +" "+ x +" "+ y +" 2000"
        # getAppRes = "adb -s " + devID + "  shell dumpsys window | grep -i mDisplayInfo=DisplayInfo | awk '{print $8, $10}'"
        xLim = 1050
        yLim = 1050

        if ornt[:-1] == "0":
            print("Portrait")
            xLim = 1050
            yLim = 2050
        elif ornt[:-1] == "1":
            print("LandScape 1")
            xLim = 2050
            yLim = 1050
        else:
            xLim = 2050
            yLim = 1050
            print("LandScape 3")

        for i in range(0, 10):
            x = str(random.randrange(70,xLim))
            y = str(random.randrange(70,yLim))
            randTouch = "adb -s " + self.deviceID + " shell input tap "+ x +" "+ y
            os.system(randTouch)

    def random_inputs(self, inputCount, appPkg):
        # monkeyCmd = "adb -s " + self.deviceID + " shell monkey --kill-process-after-error --throttle 500 --pct-touch 0 --pct-anyevent 0 --pct-syskeys 0 --pct-trackball 0 --pct-nav 0 --pct-motion 0 --pct-majornav 0 --pct-appswitch 100 -p " + appPkg + " 4"
        monkeyCmd = "adb -s " + self.deviceID + " shell monkey --throttle 1000 --pct-touch 60 --pct-anyevent 5 --pct-syskeys 5 --pct-trackball 5 --pct-nav 5 --pct-motion 10 --pct-appswitch 10 -p " + appPkg + "-v 100"
        # for i in range(inputCount):
        #     self.generate_test_input()
        os.system(monkeyCmd)
        time.sleep(3)

    def get_ui_element(self, xmlPath, sleepTimer):
        element = None
        while element is None:
            uiTree = self.get_ui_tree(xmlPath)
            if uiTree is None:
                return None
            element = uiTree.findall(xmlPath)
            if element is None or len(element) == 0:
                print(f"Retry get UI element {xmlPath} in {sleepTimer}...")
                time.sleep(sleepTimer)
                sleepTimer -= 1
        return element

    def get_ui_tree(self, xmlPath):
        UIparsed = False
        parseRetries = 3
        print("Parsing UI tree for "+xmlPath)
        while not UIparsed:
            try:
                uiAutoDevice.dump(self.uiTreePath)
                with open(self.uiTreePath, 'r') as f:
                    scrn = f.read()
                tree = ET.fromstring(scrn)
                UIparsed = True
            except Exception as e:
                print(f"Error: Could not parse {self.uiTreePath}. {e}")
                parseRetries -= 1
                if parseRetries == 0:
                    return None
                time.sleep(1)

        # os.system(f"rm {self.uiTreePath}")
        return tree

    def get_bounds(self, ele):
        bounds = ele.attrib['bounds']
        bounds = bounds.replace('[', '').replace(']', ',').split(',')
        x = (int(bounds[0]) + int(bounds[2])) / 2
        y = (int(bounds[1]) + int(bounds[3])) / 2
        return x, y

    def tap_element(self, ele):
        x, y = self.get_bounds(ele)
        os.system(f'adb -s {self.deviceID} shell input tap {x} {y}')

    def get_installed_pkgs(self, appType):
        if appType == "user":
            pkgList = subprocess.check_output(f'adb -s {self.deviceID} shell pm list packages -3 | cut -f 2 -d ":"', shell=True)
        elif appType == "system":
            pkgList = subprocess.check_output(f'adb -s {self.deviceID} shell pm list packages -f | cut -f 2 -d ":" | grep -E "/system/(app|priv-app)/" | rev | cut -f 1 -d "=" | rev', shell=True)
        elif appType == "all":
            pkgList = subprocess.check_output(f'adb -s {self.deviceID} shell pm list packages | cut -f 2 -d ":"', shell=True)
        pkgList = pkgList.decode("utf-8").splitlines()
        return pkgList
    
    def launch_app(self, appPkg):
        print(f'Launching {appPkg}...')
        getMainActivityCmd = f"adb -s {self.deviceID} shell \"cmd package resolve-activity --brief {appPkg} | tail -n 1\""
        mainActivity = subprocess.check_output(getMainActivityCmd, shell=True).decode("utf-8")[:-1]
        startCmd = f"adb -s {self.deviceID} shell am start -W -n {mainActivity}"
        launchRetries = 3
        while self.get_front_app().split("/")[0] != mainActivity.split("/")[0]:
            if os.system(startCmd):
                print(f"Error: Could not start {appPkg}.")
            launchRetries -= 1
            if launchRetries == 0:
                return False
            time.sleep(2)
        return True

    def get_front_app(self):
        frontAppCmd = f"adb -s {self.deviceID} shell dumpsys activity activities | grep -i mCurrentFocus |  awk '{{ print $3 }}'"
        frontApp = subprocess.check_output(frontAppCmd, shell=True).decode("utf-8")[:-2]
        return frontApp

    def close_app(self, appPkg):
        os.system(f"adb -s {self.deviceID} shell am force-stop {appPkg}")

    def clean_up(self, appPkg):
        os.system(f"adb -s {self.deviceID} shell am force-stop {appPkg}")
        os.system(f"adb -s {self.deviceID} uninstall {appPkg}")
    
    def a11y_tap(self, a11y_coords):
        # (22, 231 - 243, 363)
        coords_match = re.search(r'\((\d+), (\d+) - (\d+), (\d+)\)', a11y_coords)
        if coords_match:
            x = (int(coords_match.group(1)) + int(coords_match.group(3))) // 2
            y = (int(coords_match.group(2)) + int(coords_match.group(4))) // 2

        os.system(f"adb -s {self.deviceID} shell input tap {x} {y}")

if __name__ == "__main__":
    adbDevice = adb_a11y("931AY05A0C")
    # adbDevice.install_app("app.pkg")
    from IPython import embed
    embed()