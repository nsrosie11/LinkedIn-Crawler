import os
import json
from collections import defaultdict

def count_leads_per_template():
    # Initialize counters
    template_counts = defaultdict(int)
    
    # Count leads in data directory
    data_dir = os.path.join(os.getcwd(), 'data')
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                # Extract template name from filename
                template_name = filename.split('_20')[0] if '_20' in filename else filename.split('.json')[0]
                
                try:
                    with open(os.path.join(data_dir, filename), 'r') as f:
                        data = json.load(f)
                        if 'leads' in data and isinstance(data['leads'], list):
                            template_counts[template_name] += len(data['leads'])
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    
    # Count leads in db directory
    db_dir = os.path.join(os.getcwd(), 'db')
    if os.path.exists(db_dir):
        for filename in os.listdir(db_dir):
            if filename.endswith('.json') and filename != 'templates.json' and filename != 'leads_data.json' and filename != 'successful_connections.json':
                # Extract template name from filename (format: YYYY-MM-DD-template_name.json)
                parts = filename.split('-')
                if len(parts) >= 4:
                    # Join all parts after the date components
                    template_name = '-'.join(parts[3:]).replace('.json', '')
                    
                    try:
                        with open(os.path.join(db_dir, filename), 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                template_counts[template_name] += len(data)
                            elif isinstance(data, dict) and 'leads' in data and isinstance(data['leads'], list):
                                template_counts[template_name] += len(data['leads'])
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")
    
    return template_counts

def main():
    template_counts = count_leads_per_template()
    
    # Sort templates by count (descending)
    sorted_templates = sorted(template_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Print results
    print("\nLead Count by Template:")
    print("-" * 50)
    print(f"{'Template Name':<30} {'Lead Count':>10}")
    print("-" * 50)
    
    for template, count in sorted_templates:
        print(f"{template:<30} {count:>10}")
    
    print("-" * 50)
    print(f"{'Total':<30} {sum(template_counts.values()):>10}")

if __name__ == "__main__":
    main()