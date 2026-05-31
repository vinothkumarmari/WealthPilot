package in.mywealthpilot.twa;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

/**
 * Activity for configuring SMS auto-sync.
 * Users paste their sync token from the web profile page and grant SMS permissions.
 */
public class SmsSyncSetupActivity extends Activity {
    private static final String TAG = "SmsSyncSetup";
    private static final int PERMISSION_REQUEST_CODE = 1001;

    private EditText tokenInput;
    private Switch enableSwitch;
    private TextView statusText;
    private Button saveButton;
    private SmsPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        prefs = new SmsPreferences(this);

        // Build UI programmatically (no XML layout needed)
        android.widget.LinearLayout layout = new android.widget.LinearLayout(this);
        layout.setOrientation(android.widget.LinearLayout.VERTICAL);
        layout.setPadding(48, 48, 48, 48);
        layout.setBackgroundColor(0xFF1A1A2E);

        // Title
        TextView title = new TextView(this);
        title.setText("📱 SMS Auto-Sync Setup");
        title.setTextSize(22);
        title.setTextColor(0xFFFFFFFF);
        title.setPadding(0, 0, 0, 16);
        layout.addView(title);

        // Description
        TextView desc = new TextView(this);
        desc.setText("Automatically read bank SMS to add expenses & income to MyWealthPilot.\n\n" +
                "1. Enable SMS Sync in your Profile on mywealthpilot.in\n" +
                "2. Copy your SMS Sync Token from the Profile page\n" +
                "3. Paste it below and tap Save");
        desc.setTextSize(14);
        desc.setTextColor(0xFFAAAAAA);
        desc.setPadding(0, 0, 0, 32);
        layout.addView(desc);

        // Token input
        TextView tokenLabel = new TextView(this);
        tokenLabel.setText("SMS Sync Token:");
        tokenLabel.setTextSize(14);
        tokenLabel.setTextColor(0xFFCCCCCC);
        layout.addView(tokenLabel);

        tokenInput = new EditText(this);
        tokenInput.setHint("Paste your token here");
        tokenInput.setText(prefs.getToken());
        tokenInput.setTextColor(0xFFFFFFFF);
        tokenInput.setHintTextColor(0xFF666666);
        tokenInput.setBackgroundColor(0xFF2A2A3E);
        tokenInput.setPadding(24, 16, 24, 16);
        tokenInput.setSingleLine(true);
        layout.addView(tokenInput);

        // Spacer
        View spacer1 = new View(this);
        spacer1.setMinimumHeight(24);
        layout.addView(spacer1);

        // Enable switch
        enableSwitch = new Switch(this);
        enableSwitch.setText("Enable SMS Auto-Sync");
        enableSwitch.setTextColor(0xFFFFFFFF);
        enableSwitch.setChecked(prefs.isEnabled());
        layout.addView(enableSwitch);

        // Spacer
        View spacer2 = new View(this);
        spacer2.setMinimumHeight(32);
        layout.addView(spacer2);

        // Status
        statusText = new TextView(this);
        statusText.setTextSize(13);
        statusText.setTextColor(0xFF6C5CE7);
        updateStatus();
        layout.addView(statusText);

        // Spacer
        View spacer3 = new View(this);
        spacer3.setMinimumHeight(32);
        layout.addView(spacer3);

        // Save button
        saveButton = new Button(this);
        saveButton.setText("💾 Save & Enable");
        saveButton.setBackgroundColor(0xFF6C5CE7);
        saveButton.setTextColor(0xFFFFFFFF);
        saveButton.setOnClickListener(v -> saveSettings());
        layout.addView(saveButton);

        // Spacer
        View spacer4 = new View(this);
        spacer4.setMinimumHeight(16);
        layout.addView(spacer4);

        // Info text
        TextView realtimeInfo = new TextView(this);
        realtimeInfo.setText("📱 How it works:\n" +
                "• Real-time: New bank SMS are automatically detected and added\n" +
                "• Inbox Scan: Tap below to read recent bank SMS from your inbox\n" +
                "• Only bank/UPI transaction SMS are processed — personal messages are never read");
        realtimeInfo.setTextSize(13);
        realtimeInfo.setTextColor(0xFF6C5CE7);
        realtimeInfo.setPadding(0, 0, 0, 16);
        layout.addView(realtimeInfo);

        // Scan Inbox button
        Button scanBtn = new Button(this);
        scanBtn.setText("📥 Scan SMS Inbox (Last 7 Days)");
        scanBtn.setBackgroundColor(0xFF00B894);
        scanBtn.setTextColor(0xFFFFFFFF);
        scanBtn.setOnClickListener(v -> scanInbox(scanBtn));
        layout.addView(scanBtn);

        // Spacer
        View spacer5 = new View(this);
        spacer5.setMinimumHeight(16);
        layout.addView(spacer5);

