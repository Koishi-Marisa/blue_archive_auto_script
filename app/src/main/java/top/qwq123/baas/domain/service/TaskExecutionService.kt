package top.qwq123.baas.domain.service

import android.app.Service
import android.content.Intent
import android.os.IBinder

class TaskExecutionService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // TODO: run BAAS task with foreground notification
        return START_NOT_STICKY
    }
}
