document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ auth.js cargado correctamente en el DOM.");

    // --- MANEJO DEL LOGIN ---
    const formLogin = document.getElementById("formLoginModal");
    if (formLogin) {
        formLogin.addEventListener("submit", async (e) => {
            e.preventDefault();
            console.log("🔐 Intentando iniciar sesión...");

            const user = document.getElementById("loginUsername").value;
            const pass = document.getElementById("loginPassword").value;
            const alerta = document.getElementById("alertaErrorLogin");
            const btn = document.getElementById("btnSubmitLogin");

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span> Verificando...';
            alerta.classList.add("d-none");

            try {
                const formData = new URLSearchParams();
                formData.append('username', user);
                formData.append('password', pass);

                const response = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.access_token) {
                        localStorage.setItem("token", data.access_token);
                        window.location.href = "dashboard.html";
                    }
                } else {
                    const err = await response.json();
                    alerta.textContent = err.detail || "Credenciales incorrectas.";
                    alerta.classList.remove("d-none");
                }
            } catch (err) {
                console.error("❌ Error de red en login:", err);
                alerta.textContent = "Error de conexión con el servidor.";
                alerta.classList.remove("d-none");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "Ingresar al Sistema";
            }
        });
    }

    // --- MANEJO DEL REGISTRO ---
    const formRegistro = document.getElementById("formRegistroModal");
    if (formRegistro) {
        console.log("✅ Formulario de registro detectado en la vista.");
        
        formRegistro.addEventListener("submit", async (e) => {
            e.preventDefault();
            console.log("🚀 Evento submit interceptado en el registro.");

            const nombre = document.getElementById("regNombre").value;
            const email = document.getElementById("regEmail").value;
            const password = document.getElementById("regPassword").value;
            const rol = document.getElementById("regRol").value;
            
            console.log("📋 Datos capturados para registro:", { nombre, email, password, rol });

            const alertaError = document.getElementById("alertaErrorRegistro");
            const alertaExito = document.getElementById("alertaExitoRegistro");
            const btn = document.getElementById("btnSubmitRegistro");

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span> Registrando...';
            alertaError.classList.add("d-none");
            alertaExito.classList.add("d-none");

            try {
                console.log(`🌐 Enviando petición POST a: ${API_URL}/auth/registro`);
                const response = await fetch(`${API_URL}/auth/registro`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombre, email, password, rol })
                });

                console.log("📥 Respuesta recibida del servidor, status:", response.status);

                if (response.ok) {
                    const dataRes = await response.json();
                    console.log("✅ Registro exitoso en backend:", dataRes);

                    alertaExito.textContent = "¡Registro exitoso! Ya puedes iniciar sesión.";
                    alertaExito.classList.remove("d-none");
                    formRegistro.reset();
                    
                    setTimeout(() => {
                        $('#registroModal').modal('hide');
                        $('#loginModal').modal('show');
                        alertaExito.classList.add("d-none");
                    }, 2000);
                } else {
                    const err = await response.json();
                    console.warn("⚠️ Error devuelto por el backend:", err);
                    alertaError.textContent = err.detail || "No se pudo completar el registro.";
                    alertaError.classList.remove("d-none");
                }
            } catch (err) {
                console.error("❌ Excepción en fetch de registro:", err);
                alertaError.textContent = "Error de conexión con el servidor.";
                alertaError.classList.remove("d-none");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "Completar Registro";
            }
        });
    } else {
        console.warn("⚠️ No se encontró el elemento con ID 'formRegistroModal' en el DOM.");
    }
});