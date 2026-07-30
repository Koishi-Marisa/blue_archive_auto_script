package top.qwq123.baas.shizuku

import android.content.pm.PackageManager
import android.os.ParcelFileDescriptor
import android.os.RemoteException
import android.util.Log
import rikka.shizuku.Shizuku
import java.io.BufferedReader
import java.io.InputStreamReader
import java.nio.charset.Charset

/**
 * Helper that binds to the Shizuku service and executes ADB shell commands.
 *
 * Requires the Shizuku Manager app to be installed and authorized.
 */
object ShizukuHelper {

    private const val TAG = "ShizukuHelper"

    /** True if Shizuku service is running and we can try to bind. */
    fun isInstalled(): Boolean {
        return Shizuku.pingBinder()
    }

    /** True if the user has granted permission to this app. */
    fun isGranted(): Boolean {
        return try {
            Shizuku.isPreV11 || Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        } catch (e: Throwable) {
            false
        }
    }

    /** Request Shizuku permission from the user. */
    fun requestPermission(requestCode: Int) {
        Shizuku.requestPermission(requestCode)
    }

    /**
     * Execute a shell command and return stdout as a string.
     */
    fun execute(command: String): Result<String> {
        return executeInternal(command, true)
            .map { bytes -> String(bytes, Charset.defaultCharset()) }
    }

    /**
     * Execute a shell command and return stdout as raw bytes.
     * Useful for binary output such as `screencap -p`.
     */
    fun executeRaw(command: String): Result<ByteArray> {
        return executeInternal(command, false)
    }

    private fun executeInternal(command: String, redirectErr: Boolean): Result<ByteArray> {
        if (!isInstalled()) {
            return Result.failure(IllegalStateException("Shizuku is not installed or running"))
        }
        if (!isGranted()) {
            return Result.failure(SecurityException("Shizuku permission not granted"))
        }

        return try {
            val process = Shizuku.newProcess(
                arrayOf("sh", "-c", command),
                if (redirectErr) arrayOf("LD_LIBRARY_PATH=/data/local/tmp") else null,
                null
            ) ?: return Result.failure(IllegalStateException("Shizuku returned null process"))

            process.inputStream.use { it.readBytes() }
                .also { process.waitFor() }
                .let { Result.success(it) }
        } catch (e: RemoteException) {
            Result.failure(e)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
