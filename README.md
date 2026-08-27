# Aegis: The Autonomous Zero-UI Risk Operator

**Track:** AI Risk Manager (Razorpay Buildathon)

## The Wedge: Aegis vs. Thirdwatch
Thirdwatch (and similar risk engines) are world-class at device fingerprinting and detecting what is risky. However, they stop at detection. For borderline cases (impulse buys, edge-case RTOs), merchants still have to manually log into dashboards to make decisions. 

**Aegis is the decision-and-communication layer.** We do not replace Thirdwatch. We turn its risk signals into executed policies, communicated in plain language over WhatsApp, without the merchant ever opening a dashboard.

## The Two-Bucket Loss Problem
We do not conflate "RTO" with "Fraud". 60% of Indian ecommerce is COD. While ~26% of COD orders return to origin, only 8-10% of that is malicious fraud. The rest is logistics failure and impulse buying. Aegis tackles both, but treats them differently.

## Repository Structure
* `data/`: The synthetic data generator (two-bucket labeling) and raw datasets.
* `model/`: XGBoost training, Platt scaling calibration, and the Profit-Curve threshold sweep.
* `serving/`: The simulated checkout latency benchmark layer.
* `agent/`: Structured rule extraction (LLM Function Calling) and Twilio WhatsApp integration.
* `docs/`: Architecture diagrams and presentation assets.

## What is Real vs. Mocked
* **Real:** The XGBoost model, probability calibration, threshold profit math, LLM structured rule parsing, and live WhatsApp messaging via Twilio Sandbox.
* **Mocked:** The live Razorpay checkout ping (simulated locally) and cross-merchant data syndication (mocked for DPDP compliance demonstration).
