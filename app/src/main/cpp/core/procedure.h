#pragma once

#include "core/baas_core.h"
#include "core/config.h"

#include <string>

namespace baas {

// Simple procedure: wait for a feature to appear, then click a target point.
class AppearThenClickProcedure {
public:
    AppearThenClickProcedure(
        const std::string& featureName,
        int clickX,
        int clickY,
        int timeoutMs = 10000,
        int intervalMs = 500
    );

    bool execute(BaasCore& baas);

private:
    std::string featureName_;
    int clickX_;
    int clickY_;
    int timeoutMs_;
    int intervalMs_;
};

} // namespace baas
