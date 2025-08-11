// Envío manual con tipo explícito (tracking o guia_internacional)
function submitManualWithType(tipo) {
    const code = document.getElementById("codigo-input").value.trim();
    if (!code) {
        showError("Por favor ingresa un código.");
        return;
    }
    let url = "/register?";
    if (tipo === 'tracking') {
        url += `tracking=${encodeURIComponent(code)}`;
    } else if (tipo === 'guia_internacional') {
        url += `guia_internacional=${encodeURIComponent(code)}`;
    } else {
        showError("Tipo de registro no válido.");
        return;
    }
    window.location.href = url;
}
// Lógica para escanear códigos de barras usando html5-qrcode
// Requiere incluir html5-qrcode.min.js en el HTML

let html5QrCodeInstance = null;
let scanMessageTimeout;
let lastSuccessCode = '';
let successMessageVisible = false;

function startScannerLogic(readerDivId) {
    const readerDiv = document.getElementById(readerDivId);
    if (!readerDiv) {
        showError(`Error: No se encontró el elemento del lector de códigos con ID: ${readerDivId}.`);
        return;
    }

    // Detener cualquier instancia previa del escáner antes de iniciar una nueva
    // Solo intentar detener si la instancia existe y el readerDiv aún tiene hijos (indicando que el escáner está activo)
    if (html5QrCodeInstance && readerDiv.hasChildNodes()) {
        html5QrCodeInstance.stop().catch(err => {
            // Manejar el error NotFoundError silenciosamente si el elemento ya fue removido
            if (err.name === 'NotFoundError') {
                console.warn("scanner.js: Advertencia: El elemento del escáner ya no estaba en el DOM al intentar detenerlo.");
            } else {
                console.error("Error al detener escáner previo:", err);
            }
        });
        html5QrCodeInstance = null;
    } else if (html5QrCodeInstance) {
        // Si la instancia existe pero no hay hijos, simplemente la nulificamos
        html5QrCodeInstance = null;
        console.log("scanner.js: Instancia de escáner nulificada porque el elemento DOM no tiene hijos.");
    }

    // Limpiar el área de escaneo y asegurar que sea visible
    readerDiv.innerHTML = '';
    readerDiv.style.width = '100%'; // Asegurar que ocupe el ancho disponible
    readerDiv.style.minHeight = '300px'; // Asegurar una altura mínima para la cámara
    readerDiv.style.display = 'block'; // Asegurar que el div no esté oculto

    html5QrCodeInstance = new Html5Qrcode(readerDivId);
    // Configuración para escaneo continuo y mayor precisión
    const config = { 
        fps: 10, // Aumentar FPS para una detección más rápida
        qrbox: { width: 300, height: 200 }, // Aumentar el tamaño del cuadro de escaneo
        disableFlip: false // Permitir voltear la imagen si es necesario
    }; 

    showScannerStatus("Iniciando escáner...");

    html5QrCodeInstance.start(
        { facingMode: "environment" },
        config,
        qrCodeMessage => {
            // No detener el escáner; permitir escaneo continuo
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
    // Solo mostrar el mensaje de procesando si no hay un popup de confirmación activo
    const scanMsg = document.getElementById('scan-message');
    if (!scanMsg || !scanMsg.innerHTML.includes('¿Deseas registrar este paquete desconocido')) {
        showScannerStatus(`Código escaneado: ${code}. Procesando...`);
    }
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
    // Si el código es igual al último exitoso y el mensaje está visible, no vuelvas a mostrar el mensaje
    if (code === lastSuccessCode && successMessageVisible) {
        return;
    }
    fetch('/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code }) // Enviar un solo código
    })
    .then(res => {
        if (!res.ok) {
            // Si la respuesta no es OK (ej. 404, 500), intentar leer el mensaje de error del backend
            return res.json().then(errData => {
                throw new Error(errData.message || 'Error desconocido del servidor.');
            }).catch(() => {
                // Si no se puede parsear el JSON de error, es un error de comunicación genérico
                throw new Error('Error de comunicación con el servidor.');
            });
        }
        return res.json(); // Si la respuesta es OK, parsear el JSON normalmente
    })
    .then(data => {
        if (data.error) {
            showError(data.message || data.error); // Mostrar el mensaje de error del backend
            if (data.error === 'unknown_package_detected') { // Actualizado para el nuevo tipo de error
                showUnknownPackagePrompt(code, data.message); // Mostrar popup de confirmación
            }
        } else {
            // Actualizar los conteos en tiempo real ANTES de mostrar el mensaje de éxito
            if (data.total_pending_packages !== undefined) {
                const totalPendingBadge = document.querySelector('.card-body p:nth-child(1) .badge');
                if (totalPendingBadge) totalPendingBadge.textContent = data.total_pending_packages;
                const mobileTotalPending = document.getElementById('mobile-total-pending');
                if (mobileTotalPending) mobileTotalPending.textContent = data.total_pending_packages;
            }
            if (data.not_registered_packages !== undefined) {
                const notRegisteredBadge = document.querySelector('.card-body p:nth-child(2) .badge');
                if (notRegisteredBadge) notRegisteredBadge.textContent = data.not_registered_packages;
                const mobileNotRegistered = document.getElementById('mobile-not-registered');
                if (mobileNotRegistered) mobileNotRegistered.textContent = data.not_registered_packages;
            }
            if (data.missing_to_scan_packages !== undefined) {
                const missingToScanBadge = document.querySelector('.card-body p:nth-child(3) .badge');
                if (missingToScanBadge) missingToScanBadge.textContent = data.missing_to_scan_packages;
                const mobileMissingToScan = document.getElementById('mobile-missing-to-scan');
                if (mobileMissingToScan) mobileMissingToScan.textContent = data.missing_to_scan_packages;
            }
            // Mostrar mensaje de éxito solo si es un nuevo código
            lastSuccessCode = code;
            successMessageVisible = true;
            showSuccess(data.message);
            // Pausar el escáner brevemente después de un escaneo exitoso
            if (html5QrCodeInstance) {
                setTimeout(() => {
                    html5QrCodeInstance.resume();
                }, 1000); // Pausa de 1 segundo
            }
        }
    })
    .catch(error => {
        // Capturar errores lanzados por el bloque .then() o errores de red
        showError(error.message || 'Error de comunicación con el servidor.');
    });
}

// Función para mostrar mensaje de éxito (ahora recibe el mensaje y opcionalmente el ID del div)
function showSuccess(message, messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-success">${message}</div>`;
    }
    clearTimeout(scanMessageTimeout);
    // El mensaje de éxito se mantiene hasta que se detecte un nuevo código
    // No se borra automáticamente aquí
    // Se puede limpiar manualmente si se desea en otro flujo
}

