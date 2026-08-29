import json
import os
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Define the strict JSON schema we want the LLM to output (Using Pydantic)
class MerchantRule(BaseModel):
    action: str = Field(description="The action to take. Must be either 'block_cod', 'require_prepay', or 'allow_fast_track', or 'unknown' if unclear.")
    condition_feature: str = Field(description="The feature to evaluate. Examples: 'order_amount', 'sector', 'past_rto_rate', 'none' if unknown.")
    operator: str = Field(description="The logical operator: '>', '<', '==', '!=', 'contains', or 'none' if unknown.")
    threshold_value: str = Field(description="The value to compare against. Use 'none' if unknown. E.g. '8000', '0.40'")
    confirmation_message: str = Field(description="A plain English message to send back to the merchant to confirm we understood.")

def parse_merchant_chat(user_message: str) -> MerchantRule:
    print(f"Merchant WhatsApp Message: '{user_message}'\n")
    print("Aegis Agent is thinking (Live Gemini Call)...\n")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found. Falling back to mock for demo.")
        # Fallback to mock logic if API key isn't provided so demo doesn't crash completely
        lower_msg = user_message.lower()
        if "8000" in lower_msg and "cod" in lower_msg:
            return MerchantRule(
                action="block_cod",
                condition_feature="order_amount",
                operator=">",
                threshold_value="8000",
                confirmation_message="Understood. I will automatically disable COD for any order above ₹8,000. Reply YES to confirm."
            )
        elif "40%" in lower_msg or "rto" in lower_msg:
            return MerchantRule(
                action="require_prepay",
                condition_feature="past_rto_rate",
                operator=">",
                threshold_value="0.40",
                confirmation_message="Got it. If a customer has a past RTO rate higher than 40%, I will challenge them and downgrade to Prepaid. Reply YES to confirm."
            )
        else:
            return MerchantRule(
                action="unknown", condition_feature="none", operator="none", threshold_value="none",
                confirmation_message="I'm sorry, I didn't quite catch that rule. Could you rephrase it?"
            )
            
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are Aegis, an AI Risk Operator for an e-commerce merchant.
        The merchant wants to set a new automated rule.
        Analyze their request and extract the rule into the structured JSON schema.
        Also, write a plain English confirmation message ending with 'Reply YES to confirm.'
        
        Merchant's Request: "{user_message}"
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MerchantRule,
            ),
        )
        
        rule_dict = json.loads(response.text)
        rule = MerchantRule(**rule_dict)
        
        print("--- STRUCTURED JSON RULE EXTRACTED ---")
        print(json.dumps(rule.model_dump(), indent=2))
        print("\n--- WHAT WE REPLY TO THE MERCHANT ---")
        print(f"WhatsApp Reply: {rule.confirmation_message}")
        
        return rule
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return MerchantRule(
            action="unknown", condition_feature="none", operator="none", threshold_value="none",
            confirmation_message="I'm sorry, there was a system error processing your rule. Please try again."
        )

if __name__ == "__main__":
    # Test Scenario 1: Order Cap
    parse_merchant_chat("Hey Aegis, please disable COD if the order amount is more than 8000 rupees.")
    
    print("\n" + "="*50 + "\n")
    
    # Test Scenario 2: Repeat Offenders
    parse_merchant_chat("If a customer has an RTO rate higher than 40%, downgrade them to prepaid only.")