package top.qwq123.baas.shizuku

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log

/**
 * Screenshot provider backed by Shizuku ADB shell `screencap -p`.
 */
class ShizukuScreenshotService {

    private val TAG = "ShizukuScreenshot"

    /** Returns the current screen as a Bitmap, or null on failure. */
    fun capture(): Bitmap? {
        val result = ShizukuHelper.executeRaw("screencap -p")
        if (result.isFailure) {
            Log.e(TAG, "screencap failed", result.exceptionOrNull())
            return null
        }
        val bytes = result.getOrNull() ?: return null
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
    }

    fun screenshotSize(): String {
        val result = ShizukuHelper.execute("wm size")
        val output = result.getOrNull() ?: return ""
        // Output format: "Physical size: 1080x2400" or "Override size: 1080x2400"
        val regex = Regex("""(\d+)x(\d+)""")
        val match = regex.find(output) ?: return ""
        return "${match.groupValues[1]},${match.groupValues[2]}"
    }
}
