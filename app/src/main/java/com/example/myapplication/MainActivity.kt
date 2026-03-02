package com.example.myapplication

import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
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
import org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream
import org.apache.commons.compress.compressors.xz.XZCompressorInputStream
import java.io.*

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
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    LocalPatcherApp()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LocalPatcherApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    // متغيرات الواجهة
    var operationMode by remember { mutableStateOf("PATCH") } // PATCH or DECOMPRESS
    
    // الملفات المختارة (URI)
    var originalFileUri by remember { mutableStateOf<Uri?>(null) }
    var patchFileUri by remember { mutableStateOf<Uri?>(null) } // الملف المضغوط .xz
    
    var statusMessage by remember { mutableStateOf("") }
    var isProcessing by remember { mutableStateOf(false) }

    // مُشغلات اختيار الملفات
    val pickOriginal = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) originalFileUri = uri
    }
    val pickPatch = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) patchFileUri = uri
    }

    // مُشغل حفظ الملف الناتج
    val saveResult = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("*/*")) { outputUri ->
        if (outputUri != null) {
            isProcessing = true
            statusMessage = "⏳ جاري المعالجة..."
            
            scope.launch(Dispatchers.IO) {
                try {
                    if (operationMode == "PATCH") {
                        // 1. فك ضغط الباتش (XZ) مؤقتاً
                        // 2. تطبيق الباتش على الملف الأصلي
                        applyPatchLogic(context, originalFileUri!!, patchFileUri!!, outputUri)
                        withContext(Dispatchers.Main) { statusMessage = "✅ تم دمج الباتش بنجاح!" }
                    } else {
                        // مجرد فك ضغط
                        decompressLogic(context, patchFileUri!!, outputUri)
                        withContext(Dispatchers.Main) { statusMessage = "✅ تم فك الضغط بنجاح!" }
                    }
                } catch (e: Exception) {
                    withContext(Dispatchers.Main) { statusMessage = "❌ خطأ: ${e.message}" }
                    e.printStackTrace()
                } finally {
                    isProcessing = false
                }
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(scrollState),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "🛠️ أدوات الملفات المحلية",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 20.dp)
        )

        // 1. اختيار الوضع
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
            FilterChip(
                selected = operationMode == "PATCH",
                onClick = { operationMode = "PATCH" },
                label = { Text("دمج باتش (.xz)") },
                leadingIcon = { if (operationMode == "PATCH") Icon(Icons.Default.Build, null) }
            )
            FilterChip(
                selected = operationMode == "DECOMPRESS",
                onClick = { operationMode = "DECOMPRESS" },
                label = { Text("فك ضغط (.xz)") },
                leadingIcon = { if (operationMode == "DECOMPRESS") Icon(Icons.Default.Menu, null) }
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // 2. أزرار اختيار الملفات
        if (operationMode == "PATCH") {
            FilePickerButton(
                title = "1. اختر الملف الأصلي (من هاتفك)",
                fileName = getFileName(context, originalFileUri),
                onClick = { pickOriginal.launch(arrayOf("*/*")) }
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        FilePickerButton(
            title = if (operationMode == "PATCH") "2. اختر ملف الباتش المضغوط (.xz)" else "اختر الملف المضغوط (.xz)",
            fileName = getFileName(context, patchFileUri),
            onClick = { pickPatch.launch(arrayOf("application/x-xz", "*/*")) }
        )

        Spacer(modifier = Modifier.height(32.dp))

        // 3. زر البدء
        Button(
            onClick = {
                val fileName = if (operationMode == "PATCH") "patched_file.bin" else "decompressed_file.bin"
                saveResult.launch(fileName)
            },
            enabled = !isProcessing && patchFileUri != null && (operationMode != "PATCH" || originalFileUri != null),
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            if (isProcessing) {
                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("جاري العمل...")
            } else {
                Text(if (operationMode == "PATCH") "⚡ بدء الدمج وحفظ النتيجة" else "⚡ بدء فك الضغط والحفظ")
            }
        }

        if (statusMessage.isNotEmpty()) {
            Spacer(modifier = Modifier.height(24.dp))
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF2D2D2D))) {
                Text(
                    text = statusMessage,
                    modifier = Modifier.padding(16.dp),
                    color = if (statusMessage.startsWith("❌")) Color.Red else Color.Green
                )
            }
        }
    }
}

@Composable
fun FilePickerButton(title: String, fileName: String?, onClick: () -> Unit) {
    OutlinedButton(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium
    ) {
        Column(modifier = Modifier.padding(8.dp), horizontalAlignment = Alignment.Start) {
            Text(text = title, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.secondary)
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = fileName ?: "لم يتم اختيار ملف", color = Color.White)
        }
    }
}

// ==========================================
// 🧠 المنطق البرمجي (فك الضغط والباتش)
// ==========================================

fun decompressLogic(context: Context, inputUri: Uri, outputUri: Uri) {
    context.contentResolver.openInputStream(inputUri)?.use { inputStream ->
        context.contentResolver.openOutputStream(outputUri)?.use { outputStream ->
            // فك ضغط XZ باستخدام مكتبة Commons Compress
            XZCompressorInputStream(inputStream).use { xzIn ->
                xzIn.copyTo(outputStream)
            }
        }
    }
}

