import pandas as pd
import numpy as np
import os

np.random.seed(42)

NUM_ROWS = 25000

def generate_synthetic_data(num_rows):
    print(f"Generating {num_rows} synthetic orders...")
    
    sectors = np.random.choice(['Fashion', 'Electronics', 'FMCG'], size=num_rows, p=[0.5, 0.3, 0.2])
    order_amounts = []
    
    for sector in sectors:
        if sector == 'Fashion':
            order_amounts.append(np.round(np.random.lognormal(mean=7.0, sigma=0.8), 2)) 
        elif sector == 'Electronics':
            order_amounts.append(np.round(np.random.lognormal(mean=9.0, sigma=1.0), 2)) 
        else: 
            order_amounts.append(np.round(np.random.lognormal(mean=6.5, sigma=0.5), 2)) 

    df = pd.DataFrame({
        'order_id': [f"ORD_{i:06d}" for i in range(num_rows)],
        'sector': sectors,
        'order_amount': order_amounts,
        'payment_method': np.random.choice(['COD', 'Prepaid'], size=num_rows, p=[0.65, 0.35]), 
        
        'device_velocity_1h': np.random.poisson(lam=1.5, size=num_rows),
        'is_new_account': np.random.choice([0, 1], size=num_rows, p=[0.7, 0.3]),
        'ip_pincode_match': np.random.choice([0, 1], size=num_rows, p=[0.1, 0.9]), 
        
        'address_fuzziness': np.random.uniform(0, 1, size=num_rows), 
        'time_to_checkout_sec': np.random.exponential(scale=120, size=num_rows), 
        'past_rto_rate': np.random.uniform(0, 0.5, size=num_rows),
        
        'customer_name_length': np.random.randint(4, 25, size=num_rows),
        'day_of_week': np.random.randint(0, 7, size=num_rows)
    })

    labels = []
    
    for i, row in df.iterrows():
        if row['payment_method'] == 'Prepaid':
            labels.append(0) 
            continue
            

        is_fraud = False
        if row['device_velocity_1h'] > 4 and row['ip_pincode_match'] == 0:
            is_fraud = True
        elif row['sector'] == 'Electronics' and row['order_amount'] > 15000 and row['is_new_account']:
            is_fraud = np.random.rand() > 0.2 
            
        if is_fraud:
            labels.append(1) 
            continue
            
        is_logistics_rto = False
        rto_prob = 0.0
        
        if row['address_fuzziness'] > 0.75:
            rto_prob += 0.4
        if row['time_to_checkout_sec'] < 20: 
            rto_prob += 0.3
        if row['past_rto_rate'] > 0.3:
            rto_prob += 0.3
            
        if row['sector'] == 'Fashion':
            rto_prob += 0.15
            
        if np.random.rand() < rto_prob:
            labels.append(2) 
            continue
            
        labels.append(0)

    df['outcome_label'] = labels
    
    noise_indices = np.random.choice(df.index, size=int(num_rows * 0.05), replace=False)
    df.loc[noise_indices, 'outcome_label'] = np.random.choice([0, 1, 2], size=len(noise_indices))

    print("\nDataset Generated. Outcome Distribution:")
    total_cod = len(df[df['payment_method'] == 'COD'])
    cod_fraud = len(df[(df['payment_method'] == 'COD') & (df['outcome_label'] == 1)])
    cod_rto = len(df[(df['payment_method'] == 'COD') & (df['outcome_label'] == 2)])
    
    print(f"Total COD Orders: {total_cod}")
    print(f"Malicious Fraud (COD): {cod_fraud} ({cod_fraud/total_cod*100:.1f}%) - Target ~8-10%")
    print(f"Logistics/Impulse RTO (COD): {cod_rto} ({cod_rto/total_cod*100:.1f}%) - Target ~15-20%")
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/synthetic_orders.csv', index=False)
    print("\nSaved to data/synthetic_orders.csv")

if __name__ == "__main__":
    generate_synthetic_data(NUM_ROWS)
