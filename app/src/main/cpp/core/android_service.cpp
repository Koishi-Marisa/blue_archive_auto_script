#include "core/android_service.h"

#include <android/log.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "BaasCore", __VA_ARGS__)

namespace baas {

JavaVM* AndroidService::javaVm_ = nullptr;
jobject AndroidService::context_ = nullptr;

void AndroidService::init(JNIEnv* env, jobject context) {
    env->GetJavaVM(&javaVm_);
    context_ = env->NewGlobalRef(context);
    LOGI("AndroidService initialized");
}

JNIEnv* AndroidService::attachEnv() {
    if (!javaVm_) return nullptr;
    JNIEnv* env = nullptr;
    jint ret = javaVm_->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);
    if (ret == JNI_EDETACHED) {
        javaVm_->AttachCurrentThread(&env, nullptr);
    }
    return env;
}

std::vector<uint8_t> AndroidService::screenshotJpeg() {
    JNIEnv* env = attachEnv();
    if (!env) return {};

    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) return {};
    jmethodID method = env->GetStaticMethodID(bridgeClass, "screenshotJpeg", "()[B");
    if (!method) {
        env->DeleteLocalRef(bridgeClass);
        return {};
    }
    jbyteArray array = static_cast<jbyteArray>(env->CallStaticObjectMethod(bridgeClass, method));
    env->DeleteLocalRef(bridgeClass);

    if (!array) return {};
    jsize len = env->GetArrayLength(array);
    std::vector<uint8_t> jpeg(static_cast<size_t>(len));
    env->GetByteArrayRegion(array, 0, len, reinterpret_cast<jbyte*>(jpeg.data()));
    env->DeleteLocalRef(array);
    return jpeg;
}

std::pair<int, int> AndroidService::screenSize() {
    JNIEnv* env = attachEnv();
    if (!env) return {0, 0};

    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) return {0, 0};
    jmethodID method = env->GetStaticMethodID(bridgeClass, "getScreenSize", "()Ljava/lang/String;");
    if (!method) {
        env->DeleteLocalRef(bridgeClass);
        return {0, 0};
    }
    jstring result = static_cast<jstring>(env->CallStaticObjectMethod(bridgeClass, method));
    env->DeleteLocalRef(bridgeClass);

    if (!result) return {0, 0};
    const char* cstr = env->GetStringUTFChars(result, nullptr);
    std::string s(cstr ? cstr : "");
    if (cstr) env->ReleaseStringUTFChars(result, cstr);
    env->DeleteLocalRef(result);

    size_t comma = s.find(',');
    if (comma == std::string::npos) return {0, 0};
    return {std::stoi(s.substr(0, comma)), std::stoi(s.substr(comma + 1))};
}

bool AndroidService::click(int x, int y) {
    JNIEnv* env = attachEnv();
    if (!env) return false;
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

bool AndroidService::swipe(int x1, int y1, int x2, int y2, int durationMs) {
    JNIEnv* env = attachEnv();
    if (!env) return false;
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

bool AndroidService::longClick(int x, int y, int durationMs) {
    JNIEnv* env = attachEnv();
    if (!env) return false;
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

std::string AndroidService::ocr(const std::vector<uint8_t>& jpeg, const std::string& language, const std::string& candidates) {
    JNIEnv* env = attachEnv();
    if (!env || jpeg.empty()) return {};

    jclass bridgeClass = env->FindClass("top/qwq123/baas/bridge/BaasBridge");
    if (!bridgeClass) return {};
    jmethodID method = env->GetStaticMethodID(bridgeClass, "ocr",
                                              "([BLjava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
    if (!method) {
        env->DeleteLocalRef(bridgeClass);
        return {};
    }

    jbyteArray array = env->NewByteArray(static_cast<jsize>(jpeg.size()));
    env->SetByteArrayRegion(array, 0, static_cast<jsize>(jpeg.size()),
                            reinterpret_cast<const jbyte*>(jpeg.data()));
    jstring lang = env->NewStringUTF(language.c_str());
    jstring cands = env->NewStringUTF(candidates.c_str());

    jstring result = static_cast<jstring>(env->CallStaticObjectMethod(bridgeClass, method, array, lang, cands));

    env->DeleteLocalRef(array);
    env->DeleteLocalRef(lang);
    env->DeleteLocalRef(cands);
    env->DeleteLocalRef(bridgeClass);

    if (!result) return {};
    const char* cstr = env->GetStringUTFChars(result, nullptr);
    std::string out(cstr ? cstr : "");
    if (cstr) env->ReleaseStringUTFChars(result, cstr);
    env->DeleteLocalRef(result);
    return out;
}

std::vector<uint8_t> AndroidService::loadAsset(const std::string& path) {
    JNIEnv* env = attachEnv();
    if (!env || !context_) return {};

    jclass contextClass = env->GetObjectClass(context_);
    jmethodID getAssets = env->GetMethodID(contextClass, "getAssets", "()Landroid/content/res/AssetManager;");
    jobject assetManager = env->CallObjectMethod(context_, getAssets);

    jclass assetManagerClass = env->FindClass("android/content/res/AssetManager");
    jmethodID open = env->GetMethodID(assetManagerClass, "open", "(Ljava/lang/String;)Ljava/io/InputStream;");
    jstring jpath = env->NewStringUTF(path.c_str());
    jobject inputStream = env->CallObjectMethod(assetManager, open, jpath);
    env->DeleteLocalRef(jpath);

    std::vector<uint8_t> result;
    if (inputStream) {
        jclass inputStreamClass = env->FindClass("java/io/InputStream");
        jmethodID read = env->GetMethodID(inputStreamClass, "read", "([B)I");
        jmethodID close = env->GetMethodID(inputStreamClass, "close", "()V");
        jbyteArray buffer = env->NewByteArray(8192);

        while (true) {
            jint len = env->CallIntMethod(inputStream, read, buffer);
            if (len <= 0) break;
            std::vector<jbyte> tmp(static_cast<size_t>(len));
            env->GetByteArrayRegion(buffer, 0, len, tmp.data());
            result.insert(result.end(), tmp.begin(), tmp.end());
        }

        env->CallVoidMethod(inputStream, close);
        env->DeleteLocalRef(buffer);
        env->DeleteLocalRef(inputStream);
        env->DeleteLocalRef(inputStreamClass);
    }

    env->DeleteLocalRef(assetManager);
    env->DeleteLocalRef(assetManagerClass);
    env->DeleteLocalRef(contextClass);
    return result;
}

} // namespace baas
