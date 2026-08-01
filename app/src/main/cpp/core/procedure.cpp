#include "core/procedure.h"

#include <android/log.h>
#include <chrono>
#include <thread>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)

namespace baas {

AppearThenClickProcedure::AppearThenClickProcedure(
    const std::string& featureName,
    int clickX,
    int clickY,
    int timeoutMs,
    int intervalMs)
    : featureName_(featureName), clickX_(clickX), clickY_(clickY),
      timeoutMs_(timeoutMs), intervalMs_(intervalMs) {}

bool AppearThenClickProcedure::execute(BaasCore& baas) {
    auto start = std::chrono::steady_clock::now();
    Config output;

    while (baas.isRunning()) {
        baas.updateScreenshot();
        if (baas.featureAppear(featureName_, output)) {
            LOGI("AppearThenClick: feature %s appeared, click (%d,%d)",
                 featureName_.c_str(), clickX_, clickY_);
            baas.click(clickX_, clickY_, featureName_);
            return true;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(intervalMs_));

        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start).count();
        if (elapsed > timeoutMs_) {
            LOGI("AppearThenClick: timeout waiting for %s", featureName_.c_str());
            return false;
        }
    }
    return false;
}

} // namespace baas
