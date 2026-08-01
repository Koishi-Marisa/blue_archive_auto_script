package top.qwq123.baas.bridge

import android.content.Context
import android.graphics.BitmapFactory

/**
 * JNI bridge to the C++ BAAS core.
 *
 * The native library `baas-core` exposes screenshot capture, input injection,
 * template matching, and configuration APIs. It internally calls back into
 * [BaasBridge] for Android-specific services (Shizuku screenshot/touch, OCR).
 */
object BaasCoreNative {

    init {
        System.loadLibrary("baas-core")
    }

    @JvmStatic
    external fun nativeInit(context: Context)

    @JvmStatic
    external fun nativeLoadConfig(json: String): Boolean

    @JvmStatic
    external fun nativeGetConfigValue(key: String): String

    @JvmStatic
    external fun nativeScreenshot(): ByteArray?

    @JvmStatic
    external fun nativeScreenshotSize(): String

    @JvmStatic
    external fun nativeClick(x: Int, y: Int): Boolean

    @JvmStatic
    external fun nativeSwipe(x1: Int, y1: Int, x2: Int, y2: Int, durationMs: Int): Boolean

    @JvmStatic
    external fun nativeLongClick(x: Int, y: Int, durationMs: Int): Boolean

    @JvmStatic
    external fun nativeFindTemplate(templateJpeg: ByteArray, threshold: Double): String

    @JvmStatic
    external fun nativeRgbInRange(
        x: Int, y: Int,
        rMin: Int, rMax: Int,
        gMin: Int, gMax: Int,
        bMin: Int, bMax: Int
    ): Boolean

    @JvmStatic
    external fun nativeGetVersion(): String

    /** Helper that decodes the last native screenshot size. */
    fun screenshotSizePair(): Pair<Int, Int> {
        return nativeScreenshotSize().split(",").mapNotNull { it.toIntOrNull() }
            .let { if (it.size == 2) it[0] to it[1] else 0 to 0 }
    }

    /** Decode the template asset bundled in the APK. */
    fun loadAssetTemplate(context: Context, assetPath: String): ByteArray? {
        return try {
            context.assets.open(assetPath).use { it.readBytes() }
        } catch (e: Exception) {
            null
        }
    }
}
