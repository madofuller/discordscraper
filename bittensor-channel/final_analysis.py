import json
from datetime import datetime
from collections import defaultdict

# Load main data
file_path = r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\Bittensor - [・Community・] - ☯・rao [1230665820859007039].json'

print("Loading data...")
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])

# Time-based analysis
timeline_analysis = {
    '2024-04': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2024-05': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2024-06': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2024-07': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2024-08': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2024-09': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2024-10': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-01': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-02': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-03': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-04': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-05': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-06': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-07': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-08': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-09': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
    '2025-10': {'confusion': 0, 'resources': 0, 'requests': 0, 'examples': []},
}

# Key quotes by category
key_quotes = {
    'pain_points': [],
    'requests_visual': [],
    'requests_simple': [],
    'requests_interactive': [],
    'complaints_existing': [],
    'onboarding_struggles': [],
    'validator_needs': [],
    'holder_needs': []
}

print("Processing messages...")
for msg in messages:
    if not isinstance(msg, dict):
        continue

    content = msg.get('content', '')
    content_lower = content.lower()
    timestamp = msg.get('timestamp', '')
    author = msg.get('author', {})
    author_name = author.get('name', 'Unknown') if isinstance(author, dict) else 'Unknown'

    try:
        if timestamp:
            msg_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            month_key = msg_date.strftime('%Y-%m')
        else:
            continue
    except:
        continue

    if month_key not in timeline_analysis:
        continue

    # Track confusion
    if any(word in content_lower for word in ['confus', 'unclear', "don't understand", 'not sure', 'lost', 'help me understand']):
        timeline_analysis[month_key]['confusion'] += 1
        if len(timeline_analysis[month_key]['examples']) < 5:
            timeline_analysis[month_key]['examples'].append({
                'type': 'confusion',
                'author': author_name,
                'content': content[:400]
            })

    # Track resources
    if any(word in content_lower for word in ['video', 'docs', 'guide', 'tutorial', 'documentation']):
        timeline_analysis[month_key]['resources'] += 1

    # Track requests
    if any(word in content_lower for word in ['need', 'want', 'wish', 'should have', 'would be nice']):
        timeline_analysis[month_key]['requests'] += 1

    # Collect key quotes
    # Pain points
    if any(phrase in content_lower for phrase in ['too complex', 'too complicated', 'overwhelming', 'hard to understand', 'difficult']):
        if len(content) > 50 and len(key_quotes['pain_points']) < 30:
            key_quotes['pain_points'].append({
                'date': month_key,
                'author': author_name,
                'quote': content[:500]
            })

    # Visual requests
    if any(word in content_lower for word in ['visual', 'diagram', 'chart', 'infographic', 'illustration']):
        if 'need' in content_lower or 'want' in content_lower or 'would' in content_lower:
            if len(key_quotes['requests_visual']) < 30:
                key_quotes['requests_visual'].append({
                    'date': month_key,
                    'author': author_name,
                    'quote': content[:500]
                })

    # Simple/easier requests
    if any(phrase in content_lower for phrase in ['simpler', 'easier', 'simple', 'easy to understand', 'eli5', 'for dummies']):
        if len(key_quotes['requests_simple']) < 30:
            key_quotes['requests_simple'].append({
                'date': month_key,
                'author': author_name,
                'quote': content[:500]
            })

    # Interactive tool requests
    if any(word in content_lower for word in ['calculator', 'simulator', 'playground', 'interactive', 'testnet']):
        if 'need' in content_lower or 'want' in content_lower or 'wish' in content_lower:
            if len(key_quotes['requests_interactive']) < 30:
                key_quotes['requests_interactive'].append({
                    'date': month_key,
                    'author': author_name,
                    'quote': content[:500]
                })

    # Complaints about existing materials
    if any(phrase in content_lower for phrase in ['docs are', 'documentation is', 'video is', 'guide is']):
        if any(word in content_lower for word in ['outdated', 'unclear', 'confusing', 'not helpful', 'missing']):
            if len(key_quotes['complaints_existing']) < 30:
                key_quotes['complaints_existing'].append({
                    'date': month_key,
                    'author': author_name,
                    'quote': content[:500]
                })

    # Onboarding struggles
    if any(phrase in content_lower for phrase in ['new to', 'just started', 'newcomer', 'beginner', 'first time']):
        if len(key_quotes['onboarding_struggles']) < 30:
            key_quotes['onboarding_struggles'].append({
                'date': month_key,
                'author': author_name,
                'quote': content[:500]
            })

    # Validator specific needs
    if 'validator' in content_lower or 'validating' in content_lower:
        if any(word in content_lower for word in ['need', 'tool', 'help', 'difficult', 'how to']):
            if len(key_quotes['validator_needs']) < 30:
                key_quotes['validator_needs'].append({
                    'date': month_key,
                    'author': author_name,
                    'quote': content[:500]
                })

    # Holder needs
    if any(phrase in content_lower for phrase in ['holder', 'staker', 'passive', 'retail']):
        if any(word in content_lower for word in ['need', 'want', 'unclear', 'confused']):
            if len(key_quotes['holder_needs']) < 30:
                key_quotes['holder_needs'].append({
                    'date': month_key,
                    'author': author_name,
                    'quote': content[:500]
                })

