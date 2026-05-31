package in.mywealthpilot.twa;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Manages SMS sync preferences — stores the sync token and last sync timestamp.
 */
public class SmsPreferences {
    private static final String PREFS_NAME = "sms_sync_prefs";
    private static final String KEY_TOKEN = "sms_sync_token";
    private static final String KEY_ENABLED = "sms_sync_enabled";
    private static final String KEY_LAST_SYNC = "last_sync_timestamp";
    private static final String KEY_LAST_INBOX_SYNC = "last_inbox_sync_timestamp";

    private final SharedPreferences prefs;

    public SmsPreferences(Context context) {
        prefs = context.getApplicationContext()
                .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public String getToken() {
        return prefs.getString(KEY_TOKEN, "");
    }

    public void setToken(String token) {
        prefs.edit().putString(KEY_TOKEN, token).apply();
    }

    public boolean isEnabled() {
        return prefs.getBoolean(KEY_ENABLED, false);
    }

    public void setEnabled(boolean enabled) {
        prefs.edit().putBoolean(KEY_ENABLED, enabled).apply();
    }

    public long getLastSyncTimestamp() {
        return prefs.getLong(KEY_LAST_SYNC, 0);
    }

    public void setLastSyncTimestamp(long timestamp) {
        prefs.edit().putLong(KEY_LAST_SYNC, timestamp).apply();
    }

    public long getLastInboxSyncTimestamp() {
        return prefs.getLong(KEY_LAST_INBOX_SYNC, 0);
    }

    public void setLastInboxSyncTimestamp(long timestamp) {
        prefs.edit().putLong(KEY_LAST_INBOX_SYNC, timestamp).apply();
    }

    public void clear() {
        prefs.edit().clear().apply();
    }
}
