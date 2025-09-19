#!/usr/bin/env python3
"""
Script to replace all therapist references with coordinator references
"""

import re
import os

def update_file(file_path):
    """Update a single file to replace therapist with coordinator"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Store original content to check if changes were made
        original_content = content
        
        # Replace function names and variables
        replacements = [
            # Function names
            (r'\bget_therapist_phone\b', 'get_coordinator_phone'),
            (r'\bhandle_therapist_query\b', 'handle_coordinator_query'),
            (r'\bprocess_therapist_recommendation\b', 'process_coordinator_recommendation'),
            (r'\bhandle_therapist_confirmation\b', 'handle_coordinator_confirmation'),
            (r'\bescalate_to_therapist\b', 'escalate_to_coordinator'),
            
            # Variable names
            (r'\btherapist_phone\b', 'coordinator_phone'),
            (r'\btherapist_name\b', 'coordinator_name'),
            (r'\btherapist_id\b', 'coordinator_id'),
            (r'\btherapist_info\b', 'coordinator_info'),
            (r'\btherapist_notification\b', 'coordinator_notification'),
            
            # String content references  
            (r'"therapist_phone":', '"coordinator_phone":'),
            (r'"therapist_name":', '"coordinator_name":'),
            (r'"therapist_notification":', '"coordinator_notification":'),
            
            # Documentation and comments
            (r'\btherapist\b', 'coordinator'),
            (r'\bTherapist\b', 'Coordinator'),
            (r'\bTHERAPIST\b', 'COORDINATOR'),
            
            # Specific text replacements
            (r'authorized therapists', 'authorized coordinators'),
            (r'authorized therapist', 'authorized coordinator'),
            (r'the therapist', 'the coordinator'),
            (r'our therapist', 'our coordinator'),
            
            # Configuration references
            (r'THERAPIST_PHONE_NUMBER', 'COORDINATOR_PHONE_NUMBER'),
            (r'THERAPIST_NAME', 'COORDINATOR_NAME'),
        ]
        
        # Apply replacements
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Check if any changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated {file_path}")
            return True
        else:
            print(f"⏸️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update files"""
    # Files to update
    files_to_update = [
        "therapy_booking_app/app/services/adk_agent_service.py",
        "therapy_booking_app/app/models/models.py",
        "therapy_booking_app/app/services/booking_service.py",
        "therapy_booking_app/app/api/webhooks.py",
        "other_scripts/environment_config.py"
    ]
    
    updated_files = []
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_file(file_path):
                updated_files.append(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Updated {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()