        // Back button
        Button backBtn = new Button(this);
        backBtn.setText("← Back to App");
        backBtn.setBackgroundColor(0xFF2D3436);
        backBtn.setTextColor(0xFFCCCCCC);
        backBtn.setOnClickListener(v -> finish());
        layout.addView(backBtn);

        android.widget.ScrollView scrollView = new android.widget.ScrollView(this);
        scrollView.addView(layout);
        scrollView.setBackgroundColor(0xFF1A1A2E);
        setContentView(scrollView);
    }

    private void saveSettings() {
        String token = tokenInput.getText().toString().trim();
        boolean enabled = enableSwitch.isChecked();

        if (enabled && token.isEmpty()) {
            Toast.makeText(this, "Please paste your SMS Sync Token from the Profile page", Toast.LENGTH_LONG).show();
            return;
        }

        prefs.setToken(token);
        prefs.setEnabled(enabled);

        if (enabled) {
            // Request SMS permissions
            if (!hasSmsPermission()) {
                requestSmsPermission();
                return; // Will save after permission granted
            }
            // Real-time listener is now active via SmsBroadcastReceiver
            Toast.makeText(this, "✅ SMS sync enabled! New bank SMS will be auto-added.", Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "SMS sync disabled", Toast.LENGTH_SHORT).show();
        }

        updateStatus();
    }

    private boolean hasSmsPermission() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.RECEIVE_SMS) == PackageManager.PERMISSION_GRANTED
                && ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestSmsPermission() {
        ActivityCompat.requestPermissions(this,
                new String[]{
                        Manifest.permission.RECEIVE_SMS,
                        Manifest.permission.READ_SMS
                },
                PERMISSION_REQUEST_CODE);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode == PERMISSION_REQUEST_CODE) {
            boolean allGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }

            if (allGranted) {
                // Permission granted — real-time SMS listener is now active
                Toast.makeText(this, "✅ SMS sync enabled! New bank SMS will be auto-added.", Toast.LENGTH_LONG).show();
            } else {
                Toast.makeText(this, "SMS permission denied. SMS sync won't work without it.", Toast.LENGTH_LONG).show();
                prefs.setEnabled(false);
                enableSwitch.setChecked(false);
            }
            updateStatus();
        }
    }

    private void updateStatus() {
        StringBuilder sb = new StringBuilder();
        sb.append("Status: ");
        if (prefs.isEnabled() && !prefs.getToken().isEmpty()) {
            sb.append("✅ Active");
        } else {
            sb.append("⚫ Disabled");
        }
        sb.append("\nSMS Permission: ");
        boolean hasReceive = ContextCompat.checkSelfPermission(this, Manifest.permission.RECEIVE_SMS) == PackageManager.PERMISSION_GRANTED;
        boolean hasRead = ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED;
        if (hasReceive && hasRead) {
            sb.append("✅ Receive & Read Granted");
        } else if (hasReceive) {
            sb.append("⚠️ Receive Only (tap Save to grant Read)");
        } else {
            sb.append("❌ Not Granted");
        }

        long lastSync = prefs.getLastSyncTimestamp();
        if (lastSync > 0) {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("dd MMM yyyy, hh:mm a", java.util.Locale.getDefault());
            sb.append("\nLast sync: ").append(sdf.format(new java.util.Date(lastSync)));
        }

        long lastInbox = prefs.getLastInboxSyncTimestamp();
        if (lastInbox > 0) {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("dd MMM yyyy, hh:mm a", java.util.Locale.getDefault());
            sb.append("\nLast inbox scan: ").append(sdf.format(new java.util.Date(lastInbox)));
        }

        statusText.setText(sb.toString());
    }

    private void scanInbox(Button btn) {
        if (!prefs.isEnabled() || prefs.getToken().isEmpty()) {
            Toast.makeText(this, "Please save your token and enable sync first", Toast.LENGTH_LONG).show();
            return;
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS) != PackageManager.PERMISSION_GRANTED) {
            // Need READ_SMS permission
            requestSmsPermission();
            Toast.makeText(this, "Please grant SMS permission first, then tap Scan again", Toast.LENGTH_LONG).show();
            return;
        }

        btn.setEnabled(false);
        btn.setText("⏳ Scanning...");

        new Thread(() -> {
            SmsInboxReader.readAndSync(SmsSyncSetupActivity.this);
            runOnUiThread(() -> {
                btn.setEnabled(true);
                btn.setText("📥 Scan SMS Inbox (Last 7 Days)");
                updateStatus();
                Toast.makeText(SmsSyncSetupActivity.this, "✅ Inbox scan complete! Check your expenses & income.", Toast.LENGTH_LONG).show();
            });
        }).start();
    }
}
