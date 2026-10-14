# WP · 90 Error handler

**Job:** make every failure visible within a minute, in three places.

Error Trigger → Format alert → (Gmail to hello@ · Telegram to Noah · Runs row with Status Failed). Each channel has `onError: continue`, so one broken channel doesn't hide the error in the others.

Set as *Error workflow* in the settings of 00, 10, 20, 30.
