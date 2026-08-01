#include "core/feature.h"

#include "core/baas_core.h"
#include "core/android_service.h"

#include <android/log.h>
#include <cmath>

#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "BaasCore", __VA_ARGS__)

namespace baas {

Feature::Feature(const std::string& name, const Config& config) : name_(name), config_(config) {}

RgbRangeFeature::RgbRangeFeature(const std::string& name, const Config& config)
    : Feature(name, config) {}

bool RgbRangeFeature::appear(const BaasCore& baas, Config& output) {
    int x = config_.getInt("x");
    int y = config_.getInt("y");
    int rMin = config_.getInt("r_min");
    int rMax = config_.getInt("r_max");
    int gMin = config_.getInt("g_min");
    int gMax = config_.getInt("g_max");
    int bMin = config_.getInt("b_min");
    int bMax = config_.getInt("b_max");

    auto img = baas.latestScreenshot();
    if (!img || img->empty()) return false;
    if (x < 0 || x >= img->width() || y < 0 || y >= img->height()) return false;

    bool ok = img->r(x, y) >= rMin && img->r(x, y) <= rMax &&
              img->g(x, y) >= gMin && img->g(x, y) <= gMax &&
              img->b(x, y) >= bMin && img->g(x, y) <= bMax;
    if (ok) {
        output.setInt("x", x);
        output.setInt("y", y);
    }
    return ok;
}

TemplateMatchFeature::TemplateMatchFeature(const std::string& name, const Config& config)
    : Feature(name, config) {}

std::shared_ptr<ImageBuffer> TemplateMatchFeature::loadTemplate(const BaasCore& baas) const {
    std::string path = config_.getString("template");
    if (path.empty()) return nullptr;

    auto jpeg = AndroidService::loadAsset(path);
    if (jpeg.empty()) {
        LOGE("TemplateMatchFeature: failed to load asset %s", path.c_str());
        return nullptr;
    }
    JNIEnv* env = AndroidService::attachEnv();
    jobject ctx = nullptr; // AndroidService does not expose context; fromJpeg only uses env for BitmapFactory.
    return ImageBuffer::fromJpeg(env, ctx, jpeg);
}

bool TemplateMatchFeature::appear(const BaasCore& baas, Config& output) {
    auto source = baas.latestScreenshot();
    if (!source || source->empty()) return false;

    auto templ = loadTemplate(baas);
    if (!templ || templ->empty()) return false;

    double threshold = config_.getDouble("threshold", 0.7);
    auto result = matchTemplate(*source, *templ, threshold);
    if (result.found) {
        output.setInt("x", result.point.x);
        output.setInt("y", result.point.y);
        output.setDouble("score", result.score);
    }
    return result.found;
}

} // namespace baas
