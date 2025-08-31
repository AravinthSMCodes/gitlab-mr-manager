#!/usr/bin/env python3
"""
Debug script to check MR labels and understand badge counting
"""

import os
import gitlab

# Configuration
GITLAB_URL = 'https://git.csez.zohocorpin.com'
GITLAB_TOKEN = 'VJaybg9Leej4zscS_Xf4'
PROJECT_ID = '16895'

# Initialize GitLab client
gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
project = gl.projects.get(PROJECT_ID)

def analyze_mr_labels():
    """Analyze MR labels to understand badge counting"""
    print("🔍 Analyzing MR Labels for Badge Counting")
    print("=" * 60)
    
    # Get all open MRs
    open_mrs = project.mergerequests.list(state='opened', get_all=True)
    
    to_be_reviewed_count = 0
    reviewed_count = 0
    good_to_merge_count = 0
    
    print(f"\n📊 Total Open MRs: {len(list(open_mrs))}")
    print("\n" + "=" * 60)
    
    for mr in open_mrs:
        labels = mr.labels if mr.labels else []
        label_names = [label.lower() for label in labels]
        
        print(f"\n🔸 MR #{mr.iid}: {mr.title}")
        print(f"   Labels: {labels}")
        print(f"   Labels (lowercase): {label_names}")
        
        # Check "To Be Reviewed" logic
        has_review_labels = all(label in label_names for label in ['self reviewed', 'peer reviewed', 'ready to be reviewed'])
        has_reviewed_label = 'reviewed' in label_names
        is_to_be_reviewed = has_review_labels and not has_reviewed_label
        
        if is_to_be_reviewed:
            to_be_reviewed_count += 1
            print(f"   ✅ To Be Reviewed: YES")
        
        # Check "Reviewed" logic
        has_all_review_labels = all(label in label_names for label in ['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed'])
        has_gtm_label = 'good to merge' in label_names
        is_reviewed = has_all_review_labels and not has_gtm_label
        
        if is_reviewed:
            reviewed_count += 1
            print(f"   ✅ Reviewed: YES")
        
        # Check "Good to Merge" logic
        required_labels = ['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed', 'good to merge']
        has_all_required_labels = all(label in label_names for label in required_labels)
        if has_all_required_labels:
            good_to_merge_count += 1
            print(f"   ✅ Good to Merge: YES")
    
    print("\n" + "=" * 60)
    print("📈 SUMMARY:")
    print(f"   To Be Reviewed: {to_be_reviewed_count}")
    print(f"   Reviewed: {reviewed_count}")
    print(f"   Good to Merge: {good_to_merge_count}")
    print("=" * 60)

if __name__ == "__main__":
    analyze_mr_labels()
