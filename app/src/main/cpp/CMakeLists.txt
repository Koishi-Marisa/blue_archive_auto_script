cmake_minimum_required(VERSION 3.22.1)
project("baas-core")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Android NDK provides bitmap and log headers.
find_library(log-lib log)
find_library(android-lib android)
find_library(jnigraphics-lib jnigraphics)

add_library(
    baas-core
    SHARED
    core/baas_core.cpp
    core/image.cpp
    core/jni_bridge.cpp
)

target_include_directories(baas-core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(
    baas-core
    ${log-lib}
    ${android-lib}
    ${jnigraphics-lib}
)
