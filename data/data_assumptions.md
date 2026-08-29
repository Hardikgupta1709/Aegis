# Synthetic Data Assumptions

Because real-world Indian D2C transaction data containing explicit "RTO vs Fraud" labels is not publicly available, we generated a synthetic dataset of 25,000 orders grounded in published industry statistics.

## The Two-Bucket Loss Problem

Indian e-commerce is overwhelmingly driven by Cash-on-Delivery (COD), accounting for 60-70% of total volume. However, COD orders have a famously high Return-to-Origin (RTO) rate, typically ranging from 20% to 30%. 

We split this loss into two distinct buckets during data generation:

### 1. Malicious Fraud (Target: 8-10% of COD)
* **What it is:** Bot networks, promo-abuse rings, fake accounts, or deliberate competitor attacks.
* **How we modeled it:** We linked this to high `device_velocity_1h` (> 4 transactions from the same device in an hour) combined with an `ip_pincode_match` failure (IP address location does not match the delivery Pincode). For high-value electronics, new accounts are also highly weighted.
* **Why it matters:** These must be blocked outright. 

### 2. Logistics & Impulse RTO (Target: 15-20% of COD)
* **What it is:** Genuine customers who change their minds, or orders that fail delivery because the address is poorly formatted.
* **How we modeled it:** We tied this to `address_fuzziness` (a mock score of how ambiguous the address text is), low `time_to_checkout_sec` (indicating a rapid impulse buy without reading details), and the customer's `past_rto_rate`. We also introduced a slight sector bias (Fashion has higher impulse RTO than Grocery).
* **Why it matters:** Blocking these outright is a bad idea. These are genuine customers. Instead, we want to challenge them (e.g., downgrade to prepaid or ask for a small convenience fee).

## Sector Variances
We distribute orders across Fashion (50%), Electronics (30%), and FMCG/Grocery (20%), using distinct log-normal distributions for the `order_amount` to mimic real-world Average Order Values (AOV).

## Adding Noise
To prove our model is doing genuine risk separation and not just perfectly memorizing deterministic rules, we inject a 5% random noise factor into the final `outcome_label`. A model that achieves 99.9% accuracy on synthetic data is a red flag; our noise ensures the model must learn statistical generalizations, resulting in a realistic, non-perfect AUC.
