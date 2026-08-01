#pragma once

#include <jni.h>
#include <string>
#include <unordered_map>
#include <vector>

namespace baas {

// Lightweight key-value config store.
// Values are stored as strings; numeric getters parse on demand.
class Config {
public:
    Config() = default;

    // Parse a flat JSON object {"key":"value",...} into the store.
    bool loadJson(const std::string& json);

    bool has(const std::string& key) const;
    std::string getString(const std::string& key, const std::string& defaultValue = "") const;
    int getInt(const std::string& key, int defaultValue = 0) const;
    double getDouble(const std::string& key, double defaultValue = 0.0) const;
    bool getBool(const std::string& key, bool defaultValue = false) const;

    void setString(const std::string& key, const std::string& value);
    void setInt(const std::string& key, int value);
    void setDouble(const std::string& key, double value);
    void setBool(const std::string& key, bool value);

    std::vector<std::string> keys() const;

private:
    std::unordered_map<std::string, std::string> data_;
};

} // namespace baas
