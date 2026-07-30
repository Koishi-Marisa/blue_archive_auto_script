package top.qwq123.baas.bridge

import android.graphics.Bitmap
import android.graphics.Point
import android.util.Log
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.chinese.ChineseTextRecognizerOptions
import com.google.mlkit.vision.text.japanese.JapaneseTextRecognizerOptions
import com.google.mlkit.vision.text.korean.KoreanTextRecognizerOptions
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import org.json.JSONArray
import org.json.JSONObject

/**
 * On-device OCR using Google ML Kit Text Recognition.
 */
class OcrService {
    private val TAG = "OcrService"

    private val recognizers = mapOf(
        "zh-cn" to TextRecognition.getClient(ChineseTextRecognizerOptions.Builder().build()),
        "ja-jp" to TextRecognition.getClient(JapaneseTextRecognizerOptions.Builder().build()),
        "ko-kr" to TextRecognition.getClient(KoreanTextRecognizerOptions.Builder().build()),
        "en-us" to TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS),
    )

    fun recognize(bitmap: Bitmap, language: String = "zh-cn", callback: (String) -> Unit) {
        val image = InputImage.fromBitmap(bitmap, 0)
        val recognizer = recognizers[language] ?: recognizers["en-us"]!!
        recognizer.process(image)
            .addOnSuccessListener { visionText ->
                callback(textToJson(visionText))
            }
            .addOnFailureListener { e ->
                Log.e(TAG, "OCR failed", e)
                callback("[]")
            }
    }

    private fun textToJson(visionText: com.google.mlkit.vision.text.Text): String {
        val result = JSONArray()
        for (block in visionText.textBlocks) {
            for (line in block.lines) {
                for (element in line.elements) {
                    val points = element.cornerPoints ?: element.boundingBox?.let { box ->
                        arrayOf(
                            Point(box.left, box.top),
                            Point(box.right, box.top),
                            Point(box.right, box.bottom),
                            Point(box.left, box.bottom)
                        )
                    } ?: continue
                    val boxArray = JSONArray()
                    for (p in points) {
                        val pt = JSONArray()
                        pt.put(p.x)
                        pt.put(p.y)
                        boxArray.put(pt)
                    }
                    val obj = JSONObject()
                    obj.put("text", element.text)
                    obj.put("box", boxArray)
                    obj.put("score", 1.0)
                    result.put(obj)
                }
            }
        }
        return result.toString()
    }
}
