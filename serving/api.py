import time
import asyncio
import pandas as pd
import joblib
import os
import sys
import json
from datetime import datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response, HTMLResponse
from pydantic import BaseModel
import uvicorn
from twilio.twiml.messaging_response import MessagingResponse

# Ensure we can import our agent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from agent.rule_parser import parse_merchant_chat

app = FastAPI(title="Aegis Risk Gateway")

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../model/artifacts/xgboost_model.pkl')
try:
    model = joblib.load(MODEL_PATH)
except:
    model = None
    print("Warning: Model not found. Start training first.")

# --- THRESHOLDS ---
OPTIMAL_THRESHOLD = 0.71 
# Cold-start thresholds based on Sector (MCC)
COLD_START_THRESHOLDS = {
    0: 0.60, # Fashion (Default 0 in our categorical mapping)
    1: 0.65, # Electronics
    2: 0.55  # FMCG
}
MERCHANT_HISTORY_COUNT = 1500 # Assume we have enough history to use the ML optimized threshold. 

# --- STATE ---
MERCHANT_RULES = [] # Confirmed rules
PENDING_RULE = None # Rule waiting for "YES" confirmation
AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), 'audit_log.txt')

# --- FRONTEND ENDPOINTS REMOVED ---
# To maintain the "Zero Dashboard" core pitch, Aegis runs purely via API and WhatsApp.

# --- CORE LOGIC ---
class CheckoutPayload(BaseModel):
    order_id: str
    sector: int 
    order_amount: float
    payment_method: int  
    device_velocity_1h: int
    is_new_account: int
    ip_pincode_match: int
    address_fuzziness: float
    time_to_checkout_sec: float
    past_rto_rate: float
    customer_name_length: int
    day_of_week: int

def append_to_audit_log(event: str):
    """Simple audit trail for rule changes."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {event}\n"
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(log_entry)

@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...)):
    global PENDING_RULE
    print(f"\n[WHATSAPP RCV] Message from Merchant: {Body}")
    
    twiml_response = MessagingResponse()
    
    body_lower = Body.strip().lower()
    
    if body_lower in ["yes", "y"] and PENDING_RULE is not None:
        MERCHANT_RULES.append(PENDING_RULE)
        rule_desc = f"{PENDING_RULE['condition_feature']} {PENDING_RULE['operator']} {PENDING_RULE['threshold_value']} -> {PENDING_RULE['action']}"
        append_to_audit_log(f"Merchant CONFIRMED rule: {rule_desc}")
        
        PENDING_RULE = None
        twiml_response.message("Rule confirmed and is now active on the gateway.")
        return Response(content=str(twiml_response), media_type="application/xml")
        
    rule = parse_merchant_chat(Body)
    
    if rule.action != "unknown":
        try:
            val = float(rule.threshold_value.replace(',', '').replace('₹', ''))
        except:
            val = rule.threshold_value
            
        PENDING_RULE = {
            "action": rule.action,
            "condition_feature": rule.condition_feature,
            "operator": rule.operator,
            "threshold_value": val
        }
        
        twiml_response.message(rule.confirmation_message)
    else:
        twiml_response.message(rule.confirmation_message)

    return Response(content=str(twiml_response), media_type="application/xml")

@app.post("/evaluate_risk")
async def evaluate_risk(payload: CheckoutPayload):
    start_time = time.time()
    
    # 1. COLD START FALLBACK LOGIC
    # If the merchant has less than 1000 historical orders, we cannot trust a fine-tuned 
    # probability threshold yet. We fall back to the sector's baseline threshold.
    is_cold_start = MERCHANT_HISTORY_COUNT < 1000
    effective_threshold = COLD_START_THRESHOLDS.get(payload.sector, 0.60) if is_cold_start else OPTIMAL_THRESHOLD
    
    # 2. EVALUATE HARD RULES
    for rule in MERCHANT_RULES:
        if rule["condition_feature"] == "order_amount" and rule["operator"] == ">":
            if payload.order_amount > float(rule["threshold_value"]):
                return {
                    "order_id": payload.order_id,
                    "decision": rule["action"], 
                    "reason": f"WhatsApp Rule Applied: order_amount > {rule['threshold_value']}",
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }
        if rule["condition_feature"] == "past_rto_rate" and rule["operator"] == ">":
            if payload.past_rto_rate > float(rule["threshold_value"]):
                return {
                    "order_id": payload.order_id,
                    "decision": rule["action"], 
                    "reason": f"WhatsApp Rule Applied: past_rto_rate > {rule['threshold_value']}",
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }

    # 3. RUN ML MODEL
    if model is None:
        return {"error": "Model not loaded"}

    df = pd.DataFrame([payload.model_dump(exclude={'order_id'})])
    expected_cols = ['sector', 'order_amount', 'payment_method', 'device_velocity_1h', 'is_new_account', 'ip_pincode_match', 'address_fuzziness', 'time_to_checkout_sec', 'past_rto_rate', 'customer_name_length', 'day_of_week']
    rto_prob = model.predict_proba(df[expected_cols])[0][2]
    
    # 4. PLAIN-ENGLISH REASON CODES & THRESHOLDING
    if rto_prob >= effective_threshold:
        decision = "require_prepay" 
        
        # Build plain-English reason based on top contributing factors
        factors = []
        if payload.address_fuzziness > 0.7: factors.append("highly ambiguous address")
        if payload.past_rto_rate > 0.3: factors.append("poor historical delivery record")
        if payload.device_velocity_1h > 3: factors.append("suspicious order velocity")
        
        reason_str = ", ".join(factors) if factors else f"Pattern match (Score: {rto_prob:.2f})"
        
        reason = f"High RTO Risk due to {reason_str}. Downgraded to PrePay COD."
    else:
        decision = "allow_fast_track"
        reason = f"Low Risk (Score: {rto_prob:.2f}). Approved for COD."
        
    return {
        "order_id": payload.order_id,
        "decision": decision,
        "reason": reason,
        "latency_ms": round((time.time() - start_time) * 1000, 2)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)