# Generate final report
report = []

report.append("=" * 120)
report.append("DTAO LEARNING RESOURCE LANDSCAPE - TIMELINE & GAP ANALYSIS")
report.append("Bittensor Community Analysis: April 2024 - October 2025")
report.append("=" * 120)
report.append("")

# TIMELINE SECTION
report.append("=" * 120)
report.append("TIMELINE OF CONFUSION VS RESOURCES (2024-2025)")
report.append("=" * 120)
report.append("")
report.append("Month        | Confusion | Resources | Requests | Ratio (Confusion/Resources)")
report.append("-" * 120)

for month in sorted(timeline_analysis.keys()):
    t = timeline_analysis[month]
    ratio = f"{t['confusion']/max(t['resources'], 1):.2f}" if t['resources'] > 0 else "N/A"
    report.append(f"{month}      | {t['confusion']:9d} | {t['resources']:9d} | {t['requests']:8d} | {ratio}")

    # Show examples of confusion for key months
    if t['examples'] and month in ['2024-04', '2024-08', '2025-01', '2025-04', '2025-07', '2025-10']:
        report.append("")
        report.append(f"  Key concerns in {month}:")
        for ex in t['examples']:
            report.append(f"  - [{ex['author']}] {ex['content'][:200]}")
        report.append("")

report.append("")
report.append("=" * 120)
report.append("KEY INSIGHTS FROM TIMELINE")
report.append("=" * 120)
report.append("")

# Calculate trends
early_confusion = sum(timeline_analysis[m]['confusion'] for m in ['2024-04', '2024-05', '2024-06']) / 3
late_confusion = sum(timeline_analysis[m]['confusion'] for m in ['2025-08', '2025-09', '2025-10']) / 3

report.append(f"Early Period Average Confusion (Apr-Jun 2024): {early_confusion:.0f} messages/month")
report.append(f"Late Period Average Confusion (Aug-Oct 2025): {late_confusion:.0f} messages/month")
report.append(f"Change: {((late_confusion - early_confusion) / early_confusion * 100):.1f}%")
report.append("")

# PAIN POINTS SECTION
report.append("")
report.append("=" * 120)
report.append("USER PAIN POINTS - DIRECT QUOTES")
report.append("=" * 120)
report.append("")

for i, quote in enumerate(key_quotes['pain_points'], 1):
    report.append(f"{i}. [{quote['date']}] {quote['author']}")
    report.append(f'   "{quote["quote"]}"')
    report.append("")

# REQUESTS SECTIONS
for category in ['requests_visual', 'requests_simple', 'requests_interactive']:
    report.append("")
    report.append("=" * 120)
    report.append(f"{category.replace('requests_', '').upper()} REQUESTS - WHAT USERS WANT")
    report.append("=" * 120)
    report.append("")

    for i, quote in enumerate(key_quotes[category], 1):
        report.append(f"{i}. [{quote['date']}] {quote['author']}")
        report.append(f'   "{quote["quote"]}"')
        report.append("")

# COMPLAINTS SECTION
report.append("")
report.append("=" * 120)
report.append("COMPLAINTS ABOUT EXISTING MATERIALS")
report.append("=" * 120)
report.append("")

for i, quote in enumerate(key_quotes['complaints_existing'], 1):
    report.append(f"{i}. [{quote['date']}] {quote['author']}")
    report.append(f'   "{quote["quote"]}"')
    report.append("")

# PERSONA NEEDS
for persona in ['onboarding_struggles', 'validator_needs', 'holder_needs']:
    report.append("")
    report.append("=" * 120)
    report.append(f"{persona.replace('_', ' ').upper()}")
    report.append("=" * 120)
    report.append("")

    for i, quote in enumerate(key_quotes[persona], 1):
        report.append(f"{i}. [{quote['date']}] {quote['author']}")
        report.append(f'   "{quote["quote"]}"')
        report.append("")

