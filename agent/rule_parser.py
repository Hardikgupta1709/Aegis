import json
import os
import time
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class MerchantRule(BaseModel):
    action: str = Field(description="The action to take. Must be either 'block_cod', 'require_prepay', or 'allow_fast_track', or 'unknown' if unclear.")
    condition_feature: str = Field(description="The feature to evaluate. Examples: 'order_amount', 'sector', 'past_rto_rate', 'none' if unknown.")
    operator: str = Field(description="The logical operator: '>', '<', '==', '!=', 'contains', or 'none' if unknown.")
    threshold_value: str = Field(description="The value to compare against. Use 'none' if unknown. E.g. '8000', '0.40'")
    confirmation_message: str = Field(description="A plain English message to send back to the merchant to confirm we understood.")

# 1. PERSISTENT MEMORY
_sessions: dict[str, "genai.chats.Chat"] = {}
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client

def get_session(merchant_id: str, client: genai.Client, model_name: str, config: types.GenerateContentConfig):
    if merchant_id not in _sessions:
        _sessions[merchant_id] = client.chats.create(model=model_name, config=config)
    return _sessions[merchant_id]

def parse_merchant_chat(user_message: str, merchant_id: str = "default") -> MerchantRule:
    print(f"Merchant [{merchant_id}] WhatsApp Message: '{user_message}'\n")
    print("Aegis Agent is thinking (Live Gemini Call)...\n")
    
    client = get_client()
    if not client:
        print("WARNING: GEMINI_API_KEY not found. Falling back to mock for demo.")
        lower_msg = user_message.lower()
        if "8000" in lower_msg and "cod" in lower_msg:
            return MerchantRule(action="block_cod", condition_feature="order_amount", operator=">", threshold_value="8000", confirmation_message="Understood. Reply YES to confirm.")
        else:
            return MerchantRule(action="unknown", condition_feature="none", operator="none", threshold_value="none", confirmation_message="I'm sorry, I didn't quite catch that.")
            
    try:
        
        # 3. FIRST-CONTACT IDENTITY
        config = types.GenerateContentConfig(
            system_instruction=(
                "You are Aegis, a risk assistant for Indian D2C merchants. "
                "You help reduce COD fraud and RTO. Speak briefly and warmly, "
                "in English or Hindi depending on what the merchant uses. "
                "Never discuss anything outside risk, orders, or rules. "
                "If they want to set a rule, extract it to JSON and say 'Reply YES to lock it in.' "
                "If they ask 'why' about an order, set action to 'unknown' and answer naturally."
            ),
            response_mime_type="application/json",
            response_schema=MerchantRule,
        )
        
        chat = get_session(merchant_id, client, 'gemini-flash-latest', config)
        
        # Robust Retry Loop for 503 Overload Errors
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = chat.send_message(user_message)
                break
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"Network 503 spike. Retrying attempt {attempt+2} in {2**attempt}s...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"\n❌ [CRITICAL ERROR] Gemini API exhausted after {attempt+1} attempts: {e}")
                    print("⚠️  TRIGGERING GRACEFUL FALLBACK REPLY TO MERCHANT ⚠️\n")
                    return MerchantRule(
                        action="unknown", condition_feature="none", operator="none", threshold_value="none",
                        confirmation_message="I'm sorry, I'm currently overloaded. Please try again in a moment."
                    )
        
        rule_dict = json.loads(response.text)
        rule = MerchantRule(**rule_dict)
        return rule
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return MerchantRule(
            action="unknown", condition_feature="none", operator="none", threshold_value="none",
            confirmation_message="I'm sorry, there was a system error processing your rule."
        )