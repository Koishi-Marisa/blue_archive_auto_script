package top.qwq123.baas.bridge

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.core.content.getSystemService
import com.chaquo.python.PyObject
import top.qwq123.baas.service.AccessibilityHelperService
import top.qwq123.baas.shizuku.ShizukuHelper
import top.qwq123.baas.shizuku.ShizukuScreenshotService
import top.qwq123.baas.shizuku.ShizukuControlService

/**
 * Bridge between Android native services and the BAAS Python runtime.
 *
 * Python code calls these static methods via Chaquopy to take screenshots,
 * inject touch events, and run OCR.
 */
object BaasBridge {
    private const val TAG = "BaasBridge"
    private var screenshotService: ScreenshotService? = null
    private var controlService: ControlService? = null
    private var shizukuScreenshotService: ShizukuScreenshotService? = null
    private var shizukuControlService: ShizukuControlService? = null
    private var ocrService: OcrService? = null

    enum class Mode { MEDIA_PROJECTION, SHIZUKU }
    private var mode: Mode = Mode.MEDIA_PROJECTION

    /** True when both screenshot permission and accessibility service are ready. */
    @JvmStatic
    fun isReady(): Boolean {
        return when (mode) {
            Mode.MEDIA_PROJECTION -> screenshotService?.lastBitmap != null && AccessibilityHelperService.instance != null
            Mode.SHIZUKU -> ShizukuHelper.isGranted()
        }
    }

    @JvmStatic
    fun init(context: Context) {
        screenshotService = ScreenshotService(context.applicationContext)
        controlService = ControlService(context.applicationContext)
        shizukuScreenshotService = ShizukuScreenshotService()
        shizukuControlService = ShizukuControlService()
        ocrService = OcrService()
    }

    @JvmStatic
    fun setMode(newMode: String) {
        mode = try {
            Mode.valueOf(newMode.uppercase())
        } catch (e: IllegalArgumentException) {
            Mode.MEDIA_PROJECTION
        }
        Log.i(TAG, "Bridge mode set to $mode")
    }

    @JvmStatic
    fun getMode(): String = mode.name

    @JvmStatic
    fun diagnosticInfo(): String {
        return buildString {
            appendLine("mode=${mode.name}")
            appendLine("shizuku={${ShizukuHelper.info()}}")
            appendLine("mediaProjection={lastBitmap=${screenshotService?.lastBitmap != null}}")
            appendLine("accessibility={instance=${AccessibilityHelperService.instance != null}}")
        }.trim()
    }

    @JvmStatic
    fun testShizukuShell(command: String): String {
        val result = ShizukuHelper.execute(command)
        return result.fold(
            onSuccess = { "OK (${it.length} chars): ${it.take(500)}" },
            onFailure = { "FAIL: ${it.javaClass.simpleName}: ${it.message}" }
        )
    }

    @JvmStatic
    fun testScreenshot(): String {
        val jpeg = screenshotJpeg()
        return if (jpeg != null) {
            "OK: ${jpeg.size} bytes, size=${screenshotSize()}"
        } else {
            "FAIL: screenshotJpeg returned null. ${diagnosticInfo()}"
        }
    }

    @JvmStatic
    fun testControl(): String {
        val (w, h) = screenshotSize().split(",").mapNotNull { it.toIntOrNull() }
            .let { if (it.size == 2) it[0] to it[1] else 1080 to 1920 }
        val x = w / 2
        val y = h / 2
        val ok = click(x, y)
        return if (ok) "OK: click at ($x, $y)" else "FAIL: click at ($x, $y). ${diagnosticInfo()}"
    }

    @JvmStatic
    fun testOcr(): String {
        val jpeg = screenshotJpeg() ?: return "FAIL: no screenshot"
        val (w, h) = screenshotSize().split(",").mapNotNull { it.toIntOrNull() }
            .let { if (it.size == 2) it[0] to it[1] else 0 to 0 }
        if (w == 0 || h == 0) return "FAIL: unknown screenshot size"
        val json = ocr(jpeg, w, h, "zh")
        return "OK: ${json.take(500)}"
    }

    @JvmStatic
    fun requestScreenshotPermission(activity: Activity, requestCode: Int) {
        val mgr = activity.getSystemService<MediaProjectionManager>() ?: return
        val intent = mgr.createScreenCaptureIntent()
        activity.startActivityForResult(intent, requestCode)
    }

    @JvmStatic
    fun onScreenshotPermissionResult(context: Context, resultCode: Int, data: Intent?) {
        if (resultCode == Activity.RESULT_OK && data != null) {
            screenshotService?.start(resultCode, data)
        }
    }

    /** Returns the current screenshot as a JPEG byte array, or null. */
    @JvmStatic
    @Synchronized
    fun screenshotJpeg(): ByteArray? {
        val bmp = when (mode) {
            Mode.MEDIA_PROJECTION -> screenshotService?.capture()
            Mode.SHIZUKU -> shizukuScreenshotService?.capture()
        } ?: run {
            Log.w(TAG, "Screenshot service not ready")
            return null
        }
        return bmp.toJpeg()
    }

    /** Returns the last screenshot size as "width,height" or empty string. */
    @JvmStatic
    fun screenshotSize(): String {
        return when (mode) {
            Mode.MEDIA_PROJECTION -> {
                val bmp = screenshotService?.lastBitmap ?: return ""
                "${bmp.width},${bmp.height}"
            }
            Mode.SHIZUKU -> shizukuScreenshotService?.screenshotSize() ?: ""
        }
    }

    @JvmStatic
    fun click(x: Int, y: Int): Boolean {
        return when (mode) {
            Mode.MEDIA_PROJECTION -> controlService?.click(x, y)
            Mode.SHIZUKU -> shizukuControlService?.click(x, y)
        } ?: false
    }

    @JvmStatic
    fun swipe(x1: Int, y1: Int, x2: Int, y2: Int, durationMs: Int): Boolean {
        return when (mode) {
            Mode.MEDIA_PROJECTION -> controlService?.swipe(x1, y1, x2, y2, durationMs)
            Mode.SHIZUKU -> shizukuControlService?.swipe(x1, y1, x2, y2, durationMs)
        } ?: false
    }

    @JvmStatic
    fun longClick(x: Int, y: Int, durationMs: Int): Boolean {
        return when (mode) {
            Mode.MEDIA_PROJECTION -> controlService?.longClick(x, y, durationMs)
            Mode.SHIZUKU -> shizukuControlService?.longClick(x, y, durationMs)
        } ?: false
    }

    @JvmStatic
    fun ocr(bytes: ByteArray, width: Int, height: Int, language: String): String {
        val service = ocrService ?: return "[]"
        val bitmap = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: return "[]"
        val latch = java.util.concurrent.CountDownLatch(1)
        var result = "[]"
        service.recognize(bitmap, language) { json ->
            result = json
            latch.countDown()
        }
        latch.await()
        return result
    }

    private fun Bitmap.toJpeg(quality: Int = 95): ByteArray {
        val stream = java.io.ByteArrayOutputStream()
        compress(Bitmap.CompressFormat.JPEG, quality, stream)
        return stream.toByteArray()
    }
}
