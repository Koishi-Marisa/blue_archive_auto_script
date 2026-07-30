package top.qwq123.baas.bridge

import android.accessibilityservice.GestureDescription
import android.content.Context
import android.graphics.Path
import android.os.Build
import android.util.Log
import top.qwq123.baas.service.AccessibilityHelperService

/**
 * Injects touch events via the accessibility service.
 */
class ControlService(private val context: Context) {
    private val TAG = "ControlService"

    private fun service(): AccessibilityHelperService? {
        return AccessibilityHelperService.instance
    }

    fun click(x: Int, y: Int): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path().apply { moveTo(x.toFloat(), y.toFloat()) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 50))
            .build()
        return service()?.dispatchGesture(gesture, null, null) ?: false
    }

    fun swipe(x1: Int, y1: Int, x2: Int, y2: Int, durationMs: Int): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path().apply {
            moveTo(x1.toFloat(), y1.toFloat())
            lineTo(x2.toFloat(), y2.toFloat())
        }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, durationMs.coerceAtLeast(50).toLong()))
            .build()
        return service()?.dispatchGesture(gesture, null, null) ?: false
    }

    fun longClick(x: Int, y: Int, durationMs: Int): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        val path = Path().apply { moveTo(x.toFloat(), y.toFloat()) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, durationMs.coerceAtLeast(300).toLong()))
            .build()
        return service()?.dispatchGesture(gesture, null, null) ?: false
    }
}
