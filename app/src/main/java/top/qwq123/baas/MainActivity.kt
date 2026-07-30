package top.qwq123.baas

import android.content.Intent
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import top.qwq123.baas.bridge.BaasBridge
import top.qwq123.baas.domain.service.TaskExecutionService

class MainActivity : ComponentActivity() {
    companion object {
        private const val REQUEST_SCREENSHOT = 1001
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
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
}

@Composable
fun MainScreen(
    onRequestScreenshot: () -> Unit,
    onOpenAccessibility: () -> Unit
) {
    val context = LocalContext.current
    var result by remember { mutableStateOf("Tap button to run BAAS smoke test") }

    Column(modifier = Modifier.padding(16.dp)) {
        Text("BAAS Android", style = MaterialTheme.typography.headlineMedium)
        Text(result, modifier = Modifier.padding(vertical = 16.dp))

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
            Text("Grant Screenshot")
        }

        Button(onClick = onOpenAccessibility) {
            Text("Open Accessibility")
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(onClick = {
            if (!BaasBridge.isReady()) {
                result = "Please grant screenshot permission and enable accessibility service first"
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
