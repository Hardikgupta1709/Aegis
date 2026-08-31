import asyncio
import os
import sys
from fastapi.testclient import TestClient

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from serving.api import app, MERCHANT_RULES

client = TestClient(app)

def test_razorpay_scenario_2():
    print("Testing Razorpay Webhook (Scenario 2)...")
    payload = {
      "entity": "event",
      "event": "order.created",
      "payload": {
        "order": {
          "entity": {
            "id": "order_123456",
            "amount": 1800000,
            "currency": "INR",
            "status": "created",
            "notes": {
              "aegis_enriched_rto_history": "0.60"
            }
          }
        }
      }
    }
    response = client.post("/razorpay_webhook", json=payload)
    print("Status:", response.status_code)
    try:
        print("Response:", response.json())
    except:
        print("Raw:", response.text)

def test_idempotency():
    print("\nTesting Idempotency...")
    # Fire first
    data = {"Body": "Test message", "From": "phone_C", "MessageSid": "SM123"}
    resp1 = client.post("/whatsapp", data=data)
    print("Resp 1 Status:", resp1.status_code)
    print("Resp 1 Body:", resp1.text)
    
    # Fire second (duplicate)
    resp2 = client.post("/whatsapp", data=data)
    print("Resp 2 Status:", resp2.status_code)
    print("Resp 2 Body:", resp2.text)
    if resp2.text == "<Response></Response>":
        print("✅ SUCCESS: Idempotency blocked the duplicate.")
    else:
        print("❌ FAIL: Idempotency did not work.")

if __name__ == "__main__":
    test_razorpay_scenario_2()
    test_idempotency()
