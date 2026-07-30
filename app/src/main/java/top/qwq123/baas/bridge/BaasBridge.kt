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
    private var ocrService: OcrService? = null

    /** True when both screenshot permission and accessibility service are ready. */
    @JvmStatic
    fun isReady(): Boolean {
        return screenshotService?.lastBitmap != null && AccessibilityHelperService.instance != null
    }

    @JvmStatic
    fun init(context: Context) {
        screenshotService = ScreenshotService(context.applicationContext)
        controlService = ControlService(context.applicationContext)
        ocrService = OcrService()
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

    /** Returns the last screenshot as a JPEG byte array, or null. */
    @JvmStatic
    @Synchronized
    fun screenshotJpeg(): ByteArray? {
        val bmp = screenshotService?.capture() ?: run {
            Log.w(TAG, "Screenshot service not ready")
            return null
        }
        return bmp.toJpeg()
    }

    /** Returns the last screenshot size as "width,height" or empty string. */
    @JvmStatic
    fun screenshotSize(): String {
        val bmp = screenshotService?.lastBitmap ?: return ""
        return "${bmp.width},${bmp.height}"
    }

    @JvmStatic
    fun click(x: Int, y: Int): Boolean {
        return controlService?.click(x, y) ?: false
    }

    @JvmStatic
    fun swipe(x1: Int, y1: Int, x2: Int, y2: Int, durationMs: Int): Boolean {
        return controlService?.swipe(x1, y1, x2, y2, durationMs) ?: false
    }

    @JvmStatic
    fun longClick(x: Int, y: Int, durationMs: Int): Boolean {
        return controlService?.longClick(x, y, durationMs) ?: false
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
