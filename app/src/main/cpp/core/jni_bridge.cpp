#include "core/baas_core.h"

#include <android/log.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "BaasCore", __VA_ARGS__)

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
    std::string value = baas::BaasCore::instance().getConfigValue(k);
    return env->NewStringUTF(value.c_str());
}

JNIEXPORT jbyteArray JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeScreenshot(JNIEnv* env, jclass /*clazz*/) {
    auto jpeg = baas::BaasCore::instance().screenshot();
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
    return baas::BaasCore::instance().click(static_cast<int>(x), static_cast<int>(y)) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeSwipe(JNIEnv* /*env*/, jclass /*clazz*/,
                                                       jint x1, jint y1, jint x2, jint y2, jint durationMs) {
    return baas::BaasCore::instance().swipe(static_cast<int>(x1), static_cast<int>(y1),
                                            static_cast<int>(x2), static_cast<int>(y2),
                                            static_cast<int>(durationMs)) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jboolean JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeLongClick(JNIEnv* /*env*/, jclass /*clazz*/,
                                                           jint x, jint y, jint durationMs) {
    return baas::BaasCore::instance().longClick(static_cast<int>(x), static_cast<int>(y),
                                                static_cast<int>(durationMs)) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeFindTemplate(JNIEnv* env, jclass /*clazz*/,
                                                              jbyteArray templateJpeg, jdouble threshold) {
    jsize len = env->GetArrayLength(templateJpeg);
    std::vector<uint8_t> templ(static_cast<size_t>(len));
    env->GetByteArrayRegion(templateJpeg, 0, len, reinterpret_cast<jbyte*>(templ.data()));

    auto result = baas::BaasCore::instance().findTemplate(templ, static_cast<double>(threshold));
    char buf[256];
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
    return baas::BaasCore::instance().rgbInRange(static_cast<int>(x), static_cast<int>(y),
                                                  static_cast<int>(rMin), static_cast<int>(rMax),
                                                  static_cast<int>(gMin), static_cast<int>(gMax),
                                                  static_cast<int>(bMin), static_cast<int>(bMax))
               ? JNI_TRUE
               : JNI_FALSE;
}

JNIEXPORT jstring JNICALL
Java_top_qwq123_baas_bridge_BaasCoreNative_nativeGetVersion(JNIEnv* env, jclass /*clazz*/) {
    return env->NewStringUTF("0.1.0-cpp");
}

} // extern "C"
