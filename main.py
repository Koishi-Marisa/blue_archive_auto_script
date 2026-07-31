from baas_main import Main
from core.config.config_set import ConfigSet
from core.Baas_thread import Baas_thread

if __name__ == '__main__':
    ocr_needed = ["en-us"]
    INSTANCE = Main(ocr_needed=ocr_needed)
    config = ConfigSet(config_dir="global")
    bThread = Baas_thread(config, None, None, None)
    bThread.set_ocr(INSTANCE.ocr)
    bThread.init_all_data()
    bThread.solve("explore_activity_mission")
