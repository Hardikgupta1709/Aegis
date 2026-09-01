import requests
import time
import json
import random

API_URL = "http://localhost:8000/razorpay_webhook"

def print_header(title):
    print("\n" + "="*50)
    print(f"   {title}")
    print("="*50)

def simulate_checkout(order_amount=4500, past_rto_rate=0.10, is_bot=False):
    print_header("AEGIS JUDGE CONSOLE: SIMULATING RAZORPAY CHECKOUT")
    
    # Razorpay standard webhook format
    payload = {
      "entity": "event",
      "event": "order.created",
      "payload": {
        "order": {
          "entity": {
            "id": f"order_{random.randint(100000, 999999)}",
            "amount": int(order_amount * 100), # Razorpay uses paise
            "currency": "INR",
            "status": "created",
            "notes": {
              "aegis_enriched_rto_history": "1.0" if is_bot else str(past_rto_rate),
              "device_velocity_1h": "20" if is_bot else ("5" if past_rto_rate > 0.3 else "1"),
              "address_fuzziness": "1.0" if is_bot else ("0.85" if past_rto_rate > 0.3 else "0.1")
            }
          }
        }
      }
    }
    
    print(f"Injecting payload: {json.dumps(payload, indent=2)}")
    print("\nCalling Aegis Decision Engine...\n")
    
    try:
        start = time.time()
        response = requests.post(API_URL, json=payload)
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            if result['decision'] == 'require_prepay':
                print(f"🚨 DECISION: {result['decision'].upper()}")
            else:
                print(f"✅ DECISION: {result['decision'].upper()}")
            print(f"📝 REASON:   {result['reason']}")
            print(f"⚡ LATENCY:  {latency:.2f}ms")
        else:
            print(f"❌ ERROR: Server returned {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to API. Is 'python serving/api.py' running?")

if __name__ == "__main__":
    print("Welcome to the Aegis Judge Console.")
    print("This tool bypasses the UI to simulate direct backend checkout requests.")
    print("1. Safe Order (4500 amount, 10% RTO history)")
    print("2. High Value / Rule Override (18000 amount, 60% RTO history)")
    print("3. Blatant Bot Attack (25000 amount, Extreme Velocity & Fuzziness)")
    
    choice = input("\nSelect scenario (1, 2, or 3): ")
    if choice == '1':
        simulate_checkout(4500, 0.10, is_bot=False)
    elif choice == '2':
        simulate_checkout(18000, 0.60, is_bot=False)
    elif choice == '3':
        simulate_checkout(25000, 1.0, is_bot=True)
    else:
        print("Invalid choice.")
