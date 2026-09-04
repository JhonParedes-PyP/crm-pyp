import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\base.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_script = """        // Default to first one (Gestión) if none matched exactly
        if (!foundOpen && allDetails.length > 0) {
            allDetails[0].setAttribute('open', '');
        }"""

new_script = """        // Default behavior if no specific sub-link matched
        if (!foundOpen && allDetails.length > 0) {
            if (currentPath.startsWith('/judicial/')) {
                allDetails.forEach(d => {
                    if (d.textContent.includes('Gestión Judicial')) {
                        d.setAttribute('open', '');
                        foundOpen = true;
                    }
                });
            }
        }
        
        // Final fallback to Gestión
        if (!foundOpen && allDetails.length > 0) {
            allDetails[0].setAttribute('open', '');
        }"""

if old_script in content:
    content = content.replace(old_script, new_script)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Menu matching script updated successfully.")
else:
    print("Could not find the fallback script block to replace!")
