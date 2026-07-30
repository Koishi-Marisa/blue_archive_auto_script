package top.qwq123.baas.shizuku

import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.RemoteException
import android.util.Log
import rikka.shizuku.Shizuku
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
            Shizuku.isPreV11() || Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        } catch (e: Throwable) {
            false
        }
    }

    /** Request Shizuku permission from the user. */
    fun requestPermission(requestCode: Int) {
        Shizuku.requestPermission(requestCode)
    }

    /** Returns a one-line diagnostic string for the UI. */
    fun info(): String {
        val installed = isInstalled()
        val granted = isGranted()
        val version = try {
            Shizuku.getBinder().let { binder ->
                if (binder != null) "binder ok" else "binder null"
            }
        } catch (e: Throwable) {
            "binder err: ${e.javaClass.simpleName}"
        }
        return "installed=$installed, granted=$granted, $version"
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
            Log.d(TAG, "execute: $command (redirectErr=$redirectErr)")
            val process = newProcessViaReflection(
                arrayOf("sh", "-c", command),
                if (redirectErr) arrayOf("LD_LIBRARY_PATH=/data/local/tmp") else null,
                null
            ) ?: return Result.failure(IllegalStateException("Shizuku returned null process"))

            val output = process.inputStream.use { it.readBytes() }
            val exitCode = process.waitFor()
            Log.d(TAG, "execute finished: exit=$exitCode, bytes=${output.size}")
            if (exitCode != 0) {
                val stderr = try {
                    String(process.errorStream.readBytes(), Charset.defaultCharset())
                } catch (e: Exception) {
                    ""
                }
                Log.w(TAG, "execute exit code $exitCode, stderr: $stderr")
            }
            Result.success(output)
        } catch (e: RemoteException) {
            Log.e(TAG, "execute RemoteException", e)
            Result.failure(e)
        } catch (e: Exception) {
            Log.e(TAG, "execute Exception", e)
            Result.failure(e)
        }
    }

    @SuppressLint("PrivateApi")
    private fun newProcessViaReflection(cmd: Array<String>, env: Array<String>?, dir: String?): Process? {
        val method = Shizuku::class.java.getDeclaredMethod("newProcess", Array<String>::class.java, Array<String>::class.java, String::class.java)
        method.isAccessible = true
        return method.invoke(null, cmd, env, dir) as? Process
    }
}
