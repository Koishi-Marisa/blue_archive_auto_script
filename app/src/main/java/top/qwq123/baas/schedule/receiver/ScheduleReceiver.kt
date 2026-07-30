package top.qwq123.baas.schedule.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import top.qwq123.baas.domain.service.TaskExecutionService

class ScheduleReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        val serviceIntent = Intent(context, TaskExecutionService::class.java).apply {
            putExtra(TaskExecutionService.EXTRA_CONFIG_NAME, "android")
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(serviceIntent)
        } else {
            context.startService(serviceIntent)
        }
    }
}
