package com.aliothmoon.maameow.remote;

import android.os.Parcel;
import android.os.Parcelable;

import java.util.HashMap;
import java.util.Map;

/**
 * Parcelable result used by RemoteService.grantPermissions().
 */
public class PermissionStateInfo implements Parcelable {
    private String packageName;
    private Map<String, Integer> states;

    public PermissionStateInfo(String packageName, Map<String, Integer> states) {
        this.packageName = packageName;
        this.states = states != null ? states : new HashMap<>();
    }

    protected PermissionStateInfo(Parcel in) {
        packageName = in.readString();
        int size = in.readInt();
        states = new HashMap<>(size);
        for (int i = 0; i < size; i++) {
            String key = in.readString();
            int value = in.readInt();
            states.put(key, value);
        }
    }

    public String getPackageName() {
        return packageName;
    }

    public Map<String, Integer> getStates() {
        return states;
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeString(packageName);
        dest.writeInt(states.size());
        for (Map.Entry<String, Integer> entry : states.entrySet()) {
            dest.writeString(entry.getKey());
            dest.writeInt(entry.getValue());
        }
    }

    @Override
    public int describeContents() {
        return 0;
    }

    public static final Creator<PermissionStateInfo> CREATOR = new Creator<PermissionStateInfo>() {
        @Override
        public PermissionStateInfo createFromParcel(Parcel in) {
            return new PermissionStateInfo(in);
        }

        @Override
        public PermissionStateInfo[] newArray(int size) {
            return new PermissionStateInfo[size];
        }
    };
}
