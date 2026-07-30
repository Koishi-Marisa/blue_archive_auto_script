import time
from datetime import datetime


def implement(self):
    if not self.is_android_device:
        return True
    # When using the in-process Android bridge there is no uiautomator2.
    # We cannot query the current package via ADB, so we just ensure the
    # game is started and return to the main page.
    if getattr(self.config, 'screenshot_method', None) == 'android' or \
            getattr(self.config, 'control_method', None) == 'android':
        self.logger.info("Using Android bridge, skip ADB restart check")
        start(self)
        return True
    cur_package = self.u2.app_current()['package']
    if cur_package != self.package_name:
        if cur_package != self.package_name:
            self.logger.warning("APP NOT RUNNING current package: " + cur_package)
        start(self)
        return True
    self.logger.info("CHECK RESTART")
    if check_need_restart(self):
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.u2.app_stop(self.package_name)
        time.sleep(2)
        start(self)
        return True
    return True


def start(self):
    self.logger.info("-- START BLUE ARCHIVE --")
    # Android bridge mode: rely on the game already being in the foreground
    # (the user is expected to launch it before starting BAAS). Just return
    # to the main page using taps.
    if getattr(self.config, 'screenshot_method', None) == 'android' or \
            getattr(self.config, 'control_method', None) == 'android':
        self.to_main_page()
        return
    activity_name = self.activity_name
    if self.server == 'CN':
        activity_name = None
    self.u2.app_start(self.package_name, activity_name)
    self.to_main_page()


def check_need_restart(self):
    now = datetime.now()
    if self.server == 'CN':
        if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=4).timestamp()) <= 60:
            return True
    elif self.server == 'Global' or self.server == 'JP':
        if abs(time.time() - datetime(year=now.year, month=now.month, day=now.day, hour=3).timestamp()) <= 60:
            return True
    return False
