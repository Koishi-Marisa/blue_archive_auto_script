package top.qwq123.baas.service

import android.accessibilityservice.AccessibilityService
import android.os.Build
import android.view.accessibility.AccessibilityEvent

class AccessibilityHelperService : AccessibilityService() {

    companion object {
        @Volatile
        var instance: AccessibilityHelperService? = null
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Forward events to BAAS runtime if needed.
    }

    override fun onInterrupt() {
        // Cleanup.
    }

    override fun onDestroy() {
        super.onDestroy()
        if (instance == this) instance = null
    }
}
