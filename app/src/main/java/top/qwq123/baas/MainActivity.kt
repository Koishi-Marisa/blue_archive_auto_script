package top.qwq123.baas

import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import kotlinx.coroutines.launch
import rikka.shizuku.Shizuku
import top.qwq123.baas.bridge.BaasBridge
import top.qwq123.baas.domain.service.TaskExecutionService
import top.qwq123.baas.shizuku.ShizukuHelper

private typealias ShizukuPermissionListener = rikka.shizuku.Shizuku.OnRequestPermissionResultListener

class MainActivity : ComponentActivity() {
    companion object {
        private const val REQUEST_SCREENSHOT = 1001
        private const val REQUEST_SHIZUKU = 8722
    }

    private var onShizukuResult: ((Boolean) -> Unit)? = null

    private val shizukuPermissionListener = ShizukuPermissionListener { requestCode, grantResult ->
        if (requestCode == REQUEST_SHIZUKU) {
            val granted = grantResult == PackageManager.PERMISSION_GRANTED
            runOnUiThread {
                onShizukuResult?.invoke(granted)
                Toast.makeText(
                    this,
                    if (granted) "Shizuku granted" else "Shizuku denied",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Shizuku.addRequestPermissionResultListener(shizukuPermissionListener)
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
                        onRequestShizuku = { onResult ->
                            this.onShizukuResult = onResult
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

    override fun onDestroy() {
        super.onDestroy()
        Shizuku.removeRequestPermissionResultListener(shizukuPermissionListener)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_SCREENSHOT) {
            BaasBridge.onScreenshotPermissionResult(this, resultCode, data)
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        // Shizuku uses its own listener API; keep this as a fallback only.
        if (requestCode == REQUEST_SHIZUKU) {
            val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
            onShizukuResult?.invoke(granted)
            Toast.makeText(this, if (granted) "Shizuku granted" else "Shizuku denied", Toast.LENGTH_SHORT).show()
        }
    }
}

@Composable
fun MainScreen(
    onRequestScreenshot: () -> Unit,
    onOpenAccessibility: () -> Unit,
    onRequestShizuku: (onResult: (Boolean) -> Unit) -> Unit
) {
    val context = LocalContext.current
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    var result by remember { mutableStateOf("Tap button to run BAAS smoke test") }
    var shizukuGranted by remember { mutableStateOf(ShizukuHelper.isGranted()) }
    var shellCommand by remember { mutableStateOf("whoami") }

    fun append(line: String) {
        result = if (result == "Tap button to run BAAS smoke test") {
            line
        } else {
            "$result\n$line"
        }
        scope.launch { listState.animateScrollToItem(0) }
    }

    LaunchedEffect(Unit) {
        // Default to Shizuku mode for this build.
        BaasBridge.setMode("SHIZUKU")
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Text(
            "BAAS Android",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(start = 16.dp, top = 16.dp, end = 16.dp)
        )

        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f).padding(horizontal = 16.dp)
        ) {
            item {
                Text(result, modifier = Modifier.padding(vertical = 8.dp))
            }
        }

        LazyColumn(
            modifier = Modifier.weight(2f).padding(horizontal = 16.dp)
        ) {
            item {
                Text(
                    "Shizuku: ${if (shizukuGranted) "GRANTED" else "NOT GRANTED"}",
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (shizukuGranted) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                )
                Button(onClick = {
                    onRequestShizuku { granted ->
                        shizukuGranted = granted
                    }
                }) {
                    Text("Authorize Shizuku")
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        append("Smoke: ${runCatching { Python.getInstance().getModule("main_android").callAttr("smoke_test").toString() }.getOrElse { it.message ?: "error" }}")
                    }) {
                        Text("Smoke")
                    }
                    Button(onClick = onRequestScreenshot) {
                        Text("Screenshot")
                    }
                    Button(onClick = onOpenAccessibility) {
                        Text("A11y")
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        if (!BaasBridge.isReady()) {
                            append("Please authorize Shizuku first")
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
                        append("BAAS task started")
                    }) {
                        Text(stringResource(R.string.start_task))
                    }
                    Button(onClick = {
                        val stopIntent = Intent(context, TaskExecutionService::class.java).apply {
                            action = TaskExecutionService.ACTION_STOP
                        }
                        context.startService(stopIntent)
                        append("BAAS task stopping...")
                    }) {
                        Text(stringResource(R.string.stop_task))
                    }
                }

                HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                Text("Debug", style = MaterialTheme.typography.titleMedium)
                Text(BaasBridge.diagnosticInfo(), style = MaterialTheme.typography.bodySmall)

                Spacer(modifier = Modifier.height(4.dp))

                OutlinedTextField(
                    value = shellCommand,
                    onValueChange = { shellCommand = it },
                    label = { Text("Shell command") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { append("Shell: ${BaasBridge.testShizukuShell(shellCommand)}") }) {
                        Text("Run Shell")
                    }
                    Button(onClick = { append("Info: ${ShizukuHelper.info()}") }) {
                        Text("Shizuku Info")
                    }
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { append("SS: ${BaasBridge.testScreenshot()}") }) {
                        Text("Test SS")
                    }
                    Button(onClick = { append("Ctrl: ${BaasBridge.testControl()}") }) {
                        Text("Test Tap")
                    }
                    Button(onClick = { append("OCR: ${BaasBridge.testOcr()}") }) {
                        Text("Test OCR")
                    }
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        append("PyDiag:\n${runCatching { Python.getInstance().getModule("main_android").callAttr("diagnostic", "android").toString() }.getOrElse { it.message ?: "error" }}")
                    }) {
                        Text("Py Diagnostic")
                    }
                    Button(onClick = {
                        append("Diag:\n${BaasBridge.diagnosticInfo()}")
                    }) {
                        Text("Refresh Diagnostic")
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
