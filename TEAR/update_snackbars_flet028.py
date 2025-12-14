"""
Script to update SnackBar API to Flet 0.28.3
Instead of:
  page.snack_bar = ft.SnackBar(...)
  page.snack_bar.open = True
  page.update()
  
Use:
  page.open(ft.SnackBar(...))
"""
import os
import re

def update_snackbar_api(filepath):
    """Update snackbar API calls"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match the 3-line snackbar pattern
        # page.snack_bar = ft.SnackBar(TEXT)
        # page.snack_bar.open = True  
        # page.update()
        pattern = r'(\s+)page\.snack_bar = (ft\.SnackBar\([^)]+\))\s*\n\s+page\.snack_bar\.open = True\s*\n\s+page\.update\(\)'
        replacement = r'\1page.open(\2)'
        
        content = re.sub(pattern, replacement, content)
        
        # Also handle standalone snackbar assignments (without the .open = True pattern)
        # These should also be converted to page.open()
        pattern2 = r'(\s+)page\.snack_bar = (ft\.SnackBar\([^)]+\))\s*$'
        replacement2 = r'\1page.open(\2)'
        
        content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
        
        # Remove any remaining standalone page.snack_bar.open = True lines
        content = re.sub(r'\s+page\.snack_bar\.open = True\s*\n', '', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated SnackBars in: {filepath}")
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
        if file.endswith('.py'):
            filepath = os.path.join(views_dir, file)
            if update_snackbar_api(filepath):
                updated_count += 1
    
    print(f"\n[OK] Update complete! {updated_count} files updated.")
    print("All SnackBars now use page.open() API")

if __name__ == "__main__":
    main()
