#pragma once

#include "core/config.h"
#include "core/image.h"

#include <memory>
#include <string>

namespace baas {

class BaasCore;

// Lightweight feature system inspired by BAAS_Cpp.
// A feature checks whether something appears on the latest screenshot.
class Feature {
public:
    Feature(const std::string& name, const Config& config);
    virtual ~Feature() = default;

    const std::string& name() const { return name_; }

    // Check if the feature appears. If it does, result may contain extra data.
    virtual bool appear(const BaasCore& baas, Config& output) = 0;

protected:
    std::string name_;
    Config config_;
};

// Judge if a single point's RGB is within [min, max] for each channel.
class RgbRangeFeature : public Feature {
public:
    RgbRangeFeature(const std::string& name, const Config& config);
    bool appear(const BaasCore& baas, Config& output) override;
};

// Match a template image loaded from assets against the screenshot.
class TemplateMatchFeature : public Feature {
public:
    TemplateMatchFeature(const std::string& name, const Config& config);
    bool appear(const BaasCore& baas, Config& output) override;

private:
    std::shared_ptr<ImageBuffer> loadTemplate(const BaasCore& baas) const;
};

} // namespace baas
