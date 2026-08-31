# Aegis: The Autonomous Zero-UI Risk Operator

**Track:** AI Risk Manager (Razorpay Buildathon)

## The Wedge: Aegis vs. Thirdwatch
Thirdwatch (and similar risk engines) are world-class at device fingerprinting and detecting what is risky. However, they stop at detection. For borderline cases (impulse buys, edge-case RTOs), merchants still have to manually log into dashboards to make decisions. 

**Aegis is the decision-and-communication layer.** We do not replace Thirdwatch. We turn its risk signals into executed policies, communicated in plain language over WhatsApp, without the merchant ever opening a dashboard.

## Roadmap (Not Yet Built)
- **Voice Notes**: Routing audio via Twilio Media through Whisper/Gemini to extract risk rules deterministically.

## The Two-Bucket Loss Problem
We do not conflate "RTO" with "Fraud". 60% of Indian ecommerce is COD. While ~26% of COD orders return to origin, only 8-10% of that is malicious fraud. The rest is logistics failure and impulse buying. Aegis tackles both, but treats them differently.

## Repository Structure
* `data/`: The synthetic data generator (two-bucket labeling) and raw datasets.
* `model/`: XGBoost training, Platt scaling calibration, and the Profit-Curve threshold sweep.
* `serving/`: The simulated checkout latency benchmark layer and Judge Simulator UI.
* `agent/`: Structured rule extraction (LLM Function Calling) and Twilio WhatsApp integration.
* `docs/`: Architecture diagrams and presentation assets.

## What is Real vs. Mocked
* **Real:** The XGBoost model, probability calibration, threshold profit math, LLM structured rule parsing, and live WhatsApp messaging.
* **Mocked:** The live Razorpay checkout ping (simulated locally via our Judge Simulator) and cross-merchant data syndication (mocked for DPDP compliance demonstration).

## Scope Tiers
| Tier | Features Included |
|---|---|
| **Must-have** | Synthetic dataset with 2-bucket loss, Calibrated risk model + profit-curve sweep, Real WhatsApp digest & Approve/Reject loop, Structured rule extraction via Gemini. |
| **Should-have** | Cold-start fallback logic for new merchants, plain-English reason codes, rule audit trails. |
| **Cherry-on-top** | Judge Simulator UI (Interactive demo), Agent rule extraction regression tests. |
| **Won't-build** | Real cross-merchant data sharing (due to DPDP consent), live production payment gateway integration, open-ended natural language rule reconciliation. |

## How to Run

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pandas numpy xgboost scikit-learn twilio google-genai
   ```
2. **Set up API Keys:**
   ```bash
   export GEMINI_API_KEY="your-gemini-key"
   ```
3. **Run the Gateway Simulator:**
   ```bash
   python serving/api.py
   ```
   Navigate to `http://localhost:8000` to access the Judge Simulator.
4. **Test the LLM Rule Parsing:**
   ```bash
   python agent/test_rules.py
   ```
5. **Simulate End-of-Day Digest:**
   ```bash
   python agent/digest_generator.py
   ```
