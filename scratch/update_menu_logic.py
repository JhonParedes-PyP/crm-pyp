import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\base.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_script = """        allDetails.forEach(details => {
            const links = details.querySelectorAll('a');
            links.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href !== '#' && currentPath.includes(href)) {
                    details.setAttribute('open', '');
                    foundOpen = true;
                }
            });
        });"""

new_script = """        allDetails.forEach(details => {
            const links = details.querySelectorAll('a');
            links.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href !== '#') {
                    // Check if the current URL starts with the href (ignoring the root '/' to prevent matching everything)
                    // Or if it's an exact match
                    if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                        details.setAttribute('open', '');
                        foundOpen = true;
                    }
                }
            });
        });"""

if old_script in content:
    content = content.replace(old_script, new_script)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Menu matching script updated successfully.")
else:
    print("Could not find the script block to replace!")
