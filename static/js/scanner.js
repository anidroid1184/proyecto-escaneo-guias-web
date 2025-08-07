// Lógica para escanear códigos de barras usando html5-qrcode
// Requiere incluir html5-qrcode.min.js en el HTML

let html5QrCodeInstance = null;

function startScanner() {
    // Limpiar el área de escaneo antes de iniciar
    const readerDiv = document.getElementById('reader');
    if (readerDiv) {
        readerDiv.innerHTML = '';
    }
    // Detener instancia previa si existe
    if (html5QrCodeInstance) {
        html5QrCodeInstance.stop().catch(() => {});
        html5QrCodeInstance = null;
    }
    html5QrCodeInstance = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: 250 };
    html5QrCodeInstance.start(
        { facingMode: "environment" },
        config,
        qrCodeMessage => {
            html5QrCodeInstance.stop().then(() => {
                submitCode(qrCodeMessage);
            }).catch(() => {
                submitCode(qrCodeMessage);
            });
        },
        errorMessage => {
            // Puedes mostrar errores de escaneo si lo deseas
        }
    ).catch(err => {
        showError("No se pudo iniciar la cámara: " + err + "<br>Recuerda que en móviles solo funciona por HTTPS o localhost.");
    });
}

function submitCode(code) {
    fetch('/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error === 'no_registrado') {
            showRegisterPrompt(data.codigo);
        } else if (data.error) {
            showError(data.error);
        } else {
            showSuccess(data.nombre, data.tipo, data.timestamp);
        }
    })
    .catch(() => {
        showError('Error de comunicación con el servidor.');
    });
}

// Función para mostrar mensaje de éxito
function showSuccess(nombre, tipo, timestamp) {
    const msg = document.getElementById('scan-message');
    if (msg) {
        msg.innerHTML = `<div class="alert alert-success">${nombre} - ${tipo.toUpperCase()} registrada a las ${timestamp}</div>`;
    }
}

// Función para mostrar error
function showError(error) {
    const msg = document.getElementById('scan-message');
    if (msg) {
        msg.innerHTML = `<div class="alert alert-danger">${error}</div>`;
    }
}

// Función para mostrar opción de registrar persona nueva
function showRegisterPrompt(codigo) {
    const msg = document.getElementById('scan-message');
    if (msg) {
        msg.innerHTML = `<div class="alert alert-warning">Código no registrado. <a href="/register?codigo=${encodeURIComponent(codigo)}" class="btn btn-sm btn-primary ms-2">Registrar persona nueva</a></div>`;
    }
}
