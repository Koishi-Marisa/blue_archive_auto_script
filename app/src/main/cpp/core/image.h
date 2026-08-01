#pragma once

#include <jni.h>
#include <cstdint>
#include <memory>
#include <vector>

namespace baas {

struct Point {
    int x = 0;
    int y = 0;
};

struct Rect {
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;
};

struct MatchResult {
    bool found = false;
    Point point;
    double score = 0.0;
};

// Simple RGBA8888 image buffer.
class ImageBuffer {
public:
    ImageBuffer() = default;
    ImageBuffer(int width, int height, std::vector<uint8_t> pixels);

    int width() const { return width_; }
    int height() const { return height_; }
    bool empty() const { return width_ <= 0 || height_ <= 0 || pixels_.empty(); }

    const uint8_t* pixel(int x, int y) const;
    uint8_t* pixel(int x, int y);

    uint8_t r(int x, int y) const;
    uint8_t g(int x, int y) const;
    uint8_t b(int x, int y) const;

    // Decode JPEG bytes using Android BitmapFactory.
    static std::shared_ptr<ImageBuffer> fromJpeg(JNIEnv* env, jobject context, const std::vector<uint8_t>& jpeg);

    // Encode to JPEG (quality 0-100) using Android Bitmap compress.
    std::vector<uint8_t> toJpeg(JNIEnv* env, int quality = 95) const;

    // Crop a region into a new buffer.
    std::shared_ptr<ImageBuffer> crop(const Rect& region) const;

private:
    int width_ = 0;
    int height_ = 0;
    std::vector<uint8_t> pixels_; // RGBA8888
};

// Normalized cross-correlation template matching over RGB channels.
MatchResult matchTemplate(const ImageBuffer& source, const ImageBuffer& templ, double threshold);

} // namespace baas
