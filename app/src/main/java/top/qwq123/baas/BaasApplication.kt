package top.qwq123.baas

import android.app.Application
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import top.qwq123.baas.bridge.BaasBridge

class BaasApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        BaasBridge.init(this)
    }
}
