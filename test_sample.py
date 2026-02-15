import json

data = json.load(open('my_phishing_dataset.json'))
phishing = [x for x in data if x['label'] == 'phishing']
legit = [x for x in data if x['label'] == 'legitimate']

print('✅ Sample PHISHING URLs from training data:')
for i, item in enumerate(phishing[:5], 1):
    url = item['url']
    print(f"{i}. {url[:75]}...")

print('\n✅ Sample LEGITIMATE URLs from training data:')  
for i, item in enumerate(legit[:5], 1):
    url = item['url']
    print(f"{i}. {url[:75]}...")
