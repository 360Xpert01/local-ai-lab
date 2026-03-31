#!/usr/bin/env python3
"""Generate combined training dataset for advanced coding, architecture, and testing."""

import json
import glob
from pathlib import Path
from typing import List, Dict

# Training data directories
TRAINING_DIRS = [
    "training_data/advanced/coding",
    "training_data/advanced/architecture",
    "training_data/advanced/testing",
    "training_data/code",
    "training_data/architecture",
    "training_data/security",
]

def load_jsonl_files(directory: str) -> List[Dict]:
    """Load all JSONL files from a directory."""
    data = []
    pattern = Path(directory) / "*.jsonl"
    
    for file_path in glob.glob(str(pattern)):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            if 'instruction' in record and 'output' in record:
                                data.append(record)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return data

def format_for_unsloth(data: List[Dict]) -> List[Dict]:
    """Format data for Unsloth fine-tuning."""
    formatted = []
    
    for item in data:
        # Alpaca-style format
        instruction = item.get('instruction', '')
        input_text = item.get('input', '')
        output = item.get('output', '')
        
        if input_text:
            prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        else:
            prompt = f"### Instruction:\n{instruction}\n\n### Response:\n"
        
        formatted.append({
            'instruction': instruction,
            'input': input_text,
            'output': output,
            'text': prompt + output
        })
    
    return formatted

def generate_training_dataset():
    """Generate the complete training dataset."""
    print("🔧 Advanced Coding Training Dataset Generator")
    print("=" * 50)
    
    all_data = []
    stats = {}
    
    # Load from all directories
    for directory in TRAINING_DIRS:
        if not Path(directory).exists():
            print(f"⚠️  Directory not found: {directory}")
            continue
        
        print(f"📂 Loading from: {directory}")
        data = load_jsonl_files(directory)
        all_data.extend(data)
        stats[directory] = len(data)
        print(f"   ✓ Loaded {len(data)} examples")
    
    print("\n" + "=" * 50)
    print(f"📊 Total examples: {len(all_data)}")
    print("\nBreakdown:")
    for dir_name, count in stats.items():
        print(f"  • {dir_name}: {count}")
    
    if not all_data:
        print("\n❌ No training data found!")
        return
    
    # Format for training
    print("\n🔄 Formatting for Unsloth...")
    formatted_data = format_for_unsloth(all_data)
    
    # Save raw combined dataset
    output_file = "training_data/advanced_combined_raw.jsonl"
    print(f"\n💾 Saving raw dataset to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Save formatted dataset
    formatted_file = "training_data/advanced_combined_formatted.json"
    print(f"💾 Saving formatted dataset to: {formatted_file}")
    with open(formatted_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, indent=2, ensure_ascii=False)
    
    # Save statistics
    stats_file = "training_data/advanced_training_stats.json"
    stats_data = {
        "total_examples": len(all_data),
        "breakdown": stats,
        "files_generated": [
            output_file,
            formatted_file
        ],
        "categories": {
            "advanced_coding": stats.get("training_data/advanced/coding", 0),
            "architecture": stats.get("training_data/advanced/architecture", 0),
            "testing": stats.get("training_data/advanced/testing", 0),
            "code_frameworks": stats.get("training_data/code", 0),
            "security": stats.get("training_data/security", 0)
        }
    }
    
    with open(stats_file, 'w') as f:
        json.dump(stats_data, f, indent=2)
    
    print(f"💾 Statistics saved to: {stats_file}")
    print("\n✅ Dataset generation complete!")
    print("\nNext steps:")
    print("  1. Run the Colab notebook for fine-tuning")
    print("  2. Upload the generated JSONL file to Colab")
    print("  3. Train with: python -m colab_training.train_advanced")

if __name__ == "__main__":
    generate_training_dataset()
