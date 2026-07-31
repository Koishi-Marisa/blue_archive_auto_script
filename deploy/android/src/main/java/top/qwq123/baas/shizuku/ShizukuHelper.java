package top.qwq123.baas.shizuku;

import android.annotation.SuppressLint;
import android.content.pm.PackageManager;
import android.os.RemoteException;
import android.util.Log;

import java.nio.charset.Charset;

import rikka.shizuku.Shizuku;

public class ShizukuHelper {
    private static final String TAG = "ShizukuHelper";

    public static boolean isInstalled() {
        return Shizuku.pingBinder();
    }

    public static boolean isGranted() {
        try {
            return Shizuku.isPreV11() || Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED;
        } catch (Throwable e) {
            return false;
        }
    }

    public static void requestPermission(int requestCode) {
        Shizuku.requestPermission(requestCode);
    }

    public static String info() {
        boolean installed = isInstalled();
        boolean granted = isGranted();
        String version;
        try {
            version = Shizuku.getBinder() != null ? "binder ok" : "binder null";
        } catch (Throwable e) {
            version = "binder err: " + e.getClass().getSimpleName();
        }
        return "installed=" + installed + ", granted=" + granted + ", " + version;
    }

    public static String execute(String command) {
        Result<byte[]> result = executeInternal(command, true);
        if (result.isSuccess()) {
            return new String(result.getValue(), Charset.defaultCharset());
        }
        return "ERROR: " + result.getError();
    }

    public static byte[] executeRaw(String command) {
        Result<byte[]> result = executeInternal(command, false);
        if (result.isSuccess()) {
            return result.getValue();
        }
        return new byte[0];
    }

    private static Result<byte[]> executeInternal(String command, boolean redirectErr) {
        if (!isInstalled()) {
            return Result.failure("Shizuku is not installed or running");
        }
        if (!isGranted()) {
            return Result.failure("Shizuku permission not granted");
        }
        try {
            Log.d(TAG, "execute: " + command + " (redirectErr=" + redirectErr + ")");
            Process process = newProcessViaReflection(
                new String[]{"sh", "-c", command},
                redirectErr ? new String[]{"LD_LIBRARY_PATH=/data/local/tmp"} : null,
                null
            );
            if (process == null) {
                return Result.failure("Shizuku returned null process");
            }
            byte[] output;
            try (java.io.InputStream is = process.getInputStream()) {
                output = readAllBytes(is);
            }
            int exitCode = process.waitFor();
            Log.d(TAG, "execute finished: exit=" + exitCode + ", bytes=" + output.length);
            return Result.success(output);
        } catch (RemoteException e) {
            Log.e(TAG, "execute RemoteException", e);
            return Result.failure(e.getMessage());
        } catch (Exception e) {
            Log.e(TAG, "execute Exception", e);
            return Result.failure(e.getMessage());
        }
    }

    @SuppressLint("PrivateApi")
    private static Process newProcessViaReflection(String[] cmd, String[] env, String dir) throws Exception {
        java.lang.reflect.Method method = Shizuku.class.getDeclaredMethod(
            "newProcess",
            String[].class,
            String[].class,
            String.class
        );
        method.setAccessible(true);
        return (Process) method.invoke(null, (Object) cmd, (Object) env, dir);
    }

    private static byte[] readAllBytes(java.io.InputStream is) throws java.io.IOException {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int len;
        while ((len = is.read(buffer)) != -1) {
            bos.write(buffer, 0, len);
        }
        return bos.toByteArray();
    }

    public static class Result<T> {
        private final boolean success;
        private final T value;
        private final String error;

        private Result(boolean success, T value, String error) {
            this.success = success;
            this.value = value;
            this.error = error;
        }

        public static <T> Result<T> success(T value) {
            return new Result<>(true, value, null);
        }

        public static <T> Result<T> failure(String error) {
            return new Result<>(false, null, error);
        }

        public boolean isSuccess() {
            return success;
        }

        public T getValue() {
            return value;
        }

        public String getError() {
            return error;
        }
    }
}
