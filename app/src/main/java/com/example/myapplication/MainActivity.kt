package com.example.myapplication

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.* // هذا يستورد كل شيء بما في ذلك Experimental
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFFBB86FC),
                    secondary = Color(0xFF03DAC5),
                    background = Color(0xFF121212),
                    surface = Color(0xFF1E1E1E)
                )
            ) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    CloudPatcherApp()
                }
            }
        }
    }
}

// ==============================
// 🎨 الواجهة الرسومية (UI)
// ==============================

// ✅ التعديل هنا: إضافة هذا السطر للسماح باستخدام FilterChip و Card
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CloudPatcherApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    var serverUrl by remember { mutableStateOf("") }
    var operationMode by remember { mutableStateOf("إنشاء باتش بين ملفين وضغطه") }
    var originalUrl by remember { mutableStateOf("") }
    var modifiedUrl by remember { mutableStateOf("") }
    
    var isLoading by remember { mutableStateOf(false) }
    var resultHash by remember { mutableStateOf("") }
    var downloadLink by remember { mutableStateOf("") }
    var errorMessage by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(scrollState),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "🚀 Cloud Patcher Client",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        Card(
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("🔗 إعداد الاتصال", fontWeight = FontWeight.Bold, color = Color.White)
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = serverUrl,
                    onValueChange = { serverUrl = it },
                    label = { Text("رابط Gradio العام (مثال: https://xxxx.gradio.live)") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            // FilterChip هو المسبب للمشكلة، والآن تم حله بواسطة @OptIn
            FilterChip(
                selected = operationMode == "إنشاء باتش بين ملفين وضغطه",
                onClick = { operationMode = "إنشاء باتش بين ملفين وضغطه" },
                label = { Text("إنشاء Patch") },
                leadingIcon = { if (operationMode == "إنشاء باتش بين ملفين وضغطه") Icon(Icons.Default.Check, null) }
            )
            FilterChip(
                selected = operationMode == "تحميل ملف وضغطه مباشرة",
                onClick = { operationMode = "تحميل ملف وضغطه مباشرة" },
                label = { Text("ضغط مباشر") },
                leadingIcon = { if (operationMode == "تحميل ملف وضغطه مباشرة") Icon(Icons.Default.Check, null) }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = originalUrl,
            onValueChange = { originalUrl = it },
            label = { Text(if (operationMode == "تحميل ملف وضغطه مباشرة") "رابط الملف للتحميل" else "رابط الملف الأصلي") },
            modifier = Modifier.fillMaxWidth(),
            leadingIcon = { Icon(Icons.Default.Home, contentDescription = null) }
        )

        if (operationMode == "إنشاء باتش بين ملفين وضغطه") {
            Spacer(modifier = Modifier.height(8.dp))
            OutlinedTextField(
                value = modifiedUrl,
                onValueChange = { modifiedUrl = it },
                label = { Text("رابط الملف المعدل") },
                modifier = Modifier.fillMaxWidth(),
                leadingIcon = { Icon(Icons.Default.Edit, contentDescription = null) }
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                if (serverUrl.isBlank() || originalUrl.isBlank()) {
                    Toast.makeText(context, "تأكد من إدخال الرابط وعنوان السيرفر", Toast.LENGTH_SHORT).show()
                } else {
                    isLoading = true
                    errorMessage = ""
                    resultHash = ""
                    downloadLink = ""
                    
                    scope.launch {
                        processTask(
                            serverUrl, operationMode, originalUrl, modifiedUrl,
                            onSuccess = { link, hash ->
                                isLoading = false
                                downloadLink = link
                                resultHash = hash
                            },
                            onError = { error ->
                                isLoading = false
                                errorMessage = error
                            }
                        )
                    }
                }
            },
            enabled = !isLoading,
            modifier = Modifier.fillMaxWidth().height(50.dp)
        ) {
            if (isLoading) {
                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("جاري المعالجة...")
            } else {
                Text("⚡ بدء العملية")
            }
        }

        if (errorMessage.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = "❌ خطأ: $errorMessage", color = Color.Red)
        }

        if (resultHash.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFF2D2D2D)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("✅ تمت العملية بنجاح!", color = Color.Green, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    SelectionContainer {
                        Text(text = resultHash, color = Color.White, fontSize = 12.sp)
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Button(
                        onClick = { downloadFile(context, downloadLink) },
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.ArrowDropDown, null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("📥 تحميل الملف الناتج (.xz)", color = Color.Black)
                    }
                }
            }
        }
    }
}

// ==============================
// 🌐 منطق الاتصال (Networking Logic)
// ==============================
suspend fun processTask(
    baseUrl: String,
    mode: String,
    url1: String,
    url2: String,
    onSuccess: (String, String) -> Unit,
    onError: (String) -> Unit
) {
    withContext(Dispatchers.IO) {
        try {
            val cleanUrl = baseUrl.trim().removeSuffix("/")
            val endpoint = "$cleanUrl/run/process_task"

            val jsonBody = JSONObject()
            val dataArray = org.json.JSONArray()
            dataArray.put(mode)
            dataArray.put(url1)
            dataArray.put(url2)
            jsonBody.put("data", dataArray)

            val client = OkHttpClient.Builder()
                .connectTimeout(60, TimeUnit.SECONDS)
                .readTimeout(300, TimeUnit.SECONDS)
                .build()

            val request = Request.Builder()
                .url(endpoint)
                .post(jsonBody.toString().toRequestBody("application/json".toMediaTypeOrNull()))
                .build()

            val response = client.newCall(request).execute()
            val responseBody = response.body?.string()

            if (!response.isSuccessful || responseBody == null) {
                withContext(Dispatchers.Main) { onError("فشل الاتصال: رمز ${response.code}") }
                return@withContext
            }

            val jsonResponse = JSONObject(responseBody)
            val dataOutput = jsonResponse.getJSONArray("data")
            
            val fileObj = dataOutput.getJSONObject(0)
            val fileUrl = fileObj.getString("url")
            val finalDownloadUrl = if (fileUrl.startsWith("http")) fileUrl else "$cleanUrl/file=$fileUrl"
            
            val hashText = dataOutput.getString(1)

            withContext(Dispatchers.Main) {
                onSuccess(finalDownloadUrl, hashText)
            }

        } catch (e: Exception) {
            withContext(Dispatchers.Main) { onError(e.message ?: "حدث خطأ غير معروف") }
        }
    }
}

fun downloadFile(context: Context, url: String) {
    try {
        val request = DownloadManager.Request(Uri.parse(url))
        request.setTitle("Cloud Patcher File")
        request.setDescription("جاري تحميل الملف المضغوط...")
        request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
        request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "patched_file.xz")
        
        val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        manager.enqueue(request)
        Toast.makeText(context, "بدأ التحميل في الخلفية ⬇️", Toast.LENGTH_LONG).show()
    } catch (e: Exception) {
        Toast.makeText(context, "فشل بدء التحميل: ${e.message}", Toast.LENGTH_SHORT).show()
    }
}
