package top.qwq123.baas.domain.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
import top.qwq123.baas.R

/**
 * Foreground service that runs the BAAS Python scheduler loop.
 *
 * Starting this service will call main_android.run_task() which initializes
 * the BAAS core and starts the task scheduler on a background thread.
 */
class TaskExecutionService : Service() {

    companion object {
        const val CHANNEL_ID = "baas_task_channel"
        const val NOTIFICATION_ID = 1
        const val ACTION_STOP = "top.qwq123.baas.ACTION_STOP_TASK"
        const val EXTRA_CONFIG_NAME = "config_name"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification("BAAS is initializing..."))
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopPythonTask()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf(startId)
            return START_NOT_STICKY
        }

        val configName = intent?.getStringExtra(EXTRA_CONFIG_NAME) ?: "android"
        Thread { runBaasTask(configName) }.start()
        return START_STICKY
    }

    private fun runBaasTask(configName: String) {
        try {
            updateNotification("BAAS task running ($configName)")
            val py = Python.getInstance()
            val module = py.getModule("main_android")
            val result = module.callAttr("run_task", configName).toString()
            Log.i("TaskExecutionService", "run_task returned: $result")
            if (result != "started") {
                updateNotification("BAAS failed to start: $result")
            } else {
                updateNotification("BAAS task running ($configName)")
            }
        } catch (e: Exception) {
            Log.e("TaskExecutionService", "run_task failed", e)
            updateNotification("BAAS task error: ${e.message}")
        }
    }

    private fun stopPythonTask() {
        try {
            val py = Python.getInstance()
            val module = py.getModule("main_android")
            module.callAttr("stop_task")
        } catch (e: Exception) {
            Log.e("TaskExecutionService", "stop_task failed", e)
        }
    }

    private fun updateNotification(text: String) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification(text))
    }

    private fun buildNotification(text: String): Notification {
        val stopIntent = Intent(this, TaskExecutionService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPending = PendingIntent.getService(
            this,
            0,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("BAAS")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_progress_tracker)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .addAction(0, getString(R.string.stop_task), stopPending)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "BAAS task execution",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows progress of BAAS automated tasks"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }
}
