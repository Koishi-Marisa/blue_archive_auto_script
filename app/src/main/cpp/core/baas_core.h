#pragma once

#include <jni.h>
#include <string>
#include <vector>
#include <mutex>
#include <memory>

#include "core/image.h"

namespace baas {

class BaasCore {
public:
    static BaasCore& instance();

    void init(JNIEnv* env, jobject android_context);
    bool isInitialized() const;

    // Attach the current thread and return a valid JNIEnv.
    JNIEnv* attachEnv();

    bool loadConfig(const std::string& jsonConfig);
    std::string getConfigValue(const std::string& key) const;

    // Screenshot returns JPEG bytes captured by the active Android service.
    std::vector<uint8_t> screenshot();
    std::pair<int, int> screenshotSize();

    // Inject input events through Shizuku.
    bool click(int x, int y);
    bool swipe(int x1, int y1, int x2, int y2, int durationMs);
    bool longClick(int x, int y, int durationMs);

    // Image matching on the latest screenshot.
    MatchResult findTemplate(const std::vector<uint8_t>& templateJpeg, double threshold);
    bool rgbInRange(int x, int y, int rMin, int rMax, int gMin, int gMax, int bMin, int bMax);

    // OCR is performed on the Java side; this stores the last OCR JSON result.
    void setLastOcrResult(const std::string& json);
    std::string getLastOcrResult() const;

private:
    BaasCore() = default;
    ~BaasCore() = default;
    BaasCore(const BaasCore&) = delete;
    BaasCore& operator=(const BaasCore&) = delete;

    mutable std::mutex mutex_;
    bool initialized_ = false;
    JavaVM* javaVm_ = nullptr;
    jobject context_ = nullptr;

    std::vector<std::pair<std::string, std::string>> config_;
    std::string lastOcrResult_;

    std::shared_ptr<ImageBuffer> lastScreenshot_;
};

} // namespace baas
