import time, subprocess, os, random
import xml.etree.ElementTree as ET
from uiautomator import device as uiAutoDevice

class adbUI:
    def __init__(self, deviceID, uiTreePath):
        self.deviceID = deviceID
        self.uiTreePath = uiTreePath
        pass

    def read_local_dir(self, localApkDir):
        self.localApkDir = localApkDir
        self.apkDict = {}
        apkList = os.listdir(localApkDir)
        for apk in apkList:
            if apk.endswith(".apk"):
                self.apkDict[apk.split(".apk")[0]] = "apk"
            elif apk.endswith(".xapk"):
                self.apkDict[apk.split(".xapk")[0]] = "xapk"

    def install_xapk(self, apkPath):
        print("Installing xapk...")
        unzipPath = "xapkUnzip"
        os.system("unzip "+apkPath+" -d "+unzipPath)
        files = os.listdir(unzipPath)
        cmd = f'adb -s {self.deviceID} install-multiple '
        for app in files:
            if app.endswith(".apk"):
                cmd += f'"{unzipPath}/{app}" '
        print("Running: "+cmd)
        os.system(cmd)
        # os.system("rm -rf "+unzipPath)

    def install_apk(self, apkPath):
        print("Installing apk...")
        os.system(f"adb -s {self.deviceID} install -g {apkPath}")

    def install_local_app(self, appPkg):
        if self.apkDict[appPkg] == "apk":
            apkPath = f'{self.localApkDir}/{appPkg}.apk'
            self.install_apk(apkPath)
            return "apk"
        elif self.apkDict[appPkg] == "xapk":
            apkPath = f'{self.localApkDir}/{appPkg}.xapk'
            self.install_xapk(apkPath)
            return "xapk"

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

    def launch_playstore(self, appPkg):
        print('Launching Play Store...')
        os.system(f'adb -s {self.deviceID} shell am start -a android.intent.action.VIEW -d "market://details?id={appPkg}"')
        # Wait for playstore to load
        storeRetries = 2
        storeActivities = ["com.android.vending/com.android.vending.AssetBrowserActivity", "com.android.vending/com.google.android.finsky.activities.MainActivity"]
        while self.get_front_app() not in storeActivities:
            os.system(f'adb -s {self.deviceID} shell am start -a android.intent.action.VIEW -d "market://details?id={appPkg}"')
            time.sleep(2)
            print("Retry launching Play Store...")
            storeRetries -= 1
            if storeRetries == 0:
                return False
        return True

    def tap_element(self, ele):
        x, y = self.get_bounds(ele)
        os.system(f'adb -s {self.deviceID} shell input tap {x} {y}')

    def cannot_install_fix(self):
        gotItEles = self.get_ui_element(".//node[@text='Got it']", 3)
        self.tap_element(gotItEles[0])
        self.close_app("com.android.vending")
        print("Restarting Play Store...")
        time.sleep(10)

    # <node index="0" text="Install" resource-id="" class="android.widget.TextView" package="com.android.vending" content-desc="Install" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[486,829][595,884]" />
    def install_app(self, appPkg):
        installRetries = 3
        while installRetries > 0:
            installRetries -= 1
            if not self.launch_playstore(appPkg):
                return "PlayStoreError"
            installEles = self.get_ui_element(".//node[@content-desc='Install']", 3)
            if installEles is None or len(installEles) == 0:
                if len(self.get_ui_element(".//node[@text='Item not found.']", 3)) > 0:
                    print(f'Error: {appPkg} not found in Play Store.')
                    return "NotFoundInStore"
                elif len(self.get_ui_element(".//node[@text='Got it']", 3)) > 0:
                    self.cannot_install_fix()
                    continue
            else:
                self.tap_element(installEles[0])
                time.sleep(5)
                downloadRes = self.wait_for_download(appPkg)
                if downloadRes != True:
                    if len(self.get_ui_element(".//node[@text='Got it']", 3)) > 0:
                        self.cannot_install_fix()
                        continue
                    return downloadRes
                return True
        return "PlayStoreError"
        # input(f'Error: Could not find Install button for {appPkg}.\nInstall manually and press Enter to continue...')

    def get_installed_pkgs(self, appType):
        if appType == "user":
            pkgList = subprocess.check_output(f'adb -s {self.deviceID} shell pm list packages -3 | cut -f 2 -d ":"', shell=True)
        elif appType == "system":
            pkgList = subprocess.check_output(f'adb -s {self.deviceID} shell pm list packages -f | cut -f 2 -d ":" | grep -E "/system/(app|priv-app)/" | rev | cut -f 1 -d "=" | rev', shell=True)
        elif appType == "all":
            pkgList = subprocess.check_output(f'adb -s {self.deviceID} shell pm list packages | cut -f 2 -d ":"', shell=True)
        pkgList = pkgList.decode("utf-8").splitlines()
        return pkgList

    def get_download_percentage(self, appPkg):
        downloadEles = self.get_ui_element(".//node[@index='2']", 2)
        for ele in downloadEles:
            if '%' in ele.attrib['content-desc']:
                print(f"\rDownloading {appPkg}: {ele.attrib['content-desc']}", end="")
                return int(ele.attrib['content-desc'].replace('%', ''))
        while True:
            uninstallEles = self.get_ui_element(".//node[@content-desc='Uninstall']", 2)
            time.sleep(1)
            if len(uninstallEles) > 0:
                print(f"\rDownloading {appPkg}: 100", end="")
                return 100

    def wait_for_download(self, appPkg):
        downTimer = 10
        # while self.get_download_percentage(appPkg) < 70:
            # continue
        print("Downloading...")
        while appPkg not in self.get_installed_pkgs("user"):
            if downTimer <= 0:
                return "DownloadError"
            time.sleep(downTimer)
            downTimer -= 1
        
        installRetry = 3
        print("Installing...")
        while True:
            cancelEles = self.get_ui_element(".//node[@content-desc='Cancel']", 1)
            if len(cancelEles) == 0 or cancelEles is None:
                break
            if installRetry <= 0:
                return "InstallError"
            installRetry -= 1
            time.sleep(3)

        return True
    
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
    
    def pull_apk(self, appPkg, appDir):
        os.system(f"mkdir -p {appDir}")
        os.system(f"adb -s {self.deviceID} pull $(adb -s {self.deviceID} shell pm path {appPkg} | cut -d ':' -f 2) {appDir}")

if __name__ == "__main__":
    adbDevice = adbUI("931AY05A0C", "tmp/scrn.xml")
    adbDevice.install_app("ai.botify.app")
    # from IPython import embed
    # embed()