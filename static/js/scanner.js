// Lógica para escanear códigos de barras usando html5-qrcode
// Requiere incluir html5-qrcode.min.js en el HTML

let html5QrCodeInstance = null;
let scanMessageTimeout;

function startScannerLogic(readerDivId) {
    const readerDiv = document.getElementById(readerDivId);
    if (!readerDiv) {
        showError(`Error: No se encontró el elemento del lector de códigos con ID: ${readerDivId}.`);
        return;
    }

    // Limpiar el área de escaneo y asegurar que sea visible
    readerDiv.innerHTML = '';
    readerDiv.style.width = '100%'; // Asegurar que ocupe el ancho disponible
    readerDiv.style.minHeight = '300px'; // Asegurar una altura mínima para la cámara
    readerDiv.style.display = 'block'; // Asegurar que el div no esté oculto

    // Detener cualquier instancia previa del escáner antes de iniciar una nueva
    if (html5QrCodeInstance) {
        html5QrCodeInstance.stop().catch(err => console.error("Error al detener escáner previo:", err));
        html5QrCodeInstance = null;
    }

    html5QrCodeInstance = new Html5Qrcode(readerDivId);
    // Reducir fps para un escaneo más lento (1 fotograma cada 5 segundos)
    const config = { fps: 0.2, qrbox: 250 }; 

    showScannerStatus("Iniciando escáner...");

    html5QrCodeInstance.start(
        { facingMode: "environment" },
        config,
        qrCodeMessage => {
            // Detener el escáner después de un escaneo exitoso
            html5QrCodeInstance.stop().catch(() => {});
            html5QrCodeInstance = null;
            processScannedCode(qrCodeMessage);
        },
        errorMessage => {
            // Mostrar mensajes de error de escaneo si son relevantes
            // showScannerStatus(`Error de escaneo: ${errorMessage}`, 'danger');
        }
    ).catch(err => {
        const errorMessage = `No se pudo iniciar la cámara: ${err}. Por favor, asegúrate de haber otorgado permisos a la cámara en tu navegador y que la página se esté ejecutando en HTTPS o localhost.`;
        showErrorWithRetry(errorMessage, readerDivId);
    });
}

function showErrorWithRetry(message, readerDivId, messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-danger">
            ${message}
            <button class="btn btn-danger btn-sm mt-2" onclick="startScannerLogic('${readerDivId}')">Reintentar Escáner</button>
        </div>`;
    }
    clearTimeout(scanMessageTimeout); // No limpiar automáticamente para que el usuario vea el mensaje
}

function processScannedCode(code) {
    // Esta función es sobrescrita en edit_guia_status.html,
    // pero aquí está la implementación por defecto para index.html
    showScannerStatus(`Código escaneado: ${code}. Procesando...`);
    submitCode(code); // Enviar el código directamente
}

function submitManual() {
    const code = document.getElementById("codigo-input").value.trim();
    if (!code) {
        showError("Por favor ingresa un código.");
        return;
    }
    showScannerStatus(`Código ingresado manualmente: ${code}. Procesando...`);
    submitCode(code); // Enviar el código directamente
    document.getElementById("codigo-input").value = ''; // Limpiar input
}

function submitCode(code) {
    fetch('/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code }) // Enviar un solo código
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showError(data.message || data.error); // Mostrar el mensaje de error del backend
            if (data.error === 'guia_no_existente' || data.error === 'guia_no_esperada_en_sesion') {
                showRegisterPrompt(data.tracking, data.guia_internacional, data.message);
            }
        } else {
            showSuccess(data.message); // Mostrar el mensaje de éxito del backend
            // Actualizar los conteos en tiempo real
            if (data.total_pending_packages !== undefined) {
                document.querySelector('.card-body p:nth-child(1) .badge').textContent = data.total_pending_packages;
            }
            if (data.not_registered_packages !== undefined) {
                document.querySelector('.card-body p:nth-child(2) .badge').textContent = data.not_registered_packages;
            }
            if (data.missing_to_scan_packages !== undefined) {
                document.querySelector('.card-body p:nth-child(3) .badge').textContent = data.missing_to_scan_packages;
            }
        }
    })
    .catch(() => {
        showError('Error de comunicación con el servidor.');
    });
}

// Función para mostrar mensaje de éxito (ahora recibe el mensaje y opcionalmente el ID del div)
function showSuccess(message, messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-success">${message}</div>`;
    }
    clearTimeout(scanMessageTimeout);
    scanMessageTimeout = setTimeout(() => {
        msg.innerHTML = ''; // Limpiar el mensaje después de un tiempo
        showScannerStatus("Listo para escanear.", 'info', messageDivId); // Restablecer el estado del escáner
    }, 5000); // Mensaje visible por 5 segundos
}

function showError(error, messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-danger">${error}</div>`;
    }
    clearTimeout(scanMessageTimeout);
    scanMessageTimeout = setTimeout(() => {
        msg.innerHTML = ''; // Limpiar el mensaje después de un tiempo
        showScannerStatus("Listo para escanear.", 'info', messageDivId); // Restablecer el estado del escáner
    }, 5000); // Mensaje visible por 5 segundos
}

function showScannerStatus(message, type = 'info', messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    }
}

function showRegisterPrompt(tracking, guia_internacional, message, messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-warning">
            ${message} 
            <a href="/register?tracking=${encodeURIComponent(tracking || '')}&guia_internacional=${encodeURIComponent(guia_internacional || '')}" class="btn btn-sm btn-primary ms-2">Registrar como guía nueva</a>
        </div>`;
    }
    clearTimeout(scanMessageTimeout);
    scanMessageTimeout = setTimeout(() => {
        msg.innerHTML = ''; // Limpiar el mensaje después de un tiempo
        showScannerStatus("Listo para escanear.", 'info', messageDivId); // Restablecer el estado del escáner
    }, 10000); // Mensaje visible por 10 segundos para dar tiempo a registrar
}

// Initial state setup
document.addEventListener('DOMContentLoaded', () => {
    showScannerStatus("Listo para escanear.");
});
