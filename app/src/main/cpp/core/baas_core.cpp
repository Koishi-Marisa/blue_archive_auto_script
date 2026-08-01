#include "core/baas_core.h"
#include "core/android_service.h"

#include <android/log.h>
#include <cstdio>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "BaasCore", __VA_ARGS__)

namespace baas {

BaasCore& BaasCore::instance() {
    static BaasCore core;
    return core;
}

void BaasCore::init(JNIEnv* env, jobject context) {
    std::lock_guard<std::mutex> lock(mutex_);
    AndroidService::init(env, context);
    initialized_ = true;
    LOGI("BaasCore initialized");
}

bool BaasCore::isInitialized() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return initialized_;
}

bool BaasCore::loadConfig(const std::string& json) {
    std::lock_guard<std::mutex> lock(mutex_);
    bool ok = config_.loadJson(json);
    LOGI("loadConfig: %s", ok ? "ok" : "failed");
    return ok;
}

Config& BaasCore::config() {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_;
}

const Config& BaasCore::config() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_;
}

void BaasCore::updateScreenshot() {
    std::lock_guard<std::mutex> lock(mutex_);
    auto jpeg = AndroidService::screenshotJpeg();
    if (jpeg.empty()) {
        LOGE("updateScreenshot: failed to capture screenshot");
        return;
    }
    JNIEnv* env = AndroidService::attachEnv();
    latestScreenshot_ = ImageBuffer::fromJpeg(env, nullptr, jpeg);
    LOGI("updateScreenshot: %dx%d", latestScreenshot_ ? latestScreenshot_->width() : 0,
         latestScreenshot_ ? latestScreenshot_->height() : 0);
}

std::shared_ptr<ImageBuffer> BaasCore::latestScreenshot() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return latestScreenshot_;
}

std::pair<int, int> BaasCore::screenshotSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (latestScreenshot_ && !latestScreenshot_->empty()) {
        return {latestScreenshot_->width(), latestScreenshot_->height()};
    }
    return AndroidService::screenSize();
}

void BaasCore::click(int x, int y, const std::string& description) {
    if (!flagRun_) return;
    if (!description.empty()) LOGI("click %s", description.c_str());
    AndroidService::click(x, y);
}

void BaasCore::swipe(int x1, int y1, int x2, int y2, int durationMs) {
    if (!flagRun_) return;
    AndroidService::swipe(x1, y1, x2, y2, durationMs);
}

void BaasCore::longClick(int x, int y, int durationMs) {
    if (!flagRun_) return;
    AndroidService::longClick(x, y, durationMs);
}

bool BaasCore::featureAppear(const std::string& featureName, Config& output) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = features_.find(featureName);
    if (it == features_.end()) {
        LOGE("featureAppear: feature %s not registered", featureName.c_str());
        return false;
    }
    return it->second->appear(*this, output);
}

void BaasCore::registerFeature(const std::string& name, std::shared_ptr<Feature> feature) {
    std::lock_guard<std::mutex> lock(mutex_);
    features_[name] = feature;
}

std::string BaasCore::ocr(const Rect& region, const std::string& language, const std::string& candidates) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!latestScreenshot_ || latestScreenshot_->empty()) return {};
    auto cropped = latestScreenshot_->crop(region);
    if (!cropped || cropped->empty()) return {};

    JNIEnv* env = AndroidService::attachEnv();
    auto jpeg = cropped->toJpeg(env, 95);
    return AndroidService::ocr(jpeg, language, candidates);
}

std::string BaasCore::ocrForSingleLine(const Rect& region, const std::string& language, const std::string& candidates) {
    return ocr(region, language, candidates);
}

void BaasCore::registerModule(const std::string& name, std::function<bool(BaasCore*)> impl) {
    std::lock_guard<std::mutex> lock(mutex_);
    modules_[name] = impl;
}

bool BaasCore::solve(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = modules_.find(name);
    if (it == modules_.end()) {
        LOGE("solve: module %s not registered", name.c_str());
        return false;
    }
    return it->second(this);
}

} // namespace baas
