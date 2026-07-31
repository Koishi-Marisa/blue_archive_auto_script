package top.qwq123.baas.bridge;

import android.app.Activity;

import top.qwq123.baas.shizuku.ShizukuHelper;

public class BaasBridge {
    private static Activity sActivity;

    public static void init(Activity activity) {
        sActivity = activity;
    }

    public static boolean isShizukuGranted() {
        return ShizukuHelper.isGranted();
    }

    public static void requestShizukuPermission(int requestCode) {
        if (sActivity != null) {
            ShizukuHelper.requestPermission(requestCode);
        }
    }

    public static String executeShell(String command) {
        return ShizukuHelper.execute(command);
    }

    public static byte[] executeShellRaw(String command) {
        return ShizukuHelper.executeRaw(command);
    }

    public static boolean tap(int x, int y) {
        String result = ShizukuHelper.execute("input tap " + x + " " + y);
        return !result.startsWith("ERROR:");
    }

    public static boolean swipe(int x1, int y1, int x2, int y2, int duration) {
        String result = ShizukuHelper.execute("input swipe " + x1 + " " + y1 + " " + x2 + " " + y2 + " " + duration);
        return !result.startsWith("ERROR:");
    }

    public static boolean inputText(String text) {
        String escaped = text.replace("'", "'\\''");
        String result = ShizukuHelper.execute("input text '" + escaped + "'");
        return !result.startsWith("ERROR:");
    }

    public static String diagnosticInfo() {
        return ShizukuHelper.info();
    }

    // Methods matching core/device/android_bridge.py expectations

    public static byte[] screenshotJpeg() {
        return ShizukuHelper.executeRaw("screencap -p");
    }

    public static String screenshotSize() {
        String output = ShizukuHelper.execute("wm size");
        if (output.startsWith("ERROR:")) {
            return "";
        }
        // Typical output: "Physical size: 1080x2400" or "Override size: 1080x2400"
        for (String line : output.split("\\n")) {
            int idx = line.indexOf("size:");
            if (idx >= 0) {
                String size = line.substring(idx + 5).trim();
                String[] parts = size.split("x");
                if (parts.length == 2) {
                    return size;
                }
            }
        }
        return "";
    }

    public static boolean click(int x, int y) {
        return tap(x, y);
    }

    public static boolean longClick(int x, int y, int duration) {
        return swipe(x, y, x, y, duration);
    }

    public static String ocr(byte[] data, int w, int h, String language) {
        // TODO: implement on-device OCR or delegate to Python OCR server.
        // Returning empty result for now so BAAS core does not crash on import.
        return "[]";
    }
}
