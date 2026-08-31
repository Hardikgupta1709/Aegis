import os
import sys

# Ensure agent package is found
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from agent.rule_parser import parse_merchant_chat

TEST_CASES = [
    {
        "input": "Hey, if anyone orders more than 15000 rupees of stuff on COD, block it.",
        "expected_action": "block_cod",
    },
    {
        "input": "What's the weather today?",
        "expected_action": "unknown",
    }
]

def run_regression_tests():
    print("Running Aegis Integration Tests...\n")
    
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY is not set. The rule parser will use mock logic.")
        print("To run the real tests, export GEMINI_API_KEY.\n")
        return
        
    # LAYER 1 AUTOMATED TESTS
    # 1. Test Session Isolation
    print("Test 1: Session Isolation")
    parse_merchant_chat("I want to set a rule for Mumbai", merchant_id="phone_A")
    rule_A2 = parse_merchant_chat("Actually change that to Delhi", merchant_id="phone_A")
    rule_B = parse_merchant_chat("What rule did I just set?", merchant_id="phone_B")
    
    if "delhi" in rule_A2.confirmation_message.lower():
        print("✅ PASS: Session A remembered context.")
    else:
        print("❌ FAIL: Session A forgot context.")
        
    if "delhi" not in rule_B.confirmation_message.lower():
        print("✅ PASS: Session B is isolated.")
    else:
        print("❌ FAIL: Session B leaked from Session A.")

    print("\nTest 2: Basic Rule Extraction")
    for test in TEST_CASES:
        rule = parse_merchant_chat(test['input'], merchant_id="tester")
        if rule.action == test['expected_action']:
            print(f"✅ PASS: '{test['input']}' -> {rule.action}")
        else:
            print(f"❌ FAIL: Expected {test['expected_action']}, got {rule.action}")

if __name__ == "__main__":
    run_regression_tests()
