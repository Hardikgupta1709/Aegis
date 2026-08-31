import requests
import time

API_URL = "http://localhost:8000"

def test_razorpay():
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
              "aegis_enriched_rto_history": "0.60",
              "device_velocity_1h": "6",
              "address_fuzziness": "0.9"
            }
          }
        }
      }
    }
    response = requests.post(f"{API_URL}/razorpay_webhook", json=payload)
    print("Razorpay Response:", response.json())

def test_idempotency():
    print("\nTesting Idempotency...")
    data = {"Body": "Test", "From": "phone_test", "MessageSid": "SM999", "NumMedia": 0}
    
    # First request
    resp1 = requests.post(f"{API_URL}/whatsapp", data=data)
    print("First call status:", resp1.status_code, "Body:", resp1.text[:50])
    
    # Second request
    resp2 = requests.post(f"{API_URL}/whatsapp", data=data)
    print("Second call status:", resp2.status_code, "Body:", resp2.text)

if __name__ == "__main__":
    time.sleep(1) # wait for server to bind
    test_razorpay()
    test_idempotency()
