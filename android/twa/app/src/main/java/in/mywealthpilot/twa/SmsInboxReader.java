package in.mywealthpilot.twa;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.regex.Pattern;

/**
 * Reads bank/UPI transaction SMS from the phone's local inbox.
 * Only picks up messages from the last N days to avoid re-processing old ones.
 */
public class SmsInboxReader {
    private static final String TAG = "SmsInboxReader";

    /** Default: read SMS from last 7 days */
    private static final int DEFAULT_DAYS_BACK = 7;

    /** Max SMS to process in one batch */
    private static final int MAX_SMS_BATCH = 50;

    // Re-use same bank patterns from SmsBroadcastReceiver
    private static final Pattern BANK_SMS_PATTERN = Pattern.compile(
            "(?i)(debited|credited|debit|credit|withdrawn|received|" +
            "spent|paid|transferred|purchase|refund|cashback|salary|" +
            "Rs\\.?\\s*[\\d,]+|INR\\s*[\\d,]+|₹\\s*[\\d,]+)",
            Pattern.CASE_INSENSITIVE
    );

    private static final Pattern BANK_SENDER_PATTERN = Pattern.compile(
            "(?i)(SBI|HDFC|ICICI|AXIS|KOTAK|PNB|BOB|CANARA|UNION|" +
            "INDUS|IDBI|FEDER|IOB|BOI|UCO|YES|PAYTM|GPAY|PHONEPE|" +
            "BHIM|UPI|NEFT|IMPS|RTGS|BANK|CITI|HSBC|SC\\s*BANK|" +
            "AMEX|RBL|IDFC|BANDHAN|BAJAJ|FINO|AU\\s*BANK|" +
            "JM\\-|AD\\-|AX\\-|BZ\\-|CB\\-|DM\\-|HP\\-|" +
            "VM\\-|VK\\-|BW\\-|TD\\-|TM\\-)"
    );

    /**
     * Read recent bank SMS from inbox and sync to server.
     * Only processes SMS received after the last sync timestamp.
     *
     * @param context Android context (needs READ_SMS permission)
     */
    public static void readAndSync(Context context) {
        readAndSync(context, DEFAULT_DAYS_BACK);
    }

    /**
     * Read bank SMS from inbox for the given number of days back and sync to server.
     */
    public static void readAndSync(Context context, int daysBack) {
        SmsPreferences prefs = new SmsPreferences(context);
        if (!prefs.isEnabled() || prefs.getToken().isEmpty()) {
            Log.d(TAG, "SMS sync not enabled or no token, skipping inbox read");
            return;
        }

        long lastSync = prefs.getLastInboxSyncTimestamp();
        // If never synced, go back N days; otherwise only since last sync
        long sinceTimestamp;
        if (lastSync > 0) {
            sinceTimestamp = lastSync;
        } else {
            sinceTimestamp = System.currentTimeMillis() - ((long) daysBack * 24 * 60 * 60 * 1000);
        }

        JSONArray bankMessages = readBankSms(context, sinceTimestamp);
        if (bankMessages.length() == 0) {
            Log.d(TAG, "No new bank SMS found in inbox");
            return;
        }

        Log.i(TAG, "Found " + bankMessages.length() + " bank SMS to sync");

        // Send to server via SmsSyncService
        SmsSyncService.syncBatch(context, bankMessages);

        // Update last inbox sync timestamp
        prefs.setLastInboxSyncTimestamp(System.currentTimeMillis());
    }

    /**
     * Read SMS from the inbox content provider, filtering for bank messages.
     */
    private static JSONArray readBankSms(Context context, long sinceTimestamp) {
        JSONArray messages = new JSONArray();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US);

        Uri smsUri = Uri.parse("content://sms/inbox");
        String selection = "date > ?";
        String[] selectionArgs = new String[]{String.valueOf(sinceTimestamp)};
        String sortOrder = "date DESC";

        Cursor cursor = null;
        try {
            cursor = context.getContentResolver().query(
                    smsUri,
                    new String[]{"address", "body", "date"},
                    selection,
                    selectionArgs,
                    sortOrder
            );

            if (cursor == null) {
                Log.w(TAG, "SMS cursor is null — READ_SMS permission might be missing");
                return messages;
            }

            int count = 0;
            while (cursor.moveToNext() && count < MAX_SMS_BATCH) {
                String sender = cursor.getString(cursor.getColumnIndexOrThrow("address"));
                String body = cursor.getString(cursor.getColumnIndexOrThrow("body"));
                long dateMs = cursor.getLong(cursor.getColumnIndexOrThrow("date"));

                if (body == null || body.isEmpty()) continue;

                // Filter: only bank/transaction SMS
                if (isBankSms(sender, body)) {
                    try {
                        JSONObject msg = new JSONObject();
                        msg.put("body", body);
                        msg.put("date", sdf.format(new Date(dateMs)));
                        messages.put(msg);
                        count++;
                    } catch (Exception e) {
                        Log.w(TAG, "Error building SMS JSON", e);
                    }
                }
            }
        } catch (SecurityException e) {
            Log.e(TAG, "READ_SMS permission not granted", e);
        } catch (Exception e) {
            Log.e(TAG, "Error reading SMS inbox", e);
        } finally {
            if (cursor != null) cursor.close();
        }

        return messages;
    }

    /**
     * Check if an SMS is a bank transaction message.
     */
    private static boolean isBankSms(String sender, String body) {
        if (sender != null && BANK_SENDER_PATTERN.matcher(sender).find()) {
            return BANK_SMS_PATTERN.matcher(body).find();
        }
        return BANK_SMS_PATTERN.matcher(body).find() &&
                body.matches("(?i).*(?:a/c|acct|account|card|upi|neft|imps).*");
    }
}
