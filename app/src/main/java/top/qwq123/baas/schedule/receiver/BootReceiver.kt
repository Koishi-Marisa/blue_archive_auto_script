package top.qwq123.baas.schedule.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        // TODO: reschedule BAAS tasks after boot/update
    }
}
