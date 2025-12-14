"""
Script to update ALL dialog open/close calls to Flet 0.28.3 API
- dialog.open = True → page.open(dialog)  
- dialog.open = False → page.close(dialog)
"""
import os
import re

def update_dialog_api(filepath):
    """Update dialog API calls"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove any leftover page.dialog = dialog lines
        content = re.sub(r'\s+page\.dialog = dialog.*?\n', '\n', content)
        
        # Replace dialog.open = True with page.open(dialog)
        # This handles variations with/without page.update()
        content = re.sub(
            r'(\s+)dialog\.open = True\s*\n(\s+)page\.update\(\)',
            r'\1page.open(dialog)',
            content
        )
        content = re.sub(
            r'(\s+)dialog\.open = True',
            r'\1page.open(dialog)',
            content
        )
        
        # Replace dialog.open = False with page.close(dialog)
        content = re.sub(
            r'(\s+)dialog\.open = False',
            r'\1page.close(dialog)',
            content
        )
        
        # Replace _dialog.open patterns for other dialog names
        content = re.sub(
            r'(\w+_dialog)\.open = True',
            r'page.open(\1)',
            content
        )
        content = re.sub(
            r'(\w+_dialog)\.open = False',
            r'page.close(\1)',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated dialog API in: {filepath}")
            return True
        return False
            
    except Exception as e:
        print(f"[ERROR] {filepath}: {e}")
        return False

def main():
    """Update all view files"""
    views_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'views')
    updated_count = 0
    
    for file in os.listdir(views_dir):
        if file.endswith('.py') and file != 'clients_view.py':  # Skip clients_view as already fixed
            filepath = os.path.join(views_dir, file)
            if update_dialog_api(filepath):
                updated_count += 1
    
    print(f"\n[OK] Update complete! {updated_count} files updated.")
    print("All dialogs now use page.open() and page.close()")

if __name__ == "__main__":
    main()
