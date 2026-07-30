package top.qwq123.baas.shizuku

import android.util.Log

/**
 * Touch event injection backed by Shizuku ADB shell `input`.
 */
class ShizukuControlService {

    private val TAG = "ShizukuControl"

    fun click(x: Int, y: Int): Boolean {
        return execute("input tap $x $y")
    }

    fun swipe(x1: Int, y1: Int, x2: Int, y2: Int, durationMs: Int): Boolean {
        return execute("input swipe $x1 $y1 $x2 $y2 $durationMs")
    }

    fun longClick(x: Int, y: Int, durationMs: Int): Boolean {
        return execute("input swipe $x $y $x $y $durationMs")
    }

    private fun execute(command: String): Boolean {
        val result = ShizukuHelper.execute(command)
        if (result.isFailure) {
            Log.e(TAG, "Command failed: $command", result.exceptionOrNull())
            return false
        }
        return true
    }
}
