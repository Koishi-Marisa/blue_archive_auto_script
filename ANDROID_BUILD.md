# BAAS Android 构建指南

本仓库已按 [MAA-Meow](https://github.com/Aliothmoon/MAA-Meow) 的完整 Android Gradle 工程结构进行适配，但将底层核心从 MAA Core 替换为 BAAS Python 运行时。

## 项目结构变化

```text
/workspace
├── app/                          # Android 应用主模块
│   ├── build.gradle.kts          # 已改为 BAAS 包名与配置
│   ├── asset-manifest.gradle.kts # 生成 assets/baas/asset_manifest.json
│   ├── i18n-verify.gradle.kts    # 中英字符串一致性校验
│   └── src/main/
│       ├── AndroidManifest.xml   # 已改为 BAAS 包名/主题/Action
│       ├── java/top/qwq123/baas/ # 占位 Kotlin 类，保证编译通过
│       └── res/                  # MAA-Meow 的 UI 资源（已保留，可后续替换）
├── annotation-api/               # KSP SharedPreferences 注解模块
├── hidden-api/                   # 系统隐藏 API 模块
├── ksp-processor/                # KSP 注解处理器
├── scripts/
│   ├── setup_baas_assets.py      # 打包 BAAS Python 资源到 assets
│   └── requirements.txt          # 脚本依赖
├── .github/workflows/
│   ├── build-dev.yml             # 推送 main/dev 或 PR 时构建 Debug APK
│   └── build-release.yml         # 推送 v* tag 时构建 Release APK 并发布
└── deploy/android/               # 原 buildozer/PySide6 方案（已保留，但不再用于新工作流）
```

## 本地构建步骤

1. **准备环境**
   - JDK 17+
   - Android SDK + NDK (r29.0.13113456)
   - Python 3.9+

2. **打包 BAAS Python 资源**
   ```bash
   python scripts/setup_baas_assets.py --clean
   ```
   这会把 `core/`、`gui/`、`module/`、`src/`、`main.py` 等复制到 `app/src/main/assets/baas/`，并尝试安装依赖到 `app/src/main/assets/baas/site-packages/`。

3. **构建 APK**
   ```bash
   ./gradlew :app:assembleDebug
   ```
   或构建 Release：
   ```bash
   ./gradlew :app:assembleRelease
   ```

4. **输出路径**
   - Debug: `app/build/outputs/apk/debug/`
   - Release: `app/build/outputs/apk/release/`

## GitHub Actions 自动构建与发布

### Debug / CI 构建
- 触发条件：推送到 `main`/`dev` 分支、对 `main` 分支的 Pull Request、手动触发
- 工作流：[build-dev.yml](.github/workflows/build-dev.yml)
- 产物：自动上传 `debug-apk` artifact

### Release 构建与发布
- 触发条件：推送 `v*` 开头的 tag（如 `v1.0.0`、`v1.1.0-beta.1`）
- 工作流：[build-release.yml](.github/workflows/build-release.yml)
- 矩阵构建：
  - `universal`（同时包含 arm64-v8a + x86_64）
  - `arm64-v8a`
  - `x64`（x86_64）
- 发布：自动创建 GitHub Release，附带三个 APK 文件
- 预发布：tag 包含 `alpha`/`beta`/`rc` 时自动标记为 prerelease

### 签名配置（可选）
Release 构建支持使用 GitHub Secrets 签名：
- `KEYSTORE_BASE64`：release.jks 的 base64 编码
- `KEYSTORE_PASSWORD`
- `KEY_ALIAS`
- `KEY_PASSWORD`

未配置时，Release APK 为未签名状态。

## C++ 核心（android-cpp-core 分支）

本分支在保留 Chaquopy Python 运行时与 Compose UI 的基础上，新增了原生 C++ 核心：

- 路径：`app/src/main/cpp/`
- 库名：`libbaas-core.so`
- JNI 入口：`top.qwq123.baas.bridge.BaasCoreNative`
- 功能：
  - 通过 `BaasBridge` 回调获取 Shizuku 截图与注入触控事件
  - JPEG 编解码（调用 Android `BitmapFactory`）
  - RGB 范围检查
  - 简单 NCC 模板匹配
  - JSON 配置加载

UI 调试页面已增加 **C++ Core** 区域，可验证：
- 配置读写
- 截图与尺寸
- 中心点击
- RGB 检查
- 模板查找

## 已知占位项 / 待实现

1. **任务执行**
   - `TaskExecutionService`、`ScheduleExecutionService` 中调用 C++ 核心或 BAAS Python 入口。

2. **UI 替换**
   - 当前保留 MAA-Meow 的 Compose UI 骨架和字符串，后续可按 BAAS 需求重写。

3. **OCR 适配**
   - C++ 核心目前不直接做 OCR；Android 侧 OCR 仍通过 `OcrService` + MLKit 完成。

## 注意事项

- `app/src/main/assets/baas/` 与 `.baasversion` 是构建时生成的，已加入 `.gitignore`，请勿提交。
- 依赖安装步骤在 CI 中使用宿主 pip，某些含 native 扩展的包可能无法直接安装到 Android。建议后续将依赖清单改为纯 Python 或预先编译好 Android wheel。
- 原 `deploy/android/` 下的 buildozer/PySide6 方案未删除，但新 GitHub Actions 已不再使用。如需回退，仍可手动运行 `python deploy/android/build.py`。
