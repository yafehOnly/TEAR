import os
import re

# Mapping of old ft.colors to new string format
color_mappings = {
    'ft.colors.AMBER': '"amber"',
    'ft.colors.AMBER_900': '"amber900"',
    'ft.colors.BLUE': '"blue"',
    'ft.colors.BLUE_GREY_100': '"bluegrey100"',
    'ft.colors.GREEN': '"green"',
    'ft.colors.GREY': '"grey"',
    'ft.colors.GREY_800': '"grey800"',
    'ft.colors.GREY_900': '"grey900"',
    'ft.colors.ORANGE': '"orange"',
    'ft.colors.RED': '"red"',
    'ft.colors.WHITE': '"white"',
    'ft.colors.BLACK': '"black"',
    'ft.colors.PRIMARY': '"primary"',
    'ft.colors.SECONDARY': '"secondary"',
    'ft.colors.BACKGROUND': '"background"',
    'ft.colors.SURFACE': '"surface"',
    'ft.colors.SURFACE_VARIANT': '"surfacevariant"',
    'ft.colors.OUTLINE': '"outline"',
}

def update_file(filepath):
    """Update a single Python file to use new color format"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace all color references
        for old_color, new_color in color_mappings.items():
            content = content.replace(old_color, new_color)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Updated: {filepath}")
            return True
        return False
            
    except Exception as e:
        print(f"[ERROR] updating {filepath}: {e}")
        return False

def main():
    """Update all Python files in the project"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    updated_count = 0
    
    # Walk through all Python files
    for root, dirs, files in os.walk(project_root):
        # Skip __pycache__ and other unnecessary directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and file != 'update_colors_flet028.py':
                filepath = os.path.join(root, file)
                if update_file(filepath):
                    updated_count += 1
    
    print(f"\n[OK] Update complete! {updated_count} files modified.")
    print("You can now run: python main.py")

if __name__ == "__main__":
    main()
