import json
import matplotlib.pyplot as plt
import pandas as pd

file_path = 'performance_results.json'

with open(file_path, 'r') as file:
    data = json.load(file)

parsed_data = []
for entry in data:
    row = {
        'Total Data (X)': entry['total_data'],
        'Total Duration': entry['metrics']['total_duration_sec'],
        'Registration': entry['metrics']['registration_duration_sec'],
        'Diploma Issuance': entry['metrics']['diploma_issuance_duration_sec'],
        'Blockchain Validation': entry['metrics']['blockchain_validation_duration_sec']
    }
    parsed_data.append(row)

df = pd.DataFrame(parsed_data)

plt.figure(figsize=(10, 6))

plt.plot(df['Total Data (X)'], df['Total Duration'], marker='o', linewidth=2, label='Total E2E Flow')
plt.plot(df['Total Data (X)'], df['Registration'], marker='s', linestyle='--', label='Academic Registration')
plt.plot(df['Total Data (X)'], df['Diploma Issuance'], marker='^', linestyle='--', label='Diploma Issuance (Tx)')
plt.plot(df['Total Data (X)'], df['Blockchain Validation'], marker='d', linestyle='--', label='Blockchain Validation')

plt.title('SiakadChain System Performance Analysis', fontsize=14, fontweight='bold', pad=15)
plt.xlabel('Total Records (X)', fontsize=12)
plt.ylabel('Duration / Seconds (Y)', fontsize=12)
plt.xticks(df['Total Data (X)'])
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(fontsize=10)

plt.tight_layout()
plt.savefig('siakadchain_performance_chart.png', dpi=300)
plt.show()