function showError(error, messageDivId = 'scan-message') {
    console.error("Error mostrado (UI suprimida):", error); // Registrar el error en la consola
    // Si el error es de paquete desconocido, no limpiar el mensaje (el popup se encarga)
    if (typeof error === 'string' && error.includes('no corresponde a una guía conocida')) {
        return;
    }
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = '';
    }
    clearTimeout(scanMessageTimeout);
    // No se establece un timeout para limpiar, ya que no se muestra nada.
    // Si se desea un mensaje temporal, se puede ajustar aquí.
    // Por ahora, simplemente no se muestra el error en la UI.
}

function showScannerStatus(message, type = 'info', messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    }
}

function showRegisterPrompt(tracking, guia_internacional, message, messageDivId = 'scan-message') {
    // Redirigir automáticamente a la vista de registro de guía nueva manual
    let url = '/register?';
    if (tracking) {
        url += `tracking=${encodeURIComponent(tracking)}`;
    } else if (guia_internacional) {
        url += `guia_internacional=${encodeURIComponent(guia_internacional)}`;
    }
    window.location.href = url;
}

function showUnknownPackagePrompt(code, message, messageDivId = 'scan-message') {
    const msg = document.getElementById(messageDivId);
    if (msg) {
        msg.innerHTML = `
            <div class="alert alert-warning text-center">
                <p>${message}</p>
                <p>¿Deseas registrar este paquete desconocido (<strong>${code}</strong>)?</p>
                <div id="unknown-actions" class="d-flex flex-wrap justify-content-center gap-2 mt-3">
                    <button class="btn btn-success" onclick="confirmUnknownPackage('${code}')">Registrar como Guía</button>
                    <button class="btn btn-info" onclick="confirmUnknownTracking('${code}')">Registrar como Tracking</button>
                    <button class="btn btn-secondary" onclick="cancelUnknownPackage()">Cancelar</button>
                </div>
            </div>
        `;
    }
        // No limpiar el mensaje automáticamente
}

function confirmUnknownPackage(code) {
    fetch('/register_unknown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, code_type: 'guia_internacional' })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showError(data.message || data.error);
        } else {
            showSuccess(data.message);
            // Actualizar los conteos en tiempo real
            if (data.total_pending_packages !== undefined) {
                const totalPendingBadge = document.querySelector('.card-body p:nth-child(1) .badge');
                if (totalPendingBadge) totalPendingBadge.textContent = data.total_pending_packages;
                const mobileTotalPending = document.getElementById('mobile-total-pending');
                if (mobileTotalPending) mobileTotalPending.textContent = data.total_pending_packages;
            }
            if (data.not_registered_packages !== undefined) {
                const notRegisteredBadge = document.querySelector('.card-body p:nth-child(2) .badge');
                if (notRegisteredBadge) notRegisteredBadge.textContent = data.not_registered_packages;
                const mobileNotRegistered = document.getElementById('mobile-not-registered');
                if (mobileNotRegistered) mobileNotRegistered.textContent = data.not_registered_packages;
            }
            if (data.missing_to_scan_packages !== undefined) {
                const missingToScanBadge = document.querySelector('.card-body p:nth-child(3) .badge');
                if (missingToScanBadge) missingToScanBadge.textContent = data.missing_to_scan_packages;
                const mobileMissingToScan = document.getElementById('mobile-missing-to-scan');
                if (mobileMissingToScan) mobileMissingToScan.textContent = data.missing_to_scan_packages;
            }
        }
    })
    .catch(() => {
        showError('Error de comunicación con el servidor al registrar paquete desconocido.');
    })
    .finally(() => {
        // Reanudar el escáner después de la confirmación o cancelación
        startScannerLogic('reader');
    });
}

