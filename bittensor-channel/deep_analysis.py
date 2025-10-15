import json
import re
from collections import defaultdict
from datetime import datetime

# Load the main JSON file
file_path = r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\Bittensor - [・Community・] - ☯・rao [1230665820859007039].json'

print("Loading JSON file...")
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])
print(f"Total messages: {len(messages)}")

# Detailed categorization
results = {
    'videos_demos': [],
    'documentation': [],
    'tools_simulators': [],
    'specific_confusion': defaultdict(list),
    'user_wants': [],
    'personas': {
        'validators': [],
        'developers': [],
        'holders': [],
        'newcomers': []
    },
    'feature_requests': {
        'calculator': [],
        'visual_aids': [],
        'interactive': [],
        'step_by_step': []
    },
    'timeline': defaultdict(list)
}

# Keywords for detailed analysis
video_patterns = [
    r'(video|youtube|recording|demo|stream|presentation)',
    r'(watch|watched|see|show|showcase)'
]

doc_patterns = [
    r'(documentation|docs|guide|tutorial|readme|wiki|written)',
    r'(article|blog|post|medium|explanation)'
]

tool_patterns = [
    r'(testnet|simulator|calculator|playground|sandbox)',
    r'(tool|dashboard|interface|platform)'
]

confusion_topics = {
    'dtao_concept': r'(what is dtao|how does dtao|dtao work|understand dtao|dtao mean)',
    'tokens': r'(subnet token|alpha token|what.*token|token.*work|token.*mean)',
    'mechanics': r'(how.*work|mechanism|process|flow|step)',
    'emissions': r'(emission|reward|incentive|distribution)',
    'staking': r'(stake|staking|validator|delegate)',
    'alpha': r'(alpha|alpha token|what.*alpha)',
    'yuma': r'(yuma|consensus)',
    'slippage': r'(slippage|liquidity|pool)',
    'tax': r'(tax|taxation|irs|reporting)',
}

# Process messages chronologically
for msg in messages:
    if not isinstance(msg, dict):
        continue

    content = msg.get('content', '')
    content_lower = content.lower()
    timestamp = msg.get('timestamp', '')
    author = msg.get('author', {})
    author_name = author.get('name', 'Unknown') if isinstance(author, dict) else 'Unknown'

    # Parse date for timeline
    try:
        if timestamp:
            msg_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            month_key = msg_date.strftime('%Y-%m')
            date_readable = msg_date.strftime('%Y-%m-%d')
        else:
            month_key = 'unknown'
            date_readable = 'unknown'
    except:
        month_key = 'unknown'
        date_readable = 'unknown'

    # Videos and Demos
    if any(re.search(p, content_lower) for p in video_patterns):
        links = re.findall(r'https?://[^\s]+', content)
        if links or 'video' in content_lower or 'demo' in content_lower:
            results['videos_demos'].append({
                'date': date_readable,
                'author': author_name,
                'content': content[:600],
                'links': links
            })
            results['timeline'][month_key].append(('video', author_name, content[:100]))

    # Documentation
    if any(re.search(p, content_lower) for p in doc_patterns):
        links = re.findall(r'https?://[^\s]+', content)
        results['documentation'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:600],
            'links': links
        })
        results['timeline'][month_key].append(('docs', author_name, content[:100]))

    # Tools and Simulators
    if any(re.search(p, content_lower) for p in tool_patterns):
        results['tools_simulators'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:600]
        })
        results['timeline'][month_key].append(('tool', author_name, content[:100]))

    # Specific Confusion Topics
    for topic, pattern in confusion_topics.items():
        if re.search(pattern, content_lower):
            results['specific_confusion'][topic].append({
                'date': date_readable,
                'author': author_name,
                'content': content[:500]
            })

    # User Wants (requests, wishes, needs)
    if re.search(r'(need|want|wish|would.*like|could.*have|should.*have|request|looking for)', content_lower):
        if re.search(r'(visual|diagram|chart|example|guide|tutorial|tool|calculator|simple|easier|better)', content_lower):
            results['user_wants'].append({
                'date': date_readable,
                'author': author_name,
                'content': content[:600]
            })

    # Personas identification
    if re.search(r'\b(validator|validating|validate|root network)\b', content_lower):
        results['personas']['validators'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    if re.search(r'\b(code|developer|dev|technical|github|implement|build)\b', content_lower):
        results['personas']['developers'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    if re.search(r'\b(holder|holding|investor|passive|bought|own tao)\b', content_lower):
        results['personas']['holders'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    if re.search(r'\b(new|newbie|newcomer|just.*start|just.*bought|don\'t understand|confused|learning)\b', content_lower):
        results['personas']['newcomers'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    # Feature Requests
    if re.search(r'(calculator|calculate|compute|estimate)', content_lower):
        results['feature_requests']['calculator'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    if re.search(r'(visual|diagram|chart|graph|infographic|image)', content_lower):
        results['feature_requests']['visual_aids'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    if re.search(r'(interactive|playground|sandbox|simulator|testnet)', content_lower):
        results['feature_requests']['interactive'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

    if re.search(r'(step.?by.?step|walkthrough|guide|how.?to|tutorial)', content_lower):
        results['feature_requests']['step_by_step'].append({
            'date': date_readable,
            'author': author_name,
            'content': content[:500]
        })

# Generate summary report
print("\n" + "="*80)
print("COMPREHENSIVE DTAO LEARNING RESOURCE ANALYSIS")
print("="*80)

print("\n1. EDUCATIONAL RESOURCES FOUND")
print("-" * 80)
print(f"Videos/Demos: {len(results['videos_demos'])}")
print(f"Documentation: {len(results['documentation'])}")
print(f"Tools/Simulators: {len(results['tools_simulators'])}")

print("\n2. CONFUSION PATTERNS BY TOPIC")
print("-" * 80)
for topic, items in sorted(results['specific_confusion'].items(), key=lambda x: len(x[1]), reverse=True):
    print(f"{topic}: {len(items)} instances")

print("\n3. USER PERSONAS")
print("-" * 80)
for persona, items in results['personas'].items():
    print(f"{persona.capitalize()}: {len(items)} relevant messages")

print("\n4. FEATURE REQUESTS")
print("-" * 80)
for feature, items in results['feature_requests'].items():
    print(f"{feature.replace('_', ' ').title()}: {len(items)} requests")

print("\n5. TIMELINE SUMMARY")
print("-" * 80)
for month in sorted(results['timeline'].keys()):
    if month != 'unknown':
        print(f"{month}: {len(results['timeline'][month])} educational activities")

# Save detailed results
output_files = {
    'videos_demos': results['videos_demos'],
    'documentation': results['documentation'],
    'tools_simulators': results['tools_simulators'],
    'specific_confusion': dict(results['specific_confusion']),
    'user_wants': results['user_wants'],
    'personas': results['personas'],
    'feature_requests': results['feature_requests'],
    'timeline': dict(results['timeline'])
}

for key, data in output_files.items():
    with open(f'C:\\Users\\madof\\OneDrive\\Desktop\\bittensor-channel\\{key}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "="*80)
print("Detailed results saved to individual JSON files")
print("="*80)
