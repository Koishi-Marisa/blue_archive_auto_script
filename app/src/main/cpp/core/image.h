#pragma once

#include <cstdint>
#include <vector>
#include <memory>

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

class ImageBuffer {
public:
    ImageBuffer() = default;
    ImageBuffer(int width, int height, std::vector<uint8_t> pixels);

    int width() const { return width_; }
    int height() const { return height_; }
    bool empty() const { return pixels_.empty(); }

    // Pixel in RGBA8888 format.
    const uint8_t* pixel(int x, int y) const;
    uint8_t* pixel(int x, int y);

    uint8_t r(int x, int y) const;
    uint8_t g(int x, int y) const;
    uint8_t b(int x, int y) const;

    // Decode JPEG using Android BitmapFactory via JNI.
    static std::shared_ptr<ImageBuffer> fromJpeg(JNIEnv* env, jobject context, const std::vector<uint8_t>& jpeg);

    // Convert this buffer to a JPEG byte vector (quality 0-100).
    std::vector<uint8_t> toJpeg(JNIEnv* env, int quality = 95) const;

private:
    int width_ = 0;
    int height_ = 0;
    std::vector<uint8_t> pixels_; // RGBA8888
};

// Simple normalized cross-correlation template matching.
MatchResult matchTemplate(const ImageBuffer& source, const ImageBuffer& templ, double threshold);

} // namespace baas