// Registrar como Tracking
function confirmUnknownTracking(code) {
    fetch('/register_unknown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, code_type: 'tracking' })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showError(data.message || data.error);
        } else {
            showSuccess(data.message);
            // Actualizar los conteos en tiempo real
            if (data.total_pending_packages !== undefined) {
                const totalPendingBadge = document.querySelector('.card-body p:nth-child(1) .badge');
                if (totalPendingBadge) totalPendingBadge.textContent = data.total_pending_packages;
                const mobileTotalPending = document.getElementById('mobile-total-pending');
                if (mobileTotalPending) mobileTotalPending.textContent = data.total_pending_packages;
            }
            if (data.not_registered_packages !== undefined) {
                const notRegisteredBadge = document.querySelector('.card-body p:nth-child(2) .badge');
                if (notRegisteredBadge) notRegisteredBadge.textContent = data.not_registered_packages;
                const mobileNotRegistered = document.getElementById('mobile-not-registered');
                if (mobileNotRegistered) mobileNotRegistered.textContent = data.not_registered_packages;
            }
            if (data.missing_to_scan_packages !== undefined) {
                const missingToScanBadge = document.querySelector('.card-body p:nth-child(3) .badge');
                if (missingToScanBadge) missingToScanBadge.textContent = data.missing_to_scan_packages;
                const mobileMissingToScan = document.getElementById('mobile-missing-to-scan');
                if (mobileMissingToScan) mobileMissingToScan.textContent = data.missing_to_scan_packages;
            }
        }
    })
    .catch(() => {
        showError('Error de comunicación con el servidor al registrar paquete desconocido.');
    })
    .finally(() => {
        // Reanudar el escáner después de la confirmación o cancelación
        startScannerLogic('reader');
    });
}

// Hacer startScannerLogic global para el HTML inline
window.startScannerLogic = startScannerLogic;

function confirmUnknownPackage(code) {
    fetch('/register_unknown', { // Nueva ruta para registrar paquetes desconocidos
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showError(data.message || data.error);
        } else {
            showSuccess(data.message);
            // Actualizar los conteos en tiempo real
            if (data.total_pending_packages !== undefined) {
                const totalPendingBadge = document.querySelector('.card-body p:nth-child(1) .badge');
                if (totalPendingBadge) totalPendingBadge.textContent = data.total_pending_packages;
                const mobileTotalPending = document.getElementById('mobile-total-pending');
                if (mobileTotalPending) mobileTotalPending.textContent = data.total_pending_packages;
            }
            if (data.not_registered_packages !== undefined) {
                const notRegisteredBadge = document.querySelector('.card-body p:nth-child(2) .badge');
                if (notRegisteredBadge) notRegisteredBadge.textContent = data.not_registered_packages;
                const mobileNotRegistered = document.getElementById('mobile-not-registered');
                if (mobileNotRegistered) mobileNotRegistered.textContent = data.not_registered_packages;
            }
            if (data.missing_to_scan_packages !== undefined) {
                const missingToScanBadge = document.querySelector('.card-body p:nth-child(3) .badge');
                if (missingToScanBadge) missingToScanBadge.textContent = data.missing_to_scan_packages;
                const mobileMissingToScan = document.getElementById('mobile-missing-to-scan');
                if (mobileMissingToScan) mobileMissingToScan.textContent = data.missing_to_scan_packages;
            }
        }
    })
    .catch(() => {
        showError('Error de comunicación con el servidor al registrar paquete desconocido.');
    })
    .finally(() => {
        // Reanudar el escáner después de la confirmación o cancelación
        startScannerLogic('reader'); 
    });
}

function cancelUnknownPackage() {
    showScannerStatus("Registro de paquete desconocido cancelado.", 'info');
    // Reanudar el escáner
    if (html5QrCodeInstance) {
        html5QrCodeInstance.resume();
    } else {
        startScannerLogic('reader');
    }
}

// Initial state setup (moved to index.html for automatic start)
// document.addEventListener('DOMContentLoaded', () => {
//     showScannerStatus("Listo para escanear.");
// });