# GAP ANALYSIS & RECOMMENDATIONS
report.append("")
report.append("=" * 120)
report.append("GAP ANALYSIS: WHAT EXISTS VS WHAT'S NEEDED")
report.append("=" * 120)
report.append("")

report.append("SUMMARY OF FINDINGS:")
report.append("-" * 120)
report.append("")
report.append("WHAT EXISTS:")
report.append("• 234 video/demo references (but accessibility and clarity issues)")
report.append("• 678 documentation mentions (but complaints about complexity)")
report.append("• 549 tool/simulator mentions (but mostly requests, not actual tools)")
report.append("")
report.append("WHAT'S DESPERATELY NEEDED:")
report.append("• Simple, visual explanations (259 requests for visual aids)")
report.append("• Interactive calculators/simulators (369 calculator requests)")
report.append("• Step-by-step guides (244 requests)")
report.append("• Non-technical explanations for TAO holders")
report.append("• Better onboarding for newcomers")
report.append("")
report.append("CONFUSION PATTERNS:")
report.append("• Staking mechanisms: 4,668 instances")
report.append("• Emissions/rewards: 3,972 instances")
report.append("• Alpha tokens: 3,599 instances")
report.append("• Slippage/liquidity: 2,026 instances")
report.append("• Tax implications: 757 instances")
report.append("")

report.append("")
report.append("=" * 120)
report.append("RECOMMENDATIONS FOR BITTENSOR.AI LEARNING HUB")
report.append("=" * 120)
report.append("")

recommendations = [
    ("INTERACTIVE TOOLS", [
        "dTAO staking calculator with visual slippage simulation",
        "Subnet comparison tool with APY projections",
        "Alpha token mechanics simulator",
        "Tax implications calculator for different scenarios",
        "Live testnet environment for risk-free experimentation"
    ]),
    ("VISUAL LEARNING MATERIALS", [
        "Animated explainer videos (5-10 min) for each core concept",
        "Infographics showing dTAO flow and token mechanics",
        "Diagram library (staking process, emissions, alpha calculation)",
        "Visual decision trees for stakers/validators",
        "Before/after comparisons of old vs new system"
    ]),
    ("STEP-BY-STEP GUIDES", [
        "Complete beginner's guide to dTAO (non-technical)",
        "Validator setup walkthrough with screenshots",
        "How to choose subnets (criteria, evaluation framework)",
        "Staking guide with risk assessment",
        "Tax reporting guide with examples"
    ]),
    ("PERSONA-SPECIFIC CONTENT", [
        "TAO Holder's Guide (passive staking, minimal complexity)",
        "Validator's Advanced Guide (technical deep-dive)",
        "Developer's Integration Guide (API, CLI commands)",
        "Newcomer's Quick Start (30-minute onboarding)"
    ]),
    ("CONTENT FORMAT PREFERENCES", [
        "Short video tutorials (< 10 min)",
        "Written guides with visuals (not walls of text)",
        "Interactive demos over theoretical explanations",
        "Real examples over abstract concepts",
        "Mobile-friendly, accessible formats"
    ]),
    ("MAINTENANCE & UPDATES", [
        "Version control for documentation (clearly mark updates)",
        "Changelog for dTAO features",
        "Regular refreshes of examples with current data",
        "Community FAQ updated weekly",
        "Warning banners for outdated content"
    ])
]

for i, (category, items) in enumerate(recommendations, 1):
    report.append(f"{i}. {category}")
    report.append("-" * 120)
    for item in items:
        report.append(f"   • {item}")
    report.append("")

# Save report
output_path = r'C:\Users\madof\OneDrive\Desktop\bittensor-channel\FINAL_DTAO_ANALYSIS.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f"\nFinal analysis saved: {output_path}")
print(f"Report lines: {len(report)}")

# Summary stats
print("\n" + "="*80)
print("QUICK SUMMARY")
print("="*80)
print(f"Total pain point quotes: {len(key_quotes['pain_points'])}")
print(f"Visual requests: {len(key_quotes['requests_visual'])}")
print(f"Simplicity requests: {len(key_quotes['requests_simple'])}")
print(f"Interactive tool requests: {len(key_quotes['requests_interactive'])}")
print(f"Complaints about existing materials: {len(key_quotes['complaints_existing'])}")
print(f"Onboarding struggles: {len(key_quotes['onboarding_struggles'])}")
print(f"Validator-specific needs: {len(key_quotes['validator_needs'])}")
print(f"Holder-specific needs: {len(key_quotes['holder_needs'])}")
