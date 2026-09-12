import os

file_path = r'c:\CRM PYP\cobranza\templates\cobranza\gestionar.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's fix the inline style in the script we just wrote into `content` if we already modified it.
# Actually we haven't run the script yet! Let's rewrite the patch script to be correct.

target = "{% block content %}"

banner_code = """{% block content %}

<!-- BANNER AUTO-DIALER -->
<div id="autodialer-banner" style="display: none; background: #28a745; color: white; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); justify-content: space-between; align-items: center; font-weight: bold; font-size: 16px;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 20px; animation: pulse 1s infinite;">📡</span>
        <span>MODO AUTO-MARCADOR ACTIVO</span>
        <span id="autodialer-status" style="margin-left: 15px; background: rgba(0,0,0,0.2); padding: 4px 10px; border-radius: 4px; font-size: 14px;">Iniciando llamada en 3s...</span>
    </div>
    <button onclick="detenerAutoDialer()" type="button" style="background: #dc3545; color: white; border: 2px solid white; padding: 5px 15px; border-radius: 6px; font-weight: bold; cursor: pointer;">
        ⏹️ Pausar / Salir
    </button>
</div>
"""

# Script that goes at the end of the file. Let's find endblock.
target_end = "{% endblock %}"

script_code = """
<script>
    // AUTO-DIALER LOGIC
    var urlParams = new URLSearchParams(window.location.search);
    var autoDialerActivo = urlParams.get('auto_dialer') === '1';
    var timerDialer = null;

    if (autoDialerActivo) {
        var banner = document.getElementById('autodialer-banner');
        if(banner) {
            banner.style.display = 'flex';
        }
        
        var count = 3;
        var statusEl = document.getElementById('autodialer-status');
        
        timerDialer = setInterval(function() {
            count--;
            if (count > 0) {
                statusEl.innerText = "Iniciando llamada en " + count + "s...";
            } else {
                clearInterval(timerDialer);
                statusEl.innerText = "📞 Llamando ahora...";
                
                // Encontrar el primer botón de "Llamar" visible
                var callBtns = document.querySelectorAll('button[onclick^="realizarLlamada"]');
                var botonLlamar = Array.from(callBtns).find(b => b.offsetParent !== null);
                
                if (botonLlamar) {
                    // Click the button
                    botonLlamar.click();
                } else {
                    statusEl.innerText = "⚠️ No hay números disponibles para llamar.";
                }
            }
        }, 1000);
    } else {
        var banner = document.getElementById('autodialer-banner');
        if(banner) banner.style.display = 'none';
    }

    function detenerAutoDialer() {
        if (timerDialer) clearInterval(timerDialer);
        
        // Quitar auto_dialer=1 de la URL actual para que al recargar o guardar ya no siga
        var url = new URL(window.location);
        url.searchParams.delete('auto_dialer');
        window.history.replaceState({}, '', url);
        
        // Actualizar el input hidden "parametros_url" en el form si existe, para quitar auto_dialer
        var paramsInputs = document.querySelectorAll('input[name="parametros_url"]');
        paramsInputs.forEach(inp => {
            var valParams = new URLSearchParams(inp.value);
            valParams.delete('auto_dialer');
            inp.value = valParams.toString();
        });

        document.getElementById('autodialer-banner').style.display = 'none';
        alert("Modo Auto-Marcador pausado.");
    }
</script>

{% endblock %}"""

content = content.replace(target, banner_code, 1) # replace first occurrence

if target_end in content:
    content = content.rsplit(target_end, 1) # split on last occurrence
    content = content[0] + script_code
else:
    content += script_code

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("PATCH GESTIONAR SUCCESS")
