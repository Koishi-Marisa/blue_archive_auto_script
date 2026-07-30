package top.qwq123.baas.bridge

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.Looper
import android.util.Log
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Captures the device screen using MediaProjection.
 */
class ScreenshotService(private val context: Context) {
    private val TAG = "ScreenshotService"
    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private val started = AtomicBoolean(false)
    @Volatile
    var lastBitmap: Bitmap? = null
        private set

    fun start(resultCode: Int, data: Intent) {
        if (started.get()) return
        val mgr = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        mediaProjection = mgr.getMediaProjection(resultCode, data)
        startCapture()
        started.set(true)
    }

    private fun startCapture() {
        val metrics = context.resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        val density = metrics.densityDpi

        imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "BaasScreenshot",
            width, height, density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface, null, null
        )
    }

    fun capture(): Bitmap? {
        val reader = imageReader ?: return lastBitmap
        var image = reader.acquireLatestImage()
        if (image == null) {
            // Try again shortly if a frame is not ready.
            Thread.sleep(50)
            image = reader.acquireLatestImage()
        }
        image ?: return lastBitmap

        val planes = image.planes
        val buffer = planes[0].buffer
        val pixelStride = planes[0].pixelStride
        val rowStride = planes[0].rowStride
        val width = image.width
        val height = image.height
        val bmp = Bitmap.createBitmap(rowStride / pixelStride, height, Bitmap.Config.ARGB_8888)
        bmp.copyPixelsFromBuffer(buffer)
        val cropped = Bitmap.createBitmap(bmp, 0, 0, width, height)
        bmp.recycle()
        image.close()
        lastBitmap = cropped
        return cropped
    }

    fun stop() {
        virtualDisplay?.release()
        imageReader?.close()
        mediaProjection?.stop()
        started.set(false)
    }
}