fun applyPatchLogic(context: Context, originalUri: Uri, patchXzUri: Uri, outputUri: Uri) {
    // 1. فك ضغط الباتش (.xz) إلى الذاكرة أو ملف مؤقت
    // بما أن الباتش قد يكون كبيراً، سنفكه ونقرأه كـ Stream
    
    val originalStream = BufferedInputStream(context.contentResolver.openInputStream(originalUri))
    val outputStream = BufferedOutputStream(context.contentResolver.openOutputStream(outputUri))
    
    // فتح ملف الباتش المضغوط
    val compressedPatchStream = context.contentResolver.openInputStream(patchXzUri)
    val xzStream = XZCompressorInputStream(compressedPatchStream) // فك ضغط XZ أولاً
    
    // الآن لدينا (xzStream) وهو عبارة عن ملف bsdiff الخام
    // نقوم بتمريره لدالة تطبيق الباتش
    BsPatch.apply(originalStream, xzStream, outputStream)
}

// ==========================================
// 🛠️ محرك BsPatch (مكتوب يدوياً بلغة Kotlin)
// ==========================================
object BsPatch {
    fun apply(oldFile: InputStream, patchFile: InputStream, newFile: OutputStream) {
        val patchData = patchFile.readBytes() // قراءة الباتش المفكوك بالكامل للذاكرة (ضروري للقفز seek)
        
        // التحقق من الهيدر (BSDIFF40)
        val header = patchData.copyOfRange(0, 8)
        if (String(header) != "BSDIFF40") throw Exception("الملف ليس بصيغة Patch صالحة!")

        // قراءة أطوال الكتل (Header parsing)
        val ctrlBlockLen = readLong(patchData, 8)
        val diffBlockLen = readLong(patchData, 16)
        val newSize = readLong(patchData, 24)

        // تحديد بداية الكتل داخل الباتش
        val ctrlBlockIn = ByteArrayInputStream(patchData, 32, ctrlBlockLen.toInt())
        val diffBlockIn = ByteArrayInputStream(patchData, 32 + ctrlBlockLen.toInt(), diffBlockLen.toInt())
        val extraBlockIn = ByteArrayInputStream(patchData, 32 + ctrlBlockLen.toInt() + diffBlockLen.toInt(), patchData.size - (32 + ctrlBlockLen.toInt() + diffBlockLen.toInt()))

        // فك ضغط الكتل الداخلية (BZip2)
        val ctrlStream = BZip2CompressorInputStream(ctrlBlockIn)
        val diffStream = BZip2CompressorInputStream(diffBlockIn)
        val extraStream = BZip2CompressorInputStream(extraBlockIn)

        // قراءة الملف الأصلي بالكامل (نحتاج الوصول العشوائي له)
        val oldData = oldFile.readBytes()
        var newPos = 0
        var oldPos = 0

        while (newPos < newSize) {
            // قراءة التحكم (3 أرقام Long)
            val ctrl = LongArray(3)
            for (i in 0..2) ctrl[i] = readLongFromStream(ctrlStream)

            val addLen = ctrl[0].toInt()
            val copyLen = ctrl[1].toInt()
            val seekLen = ctrl[2].toInt()

            // 1. Add Block: إضافة الفروقات للملف القديم
            val diffData = ByteArray(addLen)
            diffStream.read(diffData) // قراءة من Diff Block
            
            for (i in 0 until addLen) {
                val oldByte = if (oldPos + i in oldData.indices) oldData[oldPos + i] else 0
                newFile.write((oldByte + diffData[i]) and 0xFF)
            }
            newPos += addLen
            oldPos += addLen

            // 2. Copy Block: نسخ بيانات جديدة تماماً (Extra Block)
            val extraData = ByteArray(copyLen)
            extraStream.read(extraData)
            newFile.write(extraData)
            
            newPos += copyLen
            oldPos += seekLen
        }

        newFile.flush()
        newFile.close()
    }

    // دالة مساعدة لقراءة Long من مصفوفة بايت (Little Endian)
    private fun readLong(data: ByteArray, offset: Int): Long {
        var result: Long = 0
        for (i in 0..7) {
            result = result or ((data[offset + i].toLong() and 0xFF) shl (8 * i))
        }
        // معالجة الإشارة (Negative handling for bsdiff format)
        return if (result and (1L shl 63) != 0L) -(result and (1L shl 63).inv()) else result
    }

    // دالة مساعدة لقراءة Long من ستريم (للكتل المضغوطة)
    private fun readLongFromStream(input: InputStream): Long {
        val buffer = ByteArray(8)
        var bytesRead = 0
        while (bytesRead < 8) {
            val count = input.read(buffer, bytesRead, 8 - bytesRead)
            if (count == -1) break
            bytesRead += count
        }
        return readLong(buffer, 0)
    }
}

// دالة مساعدة لجلب اسم الملف للعرض
fun getFileName(context: Context, uri: Uri?): String? {
    if (uri == null) return null
    var result: String? = null
    if (uri.scheme == "content") {
        context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex("_display_name")
                if (index != -1) result = cursor.getString(index)
            }
        }
    }
    if (result == null) {
        result = uri.path
        val cut = result?.lastIndexOf('/')
        if (cut != -1 && cut != null) result = result?.substring(cut + 1)
    }
    return result
}
