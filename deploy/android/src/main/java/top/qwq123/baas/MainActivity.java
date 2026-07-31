package top.qwq123.baas;

import android.os.Bundle;

import org.qtproject.qt.android.bindings.QtActivity;

import top.qwq123.baas.bridge.BaasBridge;

public class MainActivity extends QtActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BaasBridge.init(this);
    }
}
