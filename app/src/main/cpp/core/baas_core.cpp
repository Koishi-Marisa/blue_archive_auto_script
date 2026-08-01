#include "core/baas_core.h"
#include "core/image.h"

#include <android/log.h>
#include <cstdlib>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "BaasCore", __VA_ARGS__)

namespace baas {

BaasCore& BaasCore::instance() {
    static BaasCore core;
    return core;
}

void BaasCore::init(JNIEnv* env, jobject android_context) {
    std::lock_guard<std::mutex> lock(mutex_);
    env->GetJavaVM(&javaVm_);
    context_ = env->NewGlobalRef(android_context);
    initialized_ = true;
    LOGI("BaasCore initialized");
}

bool BaasCore::isInitialized() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return initialized_;
}

JNIEnv* BaasCore::attachEnv() {
    if (!javaVm_) return nullptr;
    JNIEnv* env = nullptr;
    jint ret = javaVm_->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);
    if (ret == JNI_EDETACHED) {
        javaVm_->AttachCurrentThread(&env, nullptr);
    }
    return env;
}

bool BaasCore::loadConfig(const std::string& jsonConfig) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_.clear();
    // Minimal parser: expects simple "key": "value" or "key": number entries.
    size_t pos = 0;
    while (pos < jsonConfig.size()) {
        size_t keyStart = jsonConfig.find('"', pos);
        if (keyStart == std::string::npos) break;
        size_t keyEnd = jsonConfig.find('"', keyStart + 1);
        if (keyEnd == std::string::npos) break;
        std::string key = jsonConfig.substr(keyStart + 1, keyEnd - keyStart - 1);

        size_t colon = jsonConfig.find(':', keyEnd);
        if (colon == std::string::npos) break;
        size_t valueStart = jsonConfig.find_first_not_of(" \t\n\r", colon + 1);
        if (valueStart == std::string::npos) break;

        std::string value;
        if (jsonConfig[valueStart] == '"') {
            size_t valueEnd = jsonConfig.find('"', valueStart + 1);
            if (valueEnd == std::string::npos) break;
            value = jsonConfig.substr(valueStart + 1, valueEnd - valueStart - 1);
            pos = valueEnd + 1;
        } else {
            size_t valueEnd = jsonConfig.find_first_of(",}\n", valueStart);
            if (valueEnd == std::string::npos) valueEnd = jsonConfig.size();
            value = jsonConfig.substr(valueStart, valueEnd - valueStart);
            // trim
            size_t first = value.find_first_not_of(" \t\r");
            size_t last = value.find_last_not_of(" \t\r");
            if (first != std::string::npos) {
                value = value.substr(first, last - first + 1);
            }
            pos = valueEnd;
        }
        config_.emplace_back(key, value);
    }
    LOGI("loadConfig: loaded %zu entries", config_.size());
    return true;
}

std::string BaasCore::getConfigValue(const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& kv : config_) {
        if (kv.first == key) return kv.second;
    }
    return "";
}

std::vector<uint8_t> BaasCore::screenshot() {
    std::lock_guard<std::mutex> lock(mutex_);
    JNIEnv* env = attachEnv();
    if (!initialized_ || !env) {
        LOGE("screenshot: not initialized");
        return {};
    }

    // Call BaasBridge.screenshotJpeg() via JNI.
    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) {
        LOGE("screenshot: BaasBridge class not found");
        return {};
    }
    jmethodID method = env->GetStaticMethodID(bridgeClass, "screenshotJpeg", "()[B");
    if (!method) {
        LOGE("screenshot: screenshotJpeg method not found");
        env->DeleteLocalRef(bridgeClass);
        return {};
    }
    jbyteArray array = static_cast<jbyteArray>(env->CallStaticObjectMethod(bridgeClass, method));
    env->DeleteLocalRef(bridgeClass);

    if (!array) {
        LOGE("screenshot: BaasBridge.screenshotJpeg returned null");
        return {};
    }

    jsize len = env->GetArrayLength(array);
    std::vector<uint8_t> jpeg(static_cast<size_t>(len));
    env->GetByteArrayRegion(array, 0, len, reinterpret_cast<jbyte*>(jpeg.data()));
    env->DeleteLocalRef(array);

    lastScreenshot_ = ImageBuffer::fromJpeg(env, context_, jpeg);
    return jpeg;
}

std::pair<int, int> BaasCore::screenshotSize() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (lastScreenshot_ && !lastScreenshot_->empty()) {
        return {lastScreenshot_->width(), lastScreenshot_->height()};
    }
    return {0, 0};
}

bool BaasCore::click(int x, int y) {
    JNIEnv* env = attachEnv();
    if (!initialized_ || !env) return false;
    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) return false;
    jmethodID method = env->GetStaticMethodID(bridgeClass, "click", "(II)Z");
    if (!method) {
        env->DeleteLocalRef(bridgeClass);
        return false;
    }
    jboolean ok = env->CallStaticBooleanMethod(bridgeClass, method, x, y);
    env->DeleteLocalRef(bridgeClass);
    return ok;
}

bool BaasCore::swipe(int x1, int y1, int x2, int y2, int durationMs) {
    JNIEnv* env = attachEnv();
    if (!initialized_ || !env) return false;
    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) return false;
    jmethodID method = env->GetStaticMethodID(bridgeClass, "swipe", "(IIIII)Z");
    if (!method) {
        env->DeleteLocalRef(bridgeClass);
        return false;
    }
    jboolean ok = env->CallStaticBooleanMethod(bridgeClass, method, x1, y1, x2, y2, durationMs);
    env->DeleteLocalRef(bridgeClass);
    return ok;
}

bool BaasCore::longClick(int x, int y, int durationMs) {
    JNIEnv* env = attachEnv();
    if (!initialized_ || !env) return false;
    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) return false;
    jmethodID method = env->GetStaticMethodID(bridgeClass, "longClick", "(III)Z");
    if (!method) {
        env->DeleteLocalRef(bridgeClass);
        return false;
    }
    jboolean ok = env->CallStaticBooleanMethod(bridgeClass, method, x, y, durationMs);
    env->DeleteLocalRef(bridgeClass);
    return ok;
}

MatchResult BaasCore::findTemplate(const std::vector<uint8_t>& templateJpeg, double threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    JNIEnv* env = attachEnv();
    MatchResult result;
    if (!lastScreenshot_ || lastScreenshot_->empty()) {
        LOGE("findTemplate: no screenshot available");
        return result;
    }
    auto templ = ImageBuffer::fromJpeg(env, context_, templateJpeg);
    if (!templ || templ->empty()) {
        LOGE("findTemplate: failed to decode template");
        return result;
    }
    return matchTemplate(*lastScreenshot_, *templ, threshold);
}

bool BaasCore::rgbInRange(int x, int y, int rMin, int rMax, int gMin, int gMax, int bMin, int bMax) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!lastScreenshot_ || lastScreenshot_->empty()) return false;
    if (x < 0 || x >= lastScreenshot_->width() || y < 0 || y >= lastScreenshot_->height()) return false;
    uint8_t r = lastScreenshot_->r(x, y);
    uint8_t g = lastScreenshot_->g(x, y);
    uint8_t b = lastScreenshot_->b(x, y);
    return r >= rMin && r <= rMax && g >= gMin && g <= gMax && b >= bMin && b <= bMax;
}

void BaasCore::setLastOcrResult(const std::string& json) {
    std::lock_guard<std::mutex> lock(mutex_);
    lastOcrResult_ = json;
}

std::string BaasCore::getLastOcrResult() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return lastOcrResult_;
}

} // namespace baas
