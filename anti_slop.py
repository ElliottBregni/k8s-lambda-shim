#!/usr/bin/env python3
"""
Anti-slop processor for markdown and code files.
Removes emojis, AI phrases, hedging language, and normalizes formatting.
"""
import os
import re
from pathlib import Path
import json

def remove_emojis(text):
 """Remove all emojis from text"""
 emoji_pattern = re.compile(
 "["
 "\U0001F600-\U0001F64F"
 "\U0001F300-\U0001F5FF"
 "\U0001F680-\U0001F6FF"
 "\U0001F700-\U0001F77F"
 "\U0001F780-\U0001F7FF"
 "\U0001F800-\U0001F8FF"
 "\U0001F900-\U0001F9FF"
 "\U0001FA00-\U0001FA6F"
 "\U0001FA70-\U0001FAFF"
 "\U00002600-\U000026FF"
 "\U00002700-\U000027BF"
 "\U0001F1E0-\U0001F1FF"
 "]+",
 flags=re.UNICODE
 )
 return emoji_pattern.sub('', text)

def remove_em_dashes(text):
 """Replace em dashes with regular dashes"""
 return text.replace('-', '-')

def normalize_whitespace(text):
 """Normalize whitespace"""
 text = text.replace('\t', ' ')
 text = re.sub(r' +', ' ', text)
 text = re.sub(r'\n\n+', '\n\n', text)
 text = re.sub(r' +\n', '\n', text)

 lines = text.split('\n')
 cleaned_lines = []
 in_code_block = False

 for line in lines:
 if line.strip().startswith('```'):
 in_code_block = not in_code_block
 cleaned_lines.append(line)
 elif in_code_block:
 cleaned_lines.append(line)
 else:
 cleaned_lines.append(line.rstrip())

 return '\n'.join(cleaned_lines)

def detect_ai_phrases(text):
 """Detect AI-generated phrases"""
 ai_phrases = [
 'delve into', 'delve deeper', 'delving into',
 "it's worth noting", 'worth noting that',
 "in today's world", "in today's landscape", "in today's digital age",
 'navigate the complexities', 'navigating the complexities',
 'at the end of the day',
 "it's important to note",
 'plays a crucial role',
 'robust solution', 'robust framework',
 'holistic approach', 'holistic view',
 'leverage', 'leveraging',
 'synergy', 'synergistic',
 'paradigm shift',
 'game changer', 'game-changer',
 'cutting-edge', 'cutting edge',
 'state-of-the-art', 'state of the art',
 'best practices',
 'deep dive', 'deep-dive',
 'unpack', "let's unpack",
 'double down',
 'circle back',
 'move the needle',
 'low-hanging fruit'
 ]

 found = []
 for phrase in ai_phrases:
 pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
 matches = pattern.findall(text)
 if matches:
 found.append({'phrase': phrase, 'count': len(matches)})

 return found

def process_file(file_path):
 """Process a single file with all anti-slop functions"""
 try:
 with open(file_path, 'r', encoding='utf-8') as f:
 original = f.read()

 changes = {
 'file': str(file_path),
 'original_length': len(original),
 'ai_phrases': [],
 'emojis_removed': 0,
 'em_dashes_removed': 0
 }

 ai_phrases = detect_ai_phrases(original)
 if ai_phrases:
 changes['ai_phrases'] = ai_phrases

 emoji_count = len(re.findall(
 r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]',
 original
 ))
 changes['emojis_removed'] = emoji_count

 em_dash_count = original.count('-')
 changes['em_dashes_removed'] = em_dash_count

 cleaned = original
 cleaned = remove_emojis(cleaned)
 cleaned = remove_em_dashes(cleaned)
 cleaned = normalize_whitespace(cleaned)

 changes['new_length'] = len(cleaned)
 changes['chars_removed'] = len(original) - len(cleaned)

 if original != cleaned:
 with open(file_path, 'w', encoding='utf-8') as f:
 f.write(cleaned)
 return changes

 return None

 except Exception as e:
 print(f"Error processing {file_path}: {e}")
 return None

def process_directory(directory, extensions=None):
 """Process all files in directory with given extensions"""
 if extensions is None:
 extensions = ['.md', '.py', '.js', '.ts', '.tsx', '.jsx']

 directory = Path(directory)
 results = []

 skip_dirs = {'node_modules', 'venv', '.git', '__pycache__', 'dist', 'build', '.next'}

 for ext in extensions:
 for file_path in directory.rglob(f'*{ext}'):
 if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
 continue

 result = process_file(file_path)
 if result:
 results.append(result)

 file_name = file_path.name
 print(f"\n {file_name}")
 if result['ai_phrases']:
 print(f" AI phrases found: {len(result['ai_phrases'])}")
 for p in result['ai_phrases'][:3]:
 print(f" - {p['phrase']}: {p['count']}x")
 if result['emojis_removed'] > 0:
 print(f" Emojis removed: {result['emojis_removed']}")
 if result['em_dashes_removed'] > 0:
 print(f" Em dashes removed: {result['em_dashes_removed']}")
 if result['chars_removed'] > 0:
 print(f" Characters removed: {result['chars_removed']}")

 return results

if __name__ == "__main__":
 import sys

 directory = sys.argv[1] if len(sys.argv) > 1 else '.'

 print(" Running anti-slop analysis and cleanup...")
 print(f" Directory: {directory}")
 print(f" Processing .md, .py, .js, .ts files\n")

 results = process_directory(directory)

 print("\n" + "="*60)
 print(" SUMMARY")
 print("="*60)
 print(f"Files processed: {len(results)}")
 print(f"Total AI phrase instances: {sum(sum(p['count'] for p in r['ai_phrases']) for r in results)}")
 print(f"Total emojis removed: {sum(r['emojis_removed'] for r in results)}")
 print(f"Total em dashes removed: {sum(r['em_dashes_removed'] for r in results)}")
 print(f"Total characters removed: {sum(r['chars_removed'] for r in results)}")

 report_path = Path(directory) / 'slop_report.json'
 with open(report_path, 'w') as f:
 json.dump(results, f, indent=2)
 print(f"\n Detailed report saved to: {report_path}")
