import json
import re
from collections import defaultdict
from datetime import datetime

# Load the JSON file
file_path = r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\Bittensor - [・Community・] - ☯・rao [1230665820859007039].json'

print("Loading JSON file...")
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])
print(f"Total messages: {len(messages)}")

# Keywords for analysis
educational_keywords = {
    'video': r'\b(video|youtube|watch|demo|recording|stream)\b',
    'documentation': r'\b(docs|documentation|guide|tutorial|readme|wiki)\b',
    'learning_tools': r'\b(testnet|simulator|calculator|playground|sandbox|interactive)\b',
    'confusion': r'\b(confus|unclear|don\'t understand|not sure|lost|help|explain|what does|how does|why does)\b',
    'request': r'\b(need|want|wish|would be nice|could we have|request|suggestion|should have)\b',
    'links': r'(https?://[^\s]+)',
    'visual': r'\b(visual|diagram|chart|graph|image|screenshot|example)\b',
}

# Results storage
educational_resources = []
confusion_patterns = []
user_requests = []
timeline = defaultdict(list)
creators = defaultdict(int)

# Process messages
for msg in messages:
    if not isinstance(msg, dict):
        continue

    content = msg.get('content', '').lower()
    timestamp = msg.get('timestamp', '')
    author = msg.get('author', {})
    author_name = author.get('name', 'Unknown') if isinstance(author, dict) else 'Unknown'

    # Parse date
    try:
        if timestamp:
            msg_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            month_key = msg_date.strftime('%Y-%m')
        else:
            month_key = 'unknown'
    except:
        month_key = 'unknown'

    # Check for educational resources
    if re.search(educational_keywords['video'], content, re.IGNORECASE):
        links = re.findall(educational_keywords['links'], msg.get('content', ''))
        educational_resources.append({
            'type': 'video',
            'author': author_name,
            'date': timestamp,
            'content': msg.get('content', '')[:500],
            'links': links
        })
        creators[author_name] += 1
        timeline[month_key].append(('video', author_name))

    if re.search(educational_keywords['documentation'], content, re.IGNORECASE):
        links = re.findall(educational_keywords['links'], msg.get('content', ''))
        educational_resources.append({
            'type': 'documentation',
            'author': author_name,
            'date': timestamp,
            'content': msg.get('content', '')[:500],
            'links': links
        })
        creators[author_name] += 1
        timeline[month_key].append(('documentation', author_name))

    if re.search(educational_keywords['learning_tools'], content, re.IGNORECASE):
        educational_resources.append({
            'type': 'tool',
            'author': author_name,
            'date': timestamp,
            'content': msg.get('content', '')[:500]
        })
        timeline[month_key].append(('tool', author_name))

    # Check for confusion
    if re.search(educational_keywords['confusion'], content, re.IGNORECASE):
        confusion_patterns.append({
            'author': author_name,
            'date': timestamp,
            'content': msg.get('content', '')[:800]
        })

    # Check for requests/wishes
    if re.search(educational_keywords['request'], content, re.IGNORECASE):
        # Look for visual/learning related requests
        if any(re.search(kw, content, re.IGNORECASE) for kw in [
            educational_keywords['visual'],
            educational_keywords['learning_tools'],
            r'\b(example|step-by-step|walkthrough|better|easier)\b'
        ]):
            user_requests.append({
                'author': author_name,
                'date': timestamp,
                'content': msg.get('content', '')[:800]
            })

# Save results to files for detailed analysis
print("\n=== SUMMARY ===")
print(f"Educational resources found: {len(educational_resources)}")
print(f"Confusion patterns found: {len(confusion_patterns)}")
print(f"User requests found: {len(user_requests)}")

# Top creators
print("\n=== TOP CONTENT CREATORS ===")
for creator, count in sorted(creators.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{creator}: {count} contributions")

# Timeline summary
print("\n=== TIMELINE BY MONTH ===")
for month in sorted(timeline.keys()):
    if month != 'unknown':
        print(f"{month}: {len(timeline[month])} educational items")

# Save detailed results
with open(r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\educational_resources.json', 'w', encoding='utf-8') as f:
    json.dump(educational_resources, f, indent=2, ensure_ascii=False)

with open(r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\confusion_patterns.json', 'w', encoding='utf-8') as f:
    json.dump(confusion_patterns, f, indent=2, ensure_ascii=False)

with open(r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\user_requests.json', 'w', encoding='utf-8') as f:
    json.dump(user_requests, f, indent=2, ensure_ascii=False)

print("\nDetailed results saved to separate JSON files.")
