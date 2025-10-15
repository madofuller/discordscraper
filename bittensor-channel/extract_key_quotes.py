import json
from datetime import datetime

# Load all the analysis files
files = {
    'videos': 'videos_demos.json',
    'docs': 'documentation.json',
    'tools': 'tools_simulators.json',
    'confusion': 'specific_confusion.json',
    'wants': 'user_wants.json',
    'personas': 'personas.json',
    'features': 'feature_requests.json'
}

data = {}
for key, filename in files.items():
    try:
        with open(f'C:\\Users\\madof\\OneDrive\\Desktop\\bittensor-channel\\{filename}', 'r', encoding='utf-8') as f:
            data[key] = json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")

# Generate comprehensive report
report = []

report.append("=" * 100)
report.append("COMPREHENSIVE DTAO LEARNING & EDUCATIONAL RESOURCE ANALYSIS")
report.append("Bittensor Community - April to October 2025")
report.append("=" * 100)
report.append("")

# SECTION 1: EDUCATIONAL RESOURCES CREATED
report.append("=" * 100)
report.append("1. EDUCATIONAL RESOURCES MENTIONED & CREATED")
report.append("=" * 100)
report.append("")

report.append("1.1 VIDEOS AND DEMOS")
report.append("-" * 100)
videos = data.get('videos', [])
video_links = {}
for v in videos[:100]:  # First 100 videos
    if v.get('links'):
        date = v.get('date', 'Unknown')
        author = v.get('author', 'Unknown')
        content = v.get('content', '')[:300]
        for link in v['links']:
            if link not in video_links:
                video_links[link] = {'date': date, 'author': author, 'context': content}

report.append(f"Total video/demo references: {len(videos)}")
report.append(f"Unique video links found: {len(video_links)}")
report.append("")
report.append("KEY VIDEOS SHARED:")
for i, (link, info) in enumerate(list(video_links.items())[:15], 1):
    report.append(f"{i}. {link}")
    report.append(f"   Date: {info['date']} | Shared by: {info['author']}")
    report.append(f"   Context: {info['context'][:200]}")
    report.append("")

report.append("")
report.append("1.2 DOCUMENTATION RESOURCES")
report.append("-" * 100)
docs = data.get('docs', [])
doc_links = {}
for d in docs[:200]:
    if d.get('links'):
        date = d.get('date', 'Unknown')
        author = d.get('author', 'Unknown')
        content = d.get('content', '')[:300]
        for link in d['links']:
            if 'docs' in link or 'github' in link or 'medium' in link or 'notion' in link:
                if link not in doc_links:
                    doc_links[link] = {'date': date, 'author': author, 'context': content}

report.append(f"Total documentation references: {len(docs)}")
report.append(f"Unique documentation links found: {len(doc_links)}")
report.append("")
report.append("KEY DOCUMENTATION SHARED:")
for i, (link, info) in enumerate(list(doc_links.items())[:15], 1):
    report.append(f"{i}. {link}")
    report.append(f"   Date: {info['date']} | Shared by: {info['author']}")
    report.append(f"   Context: {info['context'][:200]}")
    report.append("")

report.append("")
report.append("1.3 TOOLS AND SIMULATORS")
report.append("-" * 100)
tools = data.get('tools', [])
report.append(f"Total tool/simulator mentions: {len(tools)}")
report.append("")
report.append("SAMPLE TOOL DISCUSSIONS:")
for i, t in enumerate(tools[:20], 1):
    report.append(f"{i}. [{t.get('date')}] {t.get('author')}")
    report.append(f"   {t.get('content', '')[:300]}")
    report.append("")

# SECTION 2: USER CONFUSION PATTERNS
report.append("")
report.append("=" * 100)
report.append("2. USER CONFUSION PATTERNS - SPECIFIC CONCEPTS")
report.append("=" * 100)
report.append("")

confusion = data.get('confusion', {})
confusion_counts = {k: len(v) for k, v in confusion.items()}
sorted_confusion = sorted(confusion_counts.items(), key=lambda x: x[1], reverse=True)

