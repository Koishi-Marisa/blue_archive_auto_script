#pragma once

#include "core/config.h"
#include "core/image.h"
#include "core/feature.h"

#include <jni.h>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace baas {

// Main entry point for the C++ BAAS core, inspired by BAAS_Cpp::BAAS.
// Manages config, screenshot, control, features, and procedures.
class BaasCore {
public:
    static BaasCore& instance();

    void init(JNIEnv* env, jobject context);
    bool isInitialized() const;

    bool loadConfig(const std::string& json);
    Config& config();
    const Config& config() const;

    // Screenshot
    void updateScreenshot();
    std::shared_ptr<ImageBuffer> latestScreenshot() const;
    std::pair<int, int> screenshotSize() const;

    // Control
    void click(int x, int y, const std::string& description = "");
    void swipe(int x1, int y1, int x2, int y2, int durationMs);
    void longClick(int x, int y, int durationMs);

    // Feature recognition
    bool featureAppear(const std::string& featureName, Config& output);
    void registerFeature(const std::string& name, std::shared_ptr<Feature> feature);

    // OCR
    std::string ocr(const Rect& region, const std::string& language, const std::string& candidates = "");
    std::string ocrForSingleLine(const Rect& region, const std::string& language, const std::string& candidates = "");

    // Module registration
    void registerModule(const std::string& name, std::function<bool(BaasCore*)> impl);
    bool solve(const std::string& name);

    inline bool isRunning() const { return flagRun_; }
    inline void stop() { flagRun_ = false; }

private:
    BaasCore() = default;
    ~BaasCore() = default;
    BaasCore(const BaasCore&) = delete;
    BaasCore& operator=(const BaasCore&) = delete;

    mutable std::mutex mutex_;
    bool initialized_ = false;
    bool flagRun_ = true;

    Config config_;
    std::shared_ptr<ImageBuffer> latestScreenshot_;

    std::map<std::string, std::shared_ptr<Feature>> features_;
    std::map<std::string, std::function<bool(BaasCore*)>> modules_;
};

} // namespace baas
