package in.mywealthpilot.twa;

import android.content.Context;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.OutputStream;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Handles real-time SMS sync with the MyWealthPilot server.
 * Only processes NEW incoming SMS — never reads SMS history.
 * When a bank SMS arrives, SmsBroadcastReceiver calls syncSingleSms()
 * which immediately sends it to the server for parsing.
 */
public class SmsSyncService {
    private static final String TAG = "SmsSyncService";
    private static final String API_URL = "https://mywealthpilot.in/api/sms/sync";

    private static Handler backgroundHandler;

    static {
        HandlerThread thread = new HandlerThread("SmsSyncThread");
        thread.start();
        backgroundHandler = new Handler(thread.getLooper());
    }

    /**
     * Sync a single incoming SMS (called from BroadcastReceiver).
     */
    public static void syncSingleSms(Context context, String smsBody) {
        backgroundHandler.post(() -> {
            try {
                SmsPreferences prefs = new SmsPreferences(context);
                String token = prefs.getToken();
                if (token.isEmpty() || !prefs.isEnabled()) return;

                JSONArray messages = new JSONArray();
                JSONObject msg = new JSONObject();
                msg.put("body", smsBody);
                msg.put("date", new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(new Date()));
                messages.put(msg);

                sendToServer(token, messages);
                prefs.setLastSyncTimestamp(System.currentTimeMillis());
            } catch (Exception e) {
                Log.e(TAG, "Error syncing single SMS", e);
            }
        });
    }

    /**
     * Send SMS messages to the server API.
     */
    private static void sendToServer(String token, JSONArray messages) {
        HttpURLConnection conn = null;
        try {
            JSONObject payload = new JSONObject();
            payload.put("token", token);
            payload.put("messages", messages);

            URL url = new URL(API_URL);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conn.setRequestProperty("Accept", "application/json");
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(15000);
            conn.setDoOutput(true);

            byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
            conn.setFixedLengthStreamingMode(body.length);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(body);
            }

            int responseCode = conn.getResponseCode();
            InputStream is = (responseCode >= 200 && responseCode < 300)
                    ? conn.getInputStream() : conn.getErrorStream();

            BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();

            if (responseCode >= 200 && responseCode < 300) {
                JSONObject result = new JSONObject(response.toString());
                int expenses = result.optInt("added_expenses", 0);
                int income = result.optInt("added_income", 0);
                Log.i(TAG, "SMS sync success: " + expenses + " expenses, " + income + " income added");
            } else {
                Log.w(TAG, "SMS sync failed (" + responseCode + "): " + response);
            }

        } catch (Exception e) {
            Log.e(TAG, "Error sending SMS to server", e);
        } finally {
            if (conn != null) conn.disconnect();
        }
    }
}
