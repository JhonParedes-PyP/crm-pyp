import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\base.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove hardcoded open
content = content.replace('<details class="menu-group" open>', '<details class="menu-group">')

# Add JS script for accordion menu behavior
script = """
</nav>
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const allDetails = document.querySelectorAll('details.menu-group');
        
        // Accordion behavior: close others when one opens
        allDetails.forEach(details => {
            details.addEventListener('toggle', (e) => {
                if (details.open) {
                    allDetails.forEach(other => {
                        if (other !== details) {
                            other.removeAttribute('open');
                        }
                    });
                }
            });
        });

        // Auto-open the menu group that contains the current URL
        const currentPath = window.location.pathname;
        let foundOpen = false;
        
        allDetails.forEach(details => {
            const links = details.querySelectorAll('a');
            links.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href !== '#' && currentPath.includes(href)) {
                    details.setAttribute('open', '');
                    foundOpen = true;
                }
            });
        });
        
        // Default to first one (Gestión) if none matched exactly
        if (!foundOpen && allDetails.length > 0) {
            allDetails[0].setAttribute('open', '');
        }
    });
</script>
"""

if '</nav>' in content:
    # Remove any existing script that we might have added, just in case
    # Not likely, but let's just replace </nav>
    content = content.replace('</nav>', script)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("base.html updated successfully.")
else:
    print("Could not find </nav>!")
