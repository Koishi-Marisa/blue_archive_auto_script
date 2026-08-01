#include "core/image.h"

#include <android/bitmap.h>
#include <android/log.h>
#include <cmath>
#include <cstring>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "BaasCore", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "BaasCore", __VA_ARGS__)

namespace baas {

ImageBuffer::ImageBuffer(int width, int height, std::vector<uint8_t> pixels)
    : width_(width), height_(height), pixels_(std::move(pixels)) {
    if (width_ > 0 && height_ > 0 && pixels_.size() != static_cast<size_t>(width_ * height_ * 4)) {
        pixels_.resize(static_cast<size_t>(width_ * height_ * 4), 0);
    }
}

const uint8_t* ImageBuffer::pixel(int x, int y) const {
    if (x < 0 || x >= width_ || y < 0 || y >= height_) return nullptr;
    return &pixels_[(y * width_ + x) * 4];
}

uint8_t* ImageBuffer::pixel(int x, int y) {
    if (x < 0 || x >= width_ || y < 0 || y >= height_) return nullptr;
    return &pixels_[(y * width_ + x) * 4];
}

uint8_t ImageBuffer::r(int x, int y) const {
    auto p = pixel(x, y);
    return p ? p[0] : 0;
}

uint8_t ImageBuffer::g(int x, int y) const {
    auto p = pixel(x, y);
    return p ? p[1] : 0;
}

uint8_t ImageBuffer::b(int x, int y) const {
    auto p = pixel(x, y);
    return p ? p[2] : 0;
}

std::shared_ptr<ImageBuffer> ImageBuffer::fromJpeg(JNIEnv* env, jobject context, const std::vector<uint8_t>& jpeg) {
    if (jpeg.empty()) {
        LOGE("fromJpeg: empty input");
        return nullptr;
    }

    jclass bitmapFactoryClass = env->FindClass("android/graphics/BitmapFactory");
    jmethodID decodeMethod = env->GetStaticMethodID(bitmapFactoryClass, "decodeByteArray",
                                                    "([BII)Landroid/graphics/Bitmap;");
    jbyteArray array = env->NewByteArray(static_cast<jsize>(jpeg.size()));
    env->SetByteArrayRegion(array, 0, static_cast<jsize>(jpeg.size()),
                            reinterpret_cast<const jbyte*>(jpeg.data()));
    jobject bitmap = env->CallStaticObjectMethod(bitmapFactoryClass, decodeMethod, array, 0,
                                                 static_cast<jint>(jpeg.size()));
    env->DeleteLocalRef(array);
    env->DeleteLocalRef(bitmapFactoryClass);

    if (!bitmap) {
        LOGE("fromJpeg: BitmapFactory.decodeByteArray returned null");
        return nullptr;
    }

    AndroidBitmapInfo info;
    if (AndroidBitmap_getInfo(env, bitmap, &info) < 0) {
        LOGE("fromJpeg: AndroidBitmap_getInfo failed");
        env->DeleteLocalRef(bitmap);
        return nullptr;
    }

    void* pixels = nullptr;
    if (AndroidBitmap_lockPixels(env, bitmap, &pixels) < 0) {
        LOGE("fromJpeg: AndroidBitmap_lockPixels failed");
        env->DeleteLocalRef(bitmap);
        return nullptr;
    }

    int width = static_cast<int>(info.width);
    int height = static_cast<int>(info.height);
    std::vector<uint8_t> rgba(static_cast<size_t>(width * height * 4));

    if (info.format == ANDROID_BITMAP_FORMAT_RGBA_8888) {
        std::memcpy(rgba.data(), pixels, rgba.size());
    } else if (info.format == ANDROID_BITMAP_FORMAT_RGB_565) {
        const uint16_t* src = static_cast<const uint16_t*>(pixels);
        for (int i = 0; i < width * height; ++i) {
            uint16_t c = src[i];
            rgba[i * 4 + 0] = static_cast<uint8_t>(((c >> 11) & 0x1F) << 3);
            rgba[i * 4 + 1] = static_cast<uint8_t>(((c >> 5) & 0x3F) << 2);
            rgba[i * 4 + 2] = static_cast<uint8_t>((c & 0x1F) << 3);
            rgba[i * 4 + 3] = 255;
        }
    } else {
        LOGE("fromJpeg: unsupported bitmap format %d", info.format);
        AndroidBitmap_unlockPixels(env, bitmap);
        env->DeleteLocalRef(bitmap);
        return nullptr;
    }

    AndroidBitmap_unlockPixels(env, bitmap);
    env->DeleteLocalRef(bitmap);

    return std::make_shared<ImageBuffer>(width, height, std::move(rgba));
}

std::vector<uint8_t> ImageBuffer::toJpeg(JNIEnv* env, int quality) const {
    std::vector<uint8_t> emptyResult;
    if (empty()) return emptyResult;

    // Create mutable Bitmap from RGBA pixels.
    jclass bitmapClass = env->FindClass("android/graphics/Bitmap");
    jmethodID createBitmap = env->GetStaticMethodID(bitmapClass, "createBitmap",
                                                    "(IILandroid/graphics/Bitmap$Config;)Landroid/graphics/Bitmap;");
    jclass configClass = env->FindClass("android/graphics/Bitmap$Config");
    jfieldID argb8888Field = env->GetStaticFieldID(configClass, "ARGB_8888",
                                                   "Landroid/graphics/Bitmap$Config;");
    jobject argb8888 = env->GetStaticObjectField(configClass, argb8888Field);
    jobject bitmap = env->CallStaticObjectMethod(bitmapClass, createBitmap,
                                                 static_cast<jint>(width_),
                                                 static_cast<jint>(height_), argb8888);
    env->DeleteLocalRef(argb8888);
    env->DeleteLocalRef(configClass);

    void* pixels = nullptr;
    AndroidBitmapInfo info;
    if (AndroidBitmap_getInfo(env, bitmap, &info) < 0 ||
        AndroidBitmap_lockPixels(env, bitmap, &pixels) < 0) {
        env->DeleteLocalRef(bitmap);
        env->DeleteLocalRef(bitmapClass);
        return emptyResult;
    }

    // The created bitmap is RGBA8888.
    std::memcpy(pixels, pixels_.data(), pixels_.size());
    AndroidBitmap_unlockPixels(env, bitmap);

    // Compress to JPEG.
    jclass compressFormatClass = env->FindClass("android/graphics/Bitmap$CompressFormat");
    jfieldID jpegField = env->GetStaticFieldID(compressFormatClass, "JPEG",
                                               "Landroid/graphics/Bitmap$CompressFormat;");
    jobject jpegFormat = env->GetStaticObjectField(compressFormatClass, jpegField);
    jmethodID compressMethod = env->GetMethodID(bitmapClass, "compress",
                                                "(Landroid/graphics/Bitmap$CompressFormat;ILjava/io/OutputStream;)Z");

    jclass byteArrayOutputStreamClass = env->FindClass("java/io/ByteArrayOutputStream");
    jmethodID baosCtor = env->GetMethodID(byteArrayOutputStreamClass, "<init>", "()V");
    jobject baos = env->NewObject(byteArrayOutputStreamClass, baosCtor);

    env->CallBooleanMethod(bitmap, compressMethod, jpegFormat, quality, baos);

    jmethodID toByteArray = env->GetMethodID(byteArrayOutputStreamClass, "toByteArray", "()[B");
    jbyteArray result = static_cast<jbyteArray>(env->CallObjectMethod(baos, toByteArray));

    jsize len = env->GetArrayLength(result);
    std::vector<uint8_t> out(static_cast<size_t>(len));
    env->GetByteArrayRegion(result, 0, len, reinterpret_cast<jbyte*>(out.data()));

    env->DeleteLocalRef(result);
    env->DeleteLocalRef(baos);
    env->DeleteLocalRef(byteArrayOutputStreamClass);
    env->DeleteLocalRef(jpegFormat);
    env->DeleteLocalRef(compressFormatClass);
    env->DeleteLocalRef(bitmap);
    env->DeleteLocalRef(bitmapClass);

    return out;
}

MatchResult matchTemplate(const ImageBuffer& source, const ImageBuffer& templ, double threshold) {
    MatchResult result;
    int sw = source.width();
    int sh = source.height();
    int tw = templ.width();
    int th = templ.height();

    if (sw < tw || sh < th || tw == 0 || th == 0) {
        return result;
    }

    const int channels = 4;
    int maxX = sw - tw;
    int maxY = sh - th;
    double bestScore = -1.0;
    int bestX = 0;
    int bestY = 0;

    // Compute template mean.
    double templMean[3] = {0, 0, 0};
    for (int y = 0; y < th; ++y) {
        for (int x = 0; x < tw; ++x) {
            templMean[0] += templ.r(x, y);
            templMean[1] += templ.g(x, y);
            templMean[2] += templ.b(x, y);
        }
    }
    double templCount = static_cast<double>(tw * th);
    for (int c = 0; c < 3; ++c) templMean[c] /= templCount;

    for (int y = 0; y <= maxY; ++y) {
        for (int x = 0; x <= maxX; ++x) {
            double srcMean[3] = {0, 0, 0};
            for (int yy = 0; yy < th; ++yy) {
                for (int xx = 0; xx < tw; ++xx) {
                    srcMean[0] += source.r(x + xx, y + yy);
                    srcMean[1] += source.g(x + xx, y + yy);
                    srcMean[2] += source.b(x + xx, y + yy);
                }
            }
            for (int c = 0; c < 3; ++c) srcMean[c] /= templCount;

            double numerator[3] = {0, 0, 0};
            double srcDenom[3] = {0, 0, 0};
            double templDenom[3] = {0, 0, 0};

            for (int yy = 0; yy < th; ++yy) {
                for (int xx = 0; xx < tw; ++xx) {
                    double s[3] = {
                        static_cast<double>(source.r(x + xx, y + yy)) - srcMean[0],
                        static_cast<double>(source.g(x + xx, y + yy)) - srcMean[1],
                        static_cast<double>(source.b(x + xx, y + yy)) - srcMean[2]
                    };
                    double t[3] = {
                        static_cast<double>(templ.r(xx, yy)) - templMean[0],
                        static_cast<double>(templ.g(xx, yy)) - templMean[1],
                        static_cast<double>(templ.b(xx, yy)) - templMean[2]
                    };
                    for (int c = 0; c < 3; ++c) {
                        numerator[c] += s[c] * t[c];
                        srcDenom[c] += s[c] * s[c];
                        templDenom[c] += t[c] * t[c];
                    }
                }
            }

            double scoreSum = 0;
            for (int c = 0; c < 3; ++c) {
                double denom = std::sqrt(srcDenom[c] * templDenom[c]);
                scoreSum += (denom > 1e-6) ? (numerator[c] / denom) : 0.0;
            }
            double score = scoreSum / 3.0;

            if (score > bestScore) {
                bestScore = score;
                bestX = x;
                bestY = y;
            }
        }
    }

    if (bestScore >= threshold) {
        result.found = true;
        result.point = {bestX, bestY};
        result.score = bestScore;
    }
    return result;
}

} // namespace baas
