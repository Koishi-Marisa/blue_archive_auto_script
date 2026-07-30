package top.qwq123.baas

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import rikka.shizuku.Shizuku
import top.qwq123.baas.bridge.BaasBridge
import top.qwq123.baas.domain.service.TaskExecutionService
import top.qwq123.baas.shizuku.ShizukuHelper

class MainActivity : ComponentActivity() {
    companion object {
        private const val REQUEST_SCREENSHOT = 1001
        private const val REQUEST_SHIZUKU = 8722
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        BaasBridge.init(this)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MainScreen(
                        onRequestScreenshot = {
                            BaasBridge.requestScreenshotPermission(this, REQUEST_SCREENSHOT)
                        },
                        onOpenAccessibility = {
                            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                            startActivity(intent)
                        },
                        onRequestShizuku = {
                            if (ShizukuHelper.isInstalled()) {
                                ShizukuHelper.requestPermission(REQUEST_SHIZUKU)
                            } else {
                                val intent = Intent(Intent.ACTION_VIEW).apply {
                                    data = Uri.parse("https://shizuku.rikka.app/download/")
                                }
                                startActivity(intent)
                            }
                        }
                    )
                }
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_SCREENSHOT) {
            BaasBridge.onScreenshotPermissionResult(this, resultCode, data)
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_SHIZUKU) {
            val granted = grantResults.isNotEmpty() && grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED
            Toast.makeText(this, if (granted) "Shizuku granted" else "Shizuku denied", Toast.LENGTH_SHORT).show()
        }
    }
}

@Composable
fun MainScreen(
    onRequestScreenshot: () -> Unit,
    onOpenAccessibility: () -> Unit,
    onRequestShizuku: () -> Unit
) {
    val context = LocalContext.current
    var result by remember { mutableStateOf("Tap button to run BAAS smoke test") }
    var shizukuGranted by remember { mutableStateOf(ShizukuHelper.isGranted()) }

    LaunchedEffect(Unit) {
        // Default to Shizuku mode for this build.
        BaasBridge.setMode("SHIZUKU")
    }

    Column(modifier = Modifier.padding(16.dp)) {
        Text("BAAS Android", style = MaterialTheme.typography.headlineMedium)
        Text(result, modifier = Modifier.padding(vertical = 16.dp))

        // Shizuku status and authorization
        Text(
            "Shizuku: ${if (shizukuGranted) "GRANTED" else "NOT GRANTED"}",
            style = MaterialTheme.typography.bodyLarge,
            color = if (shizukuGranted) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
        )
        Button(onClick = {
            onRequestShizuku()
            shizukuGranted = ShizukuHelper.isGranted()
        }) {
            Text("Authorize Shizuku")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(onClick = {
            result = try {
                val py = Python.getInstance()
                val module = py.getModule("main_android")
                module.callAttr("smoke_test").toString()
            } catch (e: Exception) {
                "error: ${e.message}"
            }
        }) {
            Text("Run Smoke Test")
        }

        Button(onClick = onRequestScreenshot) {
            Text("Grant Screenshot (fallback)")
        }

        Button(onClick = onOpenAccessibility) {
            Text("Open Accessibility (fallback)")
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(onClick = {
            if (!BaasBridge.isReady()) {
                result = "Please authorize Shizuku first"
                Toast.makeText(context, result, Toast.LENGTH_LONG).show()
                return@Button
            }
            val intent = Intent(context, TaskExecutionService::class.java).apply {
                putExtra(TaskExecutionService.EXTRA_CONFIG_NAME, "android")
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
            result = "BAAS task started"
        }) {
            Text(stringResource(R.string.start_task))
        }

        Button(onClick = {
            val stopIntent = Intent(context, TaskExecutionService::class.java).apply {
                action = TaskExecutionService.ACTION_STOP
            }
            context.startService(stopIntent)
            result = "BAAS task stopping..."
        }) {
            Text(stringResource(R.string.stop_task))
        }
    }
}