report.append("CONFUSION FREQUENCY BY TOPIC:")
report.append("-" * 100)
for topic, count in sorted_confusion:
    report.append(f"• {topic.upper()}: {count} instances of confusion")
report.append("")

# Show examples for top confusion topics
for topic, count in sorted_confusion[:5]:
    report.append("")
    report.append(f"2.{sorted_confusion.index((topic, count))+1} {topic.upper()} CONFUSION EXAMPLES")
    report.append("-" * 100)
    examples = confusion.get(topic, [])[:15]
    for i, ex in enumerate(examples, 1):
        report.append(f"Example {i} [{ex.get('date')}] - {ex.get('author')}")
        report.append(f'"{ex.get("content", "")}"')
        report.append("")

# SECTION 3: WHAT USERS WANT
report.append("")
report.append("=" * 100)
report.append("3. WHAT USERS WANT BUT DON'T HAVE - DIRECT QUOTES")
report.append("=" * 100)
report.append("")

wants = data.get('wants', [])
report.append(f"Total user requests/wishes: {len(wants)}")
report.append("")

report.append("USER REQUESTS BY CATEGORY:")
report.append("-" * 100)

# Categorize wants
want_categories = {
    'visual': [],
    'simple': [],
    'tool': [],
    'guide': [],
    'calculator': [],
    'example': []
}

for w in wants:
    content_lower = w.get('content', '').lower()
    if any(word in content_lower for word in ['visual', 'diagram', 'chart', 'image']):
        want_categories['visual'].append(w)
    if any(word in content_lower for word in ['simple', 'simpler', 'easier', 'easy']):
        want_categories['simple'].append(w)
    if any(word in content_lower for word in ['tool', 'platform', 'dashboard']):
        want_categories['tool'].append(w)
    if any(word in content_lower for word in ['guide', 'tutorial', 'walkthrough', 'step']):
        want_categories['guide'].append(w)
    if any(word in content_lower for word in ['calculator', 'calculate', 'compute']):
        want_categories['calculator'].append(w)
    if any(word in content_lower for word in ['example', 'demo', 'show me']):
        want_categories['example'].append(w)

for category, items in want_categories.items():
    if items:
        report.append("")
        report.append(f"3.{list(want_categories.keys()).index(category)+1} REQUESTS FOR {category.upper()} ({len(items)} requests)")
        report.append("-" * 100)
        for i, item in enumerate(items[:15], 1):
            report.append(f"[{item.get('date')}] {item.get('author')}")
            report.append(f'"{item.get("content", "")}"')
            report.append("")

# SECTION 4: USER PERSONAS
report.append("")
report.append("=" * 100)
report.append("4. USER PERSONAS - DIFFERENT LEARNING NEEDS")
report.append("=" * 100)
report.append("")

personas = data.get('personas', {})
for persona, items in personas.items():
    report.append("")
    report.append(f"4.{list(personas.keys()).index(persona)+1} {persona.upper()} ({len(items)} relevant messages)")
    report.append("-" * 100)
    report.append("Sample concerns and questions:")
    for i, item in enumerate(items[:10], 1):
        report.append(f"{i}. [{item.get('date')}] {item.get('author')}")
        report.append(f"   {item.get('content', '')[:400]}")
        report.append("")

# SECTION 5: FEATURE REQUESTS
report.append("")
report.append("=" * 100)
report.append("5. SPECIFIC FEATURE REQUESTS")
report.append("=" * 100)
report.append("")

features = data.get('features', {})
for feature, items in features.items():
    report.append("")
    report.append(f"5.{list(features.keys()).index(feature)+1} {feature.upper().replace('_', ' ')} ({len(items)} requests)")
    report.append("-" * 100)
    for i, item in enumerate(items[:15], 1):
        report.append(f"[{item.get('date')}] {item.get('author')}")
        report.append(f'"{item.get("content", "")}"')
        report.append("")

# Save report
output_path = r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\COMPREHENSIVE_DTAO_LEARNING_REPORT.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f"Comprehensive report generated: {output_path}")
print(f"Report contains {len(report)} lines")
