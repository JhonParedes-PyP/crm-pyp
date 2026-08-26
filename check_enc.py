html_path = r"c:\CRM PYP\cobranza\templates\cobranza\base.html"
with open(html_path, 'r', encoding='utf-8') as f:
    c = f.read()
    print(c.split('class="user-name"')[1][:50])
