import re
from pathlib import Path

def refactor():
    for p in Path('.').rglob('*.py'):
        if 'venv' in p.parts or 'site-packages' in p.parts:
            continue
        if p.name == 'theme.py' or p.name == 'refactor.py':
            continue
            
        content = p.read_text('utf8')
        if 'theme.COLORS' not in content:
            continue
            
        # Replace CTK color usages: fg_color=theme.COLORS["key"] -> fg_color=theme.c("key")
        # Replace text_color, hover_color, button_color
        
        # We can just replace ALL theme.COLORS["key"] with theme.c("key") 
        # and then for matplotlib lines, we will change theme.c to theme.mc.
        
        new_content = re.sub(r'theme\.COLORS\["([^"]+)"\]', r'theme.c("\1")', content)
        
        # For matplotlib methods that use color:
        # ax.plot, ax.axvline, Patch, ax.set_ylabel, ax.tick_params, facecolor, ListedColormap, segments, edgecolors, c=, color=
        # This is a bit risky. Let's just manually replace theme.c with theme.mc on lines that contain matplotlib keywords
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            if 'theme.c' in line:
                if any(kw in line for kw in ['ax.', 'ax2.', 'color=', 'facecolor=', 'edgecolor=', 'c=', 'edgecolors=', 'colors=', 'Patch', 'ListedColormap']):
                    # Check if it's not a CTK widget creation
                    if 'ctk.' not in line and 'fg_color' not in line and 'text_color' not in line and 'hover_color' not in line:
                        lines[i] = line.replace('theme.c', 'theme.mc')
        
        p.write_text('\n'.join(lines), 'utf8')
        print(f"Refactored {p}")

if __name__ == '__main__':
    refactor()
