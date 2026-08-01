import json
import os
import sys

from core.ocr import ocr
from core.utils import Logger
from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet
from core.ocr.baas_ocr_client.server_installer import check_git


def _is_android():
    return sys.platform == 'android' or os.environ.get('P4A_BOOTSTRAP') is not None


class Main:
    def __init__(self, logger_signal=None, ocr_needed=None):
        self.ocr_needed = ocr_needed
        self.ocr = None
        self.logger = Logger(logger_signal)
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        self.logger.info(self.project_dir)
        self.init_all_data()
        self.threads = {}

    def init_all_data(self):
        if not self.init_ocr():
            self.logger.error("Ocr Init Incomplete Please restart .")
            return
        self.init_static_config()
        self.logger.info("-- All Data Initialization Complete Script ready--")

    def init_ocr(self):
        if _is_android():
            self.logger.info("Android environment detected, using on-device OCR.")
            try:
                from core.ocr.android_ocr import AndroidOcr
                self.ocr = AndroidOcr(self.logger)
                return True
            except Exception as e:
                self.logger.error(f"Android OCR init failed: {e}")
                return False

        try:
            check_git(self.logger)
        except Exception as e:
            self.logger.error("OCR Update Failed.")
            import traceback
            self.logger.error(traceback.format_exc())
            self.logger.info("Try to Start OCR Server Without Update.")

        try:
            self.ocr = ocr.Baas_ocr(logger=self.logger, ocr_needed=self.ocr_needed)
            self.ocr.client.start_server()
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def get_thread(
            self,
            config,
            name="1",
            logger_signal=None,
            button_signal=None,
            update_signal=None,
            exit_signal=None
    ):
        t = Baas_thread(config, logger_signal, button_signal, update_signal, exit_signal)
        t.set_ocr(self.ocr)
        self.threads.setdefault(name, t)
        return t

    def stop_script(self, name):
        if name in self.threads:
            self.threads[name].flag_run = False
            del self.threads[name]
            return True
        else:
            return False

    def init_static_config(self):
        try:
            self.static_config = self.operate_dict(
                json.load(open(self.project_dir + "/config/static.json", 'r', encoding='utf-8')))
            return True
        except Exception as e:
            self.logger.error("Static Config initialization failed")
            self.logger.error(e.__str__())
            return False

    def operate_dict(self, dic):
        for key in dic:
            if type(dic[key]) is dict:
                dic[key] = self.operate_dict(dic[key])
            else:
                dic[key] = self.operate_item(dic[key])
        return dic

    def is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def operate_item(self, item):
        if type(item) is int or type(item) is bool or type(item) is float or item is None:
            return item
        if type(item) is str:
            if item.isdigit():
                return int(item)
            elif self.is_float(item):
                return float(item)
            else:
                if item.count(",") == 2:
                    temp = item.split(",")
                    for j in range(0, len(temp)):
                        if temp[j].isdigit():
                            temp[j] = int(temp[j])
                    item = temp
                return item
        else:
            temp = []
            for i in range(0, len(item)):
                if type(item[i]) is dict:
                    temp.append(self.operate_dict(item[i]))
                else:
                    temp.append(self.operate_item(item[i]))
            return temp
