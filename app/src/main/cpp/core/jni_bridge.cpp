#include "core/baas_core.h"
#include "core/android_service.h"
#include "core/feature.h"
#include "core/procedure.h"

#include <android/log.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)

extern "C" {

JNIEXPORT void JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeInit(JNIEnv* env, jclass /*clazz*/, jobject context) {
    baas::BaasCore::instance().init(env, context);
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeLoadConfig(JNIEnv* env, jclass /*clazz*/, jstring json) {
    const char* cstr = env->GetStringUTFChars(json, nullptr);
    std::string config(cstr ? cstr : "");
    if (cstr) env->ReleaseStringUTFChars(json, cstr);
    return baas::BaasCore::instance().loadConfig(config) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeGetConfigValue(JNIEnv* env, jclass /*clazz*/, jstring key) {
    const char* cstr = env->GetStringUTFChars(key, nullptr);
    std::string k(cstr ? cstr : "");
    if (cstr) env->ReleaseStringUTFChars(key, cstr);
    std::string value = baas::BaasCore::instance().config().getString(k);
    return env->NewStringUTF(value.c_str());
}

JNIEXPORT void JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeUpdateScreenshot(JNIEnv* /*env*/, jclass /*clazz*/) {
    baas::BaasCore::instance().updateScreenshot();
}

JNIEXPORT jbyteArray JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeScreenshot(JNIEnv* env, jclass /*clazz*/) {
    auto img = baas::BaasCore::instance().latestScreenshot();
    if (!img || img->empty()) return nullptr;
    auto jpeg = img->toJpeg(env, 95);
    if (jpeg.empty()) return nullptr;
    jbyteArray result = env->NewByteArray(static_cast<jsize>(jpeg.size()));
    env->SetByteArrayRegion(result, 0, static_cast<jsize>(jpeg.size()),
                            reinterpret_cast<const jbyte*>(jpeg.data()));
    return result;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeScreenshotSize(JNIEnv* env, jclass /*clazz*/) {
    auto [w, h] = baas::BaasCore::instance().screenshotSize();
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%d,%d", w, h);
    return env->NewStringUTF(buf);
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeClick(JNIEnv* /*env*/, jclass /*clazz*/, jint x, jint y) {
    baas::BaasCore::instance().click(static_cast<int>(x), static_cast<int>(y));
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeSwipe(JNIEnv* /*env*/, jclass /*clazz*/,
                                                       jint x1, jint y1, jint x2, jint y2, jint durationMs) {
    baas::BaasCore::instance().swipe(static_cast<int>(x1), static_cast<int>(y1),
                                     static_cast<int>(x2), static_cast<int>(y2),
                                     static_cast<int>(durationMs));
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeLongClick(JNIEnv* /*env*/, jclass /*clazz*/,
                                                           jint x, jint y, jint durationMs) {
    baas::BaasCore::instance().longClick(static_cast<int>(x), static_cast<int>(y),
                                         static_cast<int>(durationMs));
    return JNI_TRUE;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeFindTemplate(JNIEnv* env, jclass /*clazz*/,
                                                              jbyteArray templateJpeg, jdouble threshold) {
    auto source = baas::BaasCore::instance().latestScreenshot();
    jsize len = env->GetArrayLength(templateJpeg);
    std::vector<uint8_t> templBytes(static_cast<size_t>(len));
    env->GetByteArrayRegion(templateJpeg, 0, len, reinterpret_cast<jbyte*>(templBytes.data()));
    auto templ = baas::ImageBuffer::fromJpeg(env, nullptr, templBytes);

    char buf[256];
    if (!source || source->empty() || !templ || templ->empty()) {
        std::snprintf(buf, sizeof(buf), R"({"found":false,"x":0,"y":0,"score":0})");
        return env->NewStringUTF(buf);
    }

    auto result = baas::matchTemplate(*source, *templ, static_cast<double>(threshold));
    if (result.found) {
        std::snprintf(buf, sizeof(buf), R"({"found":true,"x":%d,"y":%d,"score":%.4f})",
                      result.point.x, result.point.y, result.score);
    } else {
        std::snprintf(buf, sizeof(buf), R"({"found":false,"x":0,"y":0,"score":%.4f})", result.score);
    }
    return env->NewStringUTF(buf);
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeRgbInRange(JNIEnv* /*env*/, jclass /*clazz*/,
                                                            jint x, jint y,
                                                            jint rMin, jint rMax,
                                                            jint gMin, jint gMax,
                                                            jint bMin, jint bMax) {
    auto img = baas::BaasCore::instance().latestScreenshot();
    if (!img || img->empty()) return JNI_FALSE;
    if (x < 0 || x >= img->width() || y < 0 || y >= img->height()) return JNI_FALSE;
    bool ok = img->r(x, y) >= rMin && img->r(x, y) <= rMax &&
              img->g(x, y) >= gMin && img->g(x, y) <= gMax &&
              img->b(x, y) >= bMin && img->b(x, y) <= bMax;
    return ok ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeOcr(JNIEnv* env, jclass /*clazz*/,
                                                     jint x, jint y, jint w, jint h,
                                                     jstring language, jstring candidates) {
    const char* langCstr = env->GetStringUTFChars(language, nullptr);
    std::string lang(langCstr ? langCstr : "en-us");
    if (langCstr) env->ReleaseStringUTFChars(language, langCstr);

    const char* candCstr = env->GetStringUTFChars(candidates, nullptr);
    std::string cands(candCstr ? candCstr : "");
    if (candCstr) env->ReleaseStringUTFChars(candidates, candCstr);

    baas::Rect region{x, y, w, h};
    std::string text = baas::BaasCore::instance().ocr(region, lang, cands);
    return env->NewStringUTF(text.c_str());
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeRegisterFeature(JNIEnv* env, jclass /*clazz*/,
                                                                 jstring name, jstring type, jstring jsonConfig) {
    const char* nameCstr = env->GetStringUTFChars(name, nullptr);
    std::string featureName(nameCstr ? nameCstr : "");
    if (nameCstr) env->ReleaseStringUTFChars(name, nameCstr);

    const char* typeCstr = env->GetStringUTFChars(type, nullptr);
    std::string featureType(typeCstr ? typeCstr : "");
    if (typeCstr) env->ReleaseStringUTFChars(type, typeCstr);

    const char* jsonCstr = env->GetStringUTFChars(jsonConfig, nullptr);
    std::string json(jsonCstr ? jsonCstr : "");
    if (jsonCstr) env->ReleaseStringUTFChars(jsonConfig, jsonCstr);

    baas::Config cfg;
    cfg.loadJson(json);

    if (featureType == "rgb_range") {
        baas::BaasCore::instance().registerFeature(featureName, std::make_shared<baas::RgbRangeFeature>(featureName, cfg));
    } else if (featureType == "template") {
        baas::BaasCore::instance().registerFeature(featureName, std::make_shared<baas::TemplateMatchFeature>(featureName, cfg));
    } else {
        return JNI_FALSE;
    }
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeFeatureAppear(JNIEnv* env, jclass /*clazz*/, jstring name) {
    const char* cstr = env->GetStringUTFChars(name, nullptr);
    std::string featureName(cstr ? cstr : "");
    if (cstr) env->ReleaseStringUTFChars(name, cstr);

    baas::Config output;
    return baas::BaasCore::instance().featureAppear(featureName, output) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeAppearThenClick(JNIEnv* env, jclass /*clazz*/,
                                                                 jstring featureName, jint clickX, jint clickY,
                                                                 jint timeoutMs, jint intervalMs) {
    const char* cstr = env->GetStringUTFChars(featureName, nullptr);
    std::string name(cstr ? cstr : "");
    if (cstr) env->ReleaseStringUTFChars(featureName, cstr);

    baas::AppearThenClickProcedure proc(name, clickX, clickY, timeoutMs, intervalMs);
    return proc.execute(baas::BaasCore::instance()) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeGetVersion(JNIEnv* env, jclass /*clazz*/) {
    return env->NewStringUTF("0.3.0-cpp");
}

} // extern "C"
