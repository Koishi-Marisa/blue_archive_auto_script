#pragma once

#include <jni.h>
#include <cstdint>
#include <string>
#include <vector>

namespace baas {

// Callbacks into the Java-side BaasBridge for Android-specific services.
class AndroidService {
public:
    static void init(JNIEnv* env, jobject context);
    static JNIEnv* attachEnv();

    static std::vector<uint8_t> screenshotJpeg();
    static std::pair<int, int> screenSize();

    static bool click(int x, int y);
    static bool swipe(int x1, int y1, int x2, int y2, int durationMs);
    static bool longClick(int x, int y, int durationMs);

    // OCR on a JPEG region; language e.g. "en-us", "zh-cn".
    static std::string ocr(const std::vector<uint8_t>& jpeg, const std::string& language, const std::string& candidates);

    // Load an asset file as bytes.
    static std::vector<uint8_t> loadAsset(const std::string& path);

private:
    static JavaVM* javaVm_;
    static jobject context_;
};

} // namespace baas
