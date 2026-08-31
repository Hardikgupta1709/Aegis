import pandas as pd
import os

def generate_daily_digest():
    """
    Simulates the end-of-day digest sent to the merchant via WhatsApp.
    Instead of making them open a dashboard, we push the ROI directly to their phone,
    along with one high-value ambiguous case that needs human judgment.
    """
    print("\n--- INITIATING END OF DAY BATCH ---")
    
    # In a real system, this would query the DB for today's orders. 
    # For the demo, we'll pull metrics from our test set artifacts if they exist,
    # or just use realistic mock numbers aligned with the profit curve.
    
    try:
        test_df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../model/artifacts/test_set.csv'))
        total_orders = len(test_df)
        # Mock realistic daily slice
        total_orders = 450
        rto_prevented = 42
        fraud_blocked = 8
        
    except FileNotFoundError:
        total_orders = 450
        rto_prevented = 42
        fraud_blocked = 8

    # Financial Assumptions (From our profit curve)
    avg_order_value = 2000
    rto_cost = 150
    margin = 400
    
    rupees_saved = (rto_prevented * rto_cost) + (fraud_blocked * avg_order_value)
    
    # Formatting the WhatsApp Digest Message
    digest_message = f"""
*Aegis Daily Summary* 🛡️
_Your Risk Operations for Today_

*Orders Processed:* {total_orders}
*RTOs Prevented (Downgraded to PrePay):* {rto_prevented}
*Fraud Blocked:* {fraud_blocked}
*Estimated Capital Saved:* ₹{rupees_saved:,.2f}

---
*⚠️ 1 Action Required*
An order for ₹18,500 (Electronics) was placed via COD by a new account. The address has a high fuzziness score, but the IP matches the delivery Pincode perfectly.

The model score is 0.69 (just below our 0.71 threshold).

*Do you want to Allow COD or Require PrePay?*
Reply with 'ALLOW' or 'PREPAY'.
"""
    
    print("--- SENDING WHATSAPP TEMPLATE (VIA TWILIO) ---")
    print(digest_message)
    print("--- MESSAGE SENT SUCCESSFULLY ---")

if __name__ == "__main__":
    generate_daily_digest()
