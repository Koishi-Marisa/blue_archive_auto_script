package top.qwq123.baas.service

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent

class AccessibilityHelperService : AccessibilityService() {
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // TODO: forward events to BAAS runtime
    }

    override fun onInterrupt() {
        // TODO: cleanup
    }
}
