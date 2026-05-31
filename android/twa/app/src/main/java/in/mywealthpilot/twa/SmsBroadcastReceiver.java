package in.mywealthpilot.twa;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

import java.util.regex.Pattern;

/**
 * Listens for incoming SMS messages in real-time.
 * Filters for bank transaction SMS and sends them to the server.
 */
public class SmsBroadcastReceiver extends BroadcastReceiver {
    private static final String TAG = "SmsBroadcastReceiver";

    // Patterns to identify bank/UPI transaction SMS
    private static final Pattern BANK_SMS_PATTERN = Pattern.compile(
            "(?i)(debited|credited|debit|credit|withdrawn|received|" +
            "spent|paid|transferred|purchase|refund|cashback|salary|" +
            "Rs\\.?\\s*[\\d,]+|INR\\s*[\\d,]+|₹\\s*[\\d,]+)",
            Pattern.CASE_INSENSITIVE
    );

    // Common bank sender IDs (Indian banks use short codes)
    private static final Pattern BANK_SENDER_PATTERN = Pattern.compile(
            "(?i)(SBI|HDFC|ICICI|AXIS|KOTAK|PNB|BOB|CANARA|UNION|" +
            "INDUS|IDBI|FEDER|IOB|BOI|UCO|YES|PAYTM|GPAY|PHONEPE|" +
            "BHIM|UPI|NEFT|IMPS|RTGS|BANK|CITI|HSBC|SC\\s*BANK|" +
            "AMEX|RBL|IDFC|BANDHAN|BAJAJ|FINO|AU\\s*BANK|" +
            "JM\\-|AD\\-|AX\\-|BZ\\-|CB\\-|DM\\-|HP\\-|" +
            "VM\\-|VK\\-|BW\\-|TD\\-|TM\\-)"
    );

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!"android.provider.Telephony.SMS_RECEIVED".equals(intent.getAction())) {
            return;
        }

        SmsPreferences prefs = new SmsPreferences(context);
        if (!prefs.isEnabled() || prefs.getToken().isEmpty()) {
            return;
        }

        Bundle bundle = intent.getExtras();
        if (bundle == null) return;

        Object[] pdus = (Object[]) bundle.get("pdus");
        if (pdus == null) return;

        String format = bundle.getString("format", "3gpp");

        for (Object pdu : pdus) {
            SmsMessage sms = SmsMessage.createFromPdu((byte[]) pdu, format);
            if (sms == null) continue;

            String sender = sms.getOriginatingAddress();
            String body = sms.getMessageBody();

            if (body == null || body.isEmpty()) continue;

            // Only process bank/transaction SMS
            if (isBankSms(sender, body)) {
                Log.d(TAG, "Bank SMS detected from: " + sender);
                // Start sync service to send this SMS to server
                SmsSyncService.syncSingleSms(context, body);
            }
        }
    }

    /**
     * Check if an SMS is a bank transaction message.
     */
    static boolean isBankSms(String sender, String body) {
        // Check sender ID
        if (sender != null && BANK_SENDER_PATTERN.matcher(sender).find()) {
            // Also verify body has financial content
            return BANK_SMS_PATTERN.matcher(body).find();
        }
        // If sender is unknown, check body more strictly
        return BANK_SMS_PATTERN.matcher(body).find() &&
                body.matches("(?i).*(?:a/c|acct|account|card|upi|neft|imps).*");
    }
}
