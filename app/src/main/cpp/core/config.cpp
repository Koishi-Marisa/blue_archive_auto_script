#include "core/config.h"

#include <cctype>
#include <sstream>

namespace baas {

// Minimal flat JSON parser supporting string, number, true, false, null values.
bool Config::loadJson(const std::string& json) {
    data_.clear();
    size_t pos = 0;

    auto skipSpaces = [&](size_t& p) {
        while (p < json.size() && std::isspace(static_cast<unsigned char>(json[p]))) ++p;
    };

    skipSpaces(pos);
    if (pos >= json.size() || json[pos] != '{') return false;
    ++pos;

    while (true) {
        skipSpaces(pos);
        if (pos < json.size() && json[pos] == '}') {
            ++pos;
            return true;
        }
        if (pos >= json.size() || json[pos] != '"') return false;

        // key
        size_t keyStart = ++pos;
        size_t keyEnd = json.find('"', keyStart);
        if (keyEnd == std::string::npos) return false;
        std::string key = json.substr(keyStart, keyEnd - keyStart);
        pos = keyEnd + 1;

        skipSpaces(pos);
        if (pos >= json.size() || json[pos] != ':') return false;
        ++pos;
        skipSpaces(pos);

        // value
        std::string value;
        if (pos < json.size() && json[pos] == '"') {
            size_t valueStart = ++pos;
            size_t valueEnd = json.find('"', valueStart);
            if (valueEnd == std::string::npos) return false;
            value = json.substr(valueStart, valueEnd - valueStart);
            pos = valueEnd + 1;
        } else {
            size_t valueStart = pos;
            while (pos < json.size() && json[pos] != ',' && json[pos] != '}') ++pos;
            value = json.substr(valueStart, pos - valueStart);
            // trim trailing spaces
            size_t end = value.find_last_not_of(" \t\r\n");
            if (end == std::string::npos) value.clear();
            else value.resize(end + 1);
        }

        data_[key] = value;

        skipSpaces(pos);
        if (pos < json.size() && json[pos] == ',') {
            ++pos;
            continue;
        }
        if (pos < json.size() && json[pos] == '}') {
            ++pos;
            return true;
        }
        return false;
    }
}

bool Config::has(const std::string& key) const {
    return data_.find(key) != data_.end();
}

std::string Config::getString(const std::string& key, const std::string& defaultValue) const {
    auto it = data_.find(key);
    return it != data_.end() ? it->second : defaultValue;
}

int Config::getInt(const std::string& key, int defaultValue) const {
    auto it = data_.find(key);
    if (it == data_.end()) return defaultValue;
    try { return std::stoi(it->second); } catch (...) { return defaultValue; }
}

double Config::getDouble(const std::string& key, double defaultValue) const {
    auto it = data_.find(key);
    if (it == data_.end()) return defaultValue;
    try { return std::stod(it->second); } catch (...) { return defaultValue; }
}

bool Config::getBool(const std::string& key, bool defaultValue) const {
    auto it = data_.find(key);
    if (it == data_.end()) return defaultValue;
    const std::string& v = it->second;
    if (v == "true" || v == "1") return true;
    if (v == "false" || v == "0") return false;
    return defaultValue;
}

void Config::setString(const std::string& key, const std::string& value) {
    data_[key] = value;
}

void Config::setInt(const std::string& key, int value) {
    data_[key] = std::to_string(value);
}

void Config::setDouble(const std::string& key, double value) {
    data_[key] = std::to_string(value);
}

void Config::setBool(const std::string& key, bool value) {
    data_[key] = value ? "true" : "false";
}

std::vector<std::string> Config::keys() const {
    std::vector<std::string> out;
    out.reserve(data_.size());
    for (const auto& kv : data_) out.push_back(kv.first);
    return out;
}

} // namespace baas
