package org.test.cloudpatcher

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.OpenableColumns
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.PyException
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

class MainActivity : AppCompatActivity() {

    private lateinit var btnOriginalFile: Button
    private lateinit var tvOriginalFileName: TextView
    private lateinit var btnPatchFile: Button
    private lateinit var tvPatchFileName: TextView
    private lateinit var btnStartPatch: Button
    private lateinit var tvStatus: TextView
    private lateinit var progressBar: ProgressBar

    private var originalFileUri: Uri? = null
    private var patchFileUri: Uri? = null

    // Register Activity Result Launchers
    private val selectOriginalLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK) {
            result.data?.data?.let { uri ->
                originalFileUri = uri
                tvOriginalFileName.text = getFileName(uri)
                checkReady()
            }
        }
    }

    private val selectPatchLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK) {
            result.data?.data?.let { uri ->
                patchFileUri = uri
                tvPatchFileName.text = getFileName(uri)
                checkReady()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize Chaquopy
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        btnOriginalFile = findViewById(R.id.btnOriginalFile)
        tvOriginalFileName = findViewById(R.id.tvOriginalFileName)
        btnPatchFile = findViewById(R.id.btnPatchFile)
        tvPatchFileName = findViewById(R.id.tvPatchFileName)
        btnStartPatch = findViewById(R.id.btnStartPatch)
        tvStatus = findViewById(R.id.tvStatus)
        progressBar = findViewById(R.id.progressBar)

        btnOriginalFile.setOnClickListener {
            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "*/*"
            }
            selectOriginalLauncher.launch(intent)
        }

        btnPatchFile.setOnClickListener {
            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "*/*" // Can't filter extension accurately without MIME type, so "*/*"
            }
            selectPatchLauncher.launch(intent)
        }

        btnStartPatch.setOnClickListener {
            startPatching()
        }
    }

    private fun checkReady() {
        if (originalFileUri != null && patchFileUri != null) {
            btnStartPatch.isEnabled = true
            btnStartPatch.setBackgroundColor(resources.getColor(R.color.btn_start_bg, null))
        }
    }

    private fun startPatching() {
        btnStartPatch.isEnabled = false
        btnStartPatch.setBackgroundColor(resources.getColor(R.color.btn_start_disabled, null))
        progressBar.progress = 10
        tvStatus.text = "جاري تحضير الملفات..."
        tvStatus.setTextColor(resources.getColor(R.color.white, null))

        // Run in background thread
        Thread {
            try {
                // 1. Copy URIs to temp files so Python can access them via File path
                val origTempFile = File(cacheDir, "original_temp.bin")
                copyUriToFile(originalFileUri!!, origTempFile)
                
                updateProgress(30, "تم نسخ الملف الأصلي... جاري نسخ الباتش...")
                
                val patchTempFile = File(cacheDir, "patch_temp.xz")
                copyUriToFile(patchFileUri!!, patchTempFile)
                
                updateProgress(50, "جاري تطبيق الباتش (يستغرق بعض الوقت)...")

                // 2. Determine output directory (Downloads)
                // Use app-specific external storage folder or external downloads
                val outputDir = getExternalFilesDir("Downloads") ?: filesDir

                // 3. Call Python snippet
                val py = Python.getInstance()
                val patchLogic = py.getModule("patch_logic")
                
                val outPath = patchLogic.callAttr("apply_patch", 
                    origTempFile.absolutePath, 
                    patchTempFile.absolutePath, 
                    outputDir.absolutePath
                ).toString()

                updateProgress(100, "اكتمل بنجاح!")
                showSuccess(outPath)

                // Cleanup temp files
                origTempFile.delete()
                patchTempFile.delete()

            } catch (e: PyException) {
                showError("خطأ في سكربت بايثون: ${e.message}")
            } catch (e: Exception) {
                showError("خطأ: ${e.message}")
            }
        }.start()
    }

    private fun updateProgress(progress: Int, status: String) {
        Handler(Looper.getMainLooper()).post {
            progressBar.progress = progress
            tvStatus.text = status
        }
    }

    private fun showSuccess(path: String) {
        Handler(Looper.getMainLooper()).post {
            btnStartPatch.isEnabled = true
            btnStartPatch.setBackgroundColor(resources.getColor(R.color.btn_start_bg, null))
            btnStartPatch.text = "✅ اكتمل بنجاح!"
            tvStatus.setTextColor(resources.getColor(R.color.status_success, null))
            
            AlertDialog.Builder(this)
                .setTitle("🎉 نجاح")
                .setMessage("تم دمج التحديث بنجاح.\nتم حفظ الملف في:\n\n$path")
                .setPositiveButton("إغلاق", null)
                .show()
        }
    }

    private fun showError(error: String) {
        Handler(Looper.getMainLooper()).post {
            btnStartPatch.isEnabled = true
            btnStartPatch.setBackgroundColor(resources.getColor(R.color.btn_start_bg, null))
            tvStatus.text = "حدث خطأ!"
            tvStatus.setTextColor(resources.getColor(R.color.btn_patch_bg, null)) // Red/Orange ish

            AlertDialog.Builder(this)
                .setTitle("❌ خطأ")
                .setMessage("حدث خطأ أثناء العملية:\n\n$error")
                .setPositiveButton("إغلاق", null)
                .show()
        }
    }

    private fun getFileName(uri: Uri): String {
        var result: String? = null
        if (uri.scheme == "content") {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if (index != -1) result = cursor.getString(index)
                }
            }
        }
        if (result == null) {
            result = uri.path
            val cut = result?.lastIndexOf('/')
            if (cut != null && cut != -1) {
                result = result!!.substring(cut + 1)
            }
        }
        return result ?: "Unknown"
    }

    private fun copyUriToFile(uri: Uri, destFile: File) {
        contentResolver.openInputStream(uri)?.use { inputStream: InputStream ->
            FileOutputStream(destFile).use { outputStream ->
                val buffer = ByteArray(4 * 1024)
                var read: Int
                while (inputStream.read(buffer).also { read = it } != -1) {
                    outputStream.write(buffer, 0, read)
                }
                outputStream.flush()
            }
        }
    }
}
