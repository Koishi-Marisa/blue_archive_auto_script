package top.qwq123.baas;

import android.os.Bundle;

import org.kivy.android.PythonActivity;

import top.qwq123.baas.bridge.BaasBridge;

public class MainActivity extends PythonActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BaasBridge.init(this);
    }
}
