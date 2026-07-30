package com.aliothmoon.maameow.remote;

import android.os.Parcel;
import android.os.Parcelable;

import java.util.ArrayList;
import java.util.List;

/**
 * Parcelable request used by RemoteService.grantPermissions().
 */
public class PermissionGrantRequest implements Parcelable {
    private String packageName;
    private List<String> permissions;

    public PermissionGrantRequest(String packageName, List<String> permissions) {
        this.packageName = packageName;
        this.permissions = permissions != null ? permissions : new ArrayList<>();
    }

    protected PermissionGrantRequest(Parcel in) {
        packageName = in.readString();
        permissions = in.createStringArrayList();
        if (permissions == null) {
            permissions = new ArrayList<>();
        }
    }

    public String getPackageName() {
        return packageName;
    }

    public List<String> getPermissions() {
        return permissions;
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeString(packageName);
        dest.writeStringList(permissions);
    }

    @Override
    public int describeContents() {
        return 0;
    }

    public static final Creator<PermissionGrantRequest> CREATOR = new Creator<PermissionGrantRequest>() {
        @Override
        public PermissionGrantRequest createFromParcel(Parcel in) {
            return new PermissionGrantRequest(in);
        }

        @Override
        public PermissionGrantRequest[] newArray(int size) {
            return new PermissionGrantRequest[size];
        }
    };
}
