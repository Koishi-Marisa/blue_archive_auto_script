# -*- coding: utf-8 -*-
"""
OCR wrapper for Android.

This replaces the PC BAAS OCR server with the native ML Kit OCR exposed
through core.device.android_bridge. It implements the subset of the
Baas_ocr interface used by BAAS tasks.
"""
from core.device.android_bridge import ocr as bridge_ocr


class _DummyClientConfig:
    server_is_remote = True


class _DummyClient:
    config = _DummyClientConfig()

    def create_shared_memory(self, *args, **kwargs):
        pass

    def release_shared_memory(self, *args, **kwargs):
        pass


class AndroidOcr:
    def __init__(self, logger=None):
        self.logger = logger
        self.client = _DummyClient()

    @staticmethod
    def _get_area_img(img, area, ratio=1.0):
        return img[int(area[1] * ratio):int(area[3] * ratio),
                   int(area[0] * ratio):int(area[2] * ratio)]

    def get_region_res(self, baas, region, language='zh-cn', log_info="", candidates="", filter_score=0.2):
        img = self._get_area_img(baas.latest_img_array, region, baas.ratio)
        return self.ocr_for_single_line(language, log_info, img, candidates, filter_score=filter_score)

    def get_region_raw_res(self, img, region, language='zh-cn', ratio=1.0, candidates=""):
        img = self._get_area_img(img, region, ratio)
        return self.ocr_for_single_line(language, "", img, candidates)

    def recognize_int(self, baas, region, log_info="", filter_score=0.2) -> int:
        res = self.get_region_res(baas, region, language="en-us", log_info=log_info,
                                  candidates="0123456789", filter_score=filter_score)
        result = 0
        for ch in res:
            if ch.isdigit():
                result = result * 10 + int(ch)
        return result

    def get_region_pure_english(self, baas, region, log_info="", filter_score=0.2):
        res = self.get_region_res(baas, region, language="en-us", log_info=log_info,
                                  candidates="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                                  filter_score=filter_score)
        return res

    def get_region_pure_chinese(self, baas, region, log_info="", filter_score=0.2):
        res = self.get_region_res(baas, region, language="zh-cn", log_info=log_info, filter_score=filter_score)
        return "".join(ch for ch in res if self._is_chinese_char(ch))

    @staticmethod
    def _is_chinese_char(char):
        return 0x4e00 <= ord(char) <= 0x9fff

    def ocr_for_single_line(self, language, log_info, origin_image, candidates="", pass_method=1,
                            local_path="", shared_memory_name="", _logger=None, filter_score=0.2):
        try:
            results = bridge_ocr(origin_image, language=language)
        except Exception as e:
            if _logger is not None:
                _logger.warning(f"Android OCR failed: {e}")
            return ""
        if not results:
            return ""
        texts = []
        # Sort left-to-right to form a line.
        results = sorted(results, key=lambda r: min(p[0] for p in r.get("box", [])))
        for item in results:
            text = item.get("text", "")
            if candidates:
                text = "".join(ch for ch in text if ch in candidates)
            texts.append(text)
        return "".join(texts)

    # The following methods are called by Baas_thread but are no-ops when
    # OCR runs on-device through ML Kit.
    def init_baas_model(self, *args, **kwargs):
        pass

    def test_models(self, *args, **kwargs):
        pass

    def create_shared_memory(self, *args, **kwargs):
        pass

    def release_shared_memory(self, *args, **kwargs):
        pass

    def enable_thread_pool(self, *args, **kwargs):
        pass
