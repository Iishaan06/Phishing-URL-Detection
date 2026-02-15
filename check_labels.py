import json

# Check the labels
with open('my_phishing_dataset.json', 'r') as f:
    data = json.load(f)

print("Sample URLs from dataset:")
for item in data[:5]:
    print(f"  {item['url'][:70]:70} -> {item['label']}")

# Count labels
phishing_count = sum(1 for x in data if x['label'] == 'phishing')
legit_count = sum(1 for x in data if x['label'] == 'legitimate')

print(f"\nCurrent labels:")
print(f"  Phishing: {phishing_count}")
print(f"  Legitimate: {legit_count}")
