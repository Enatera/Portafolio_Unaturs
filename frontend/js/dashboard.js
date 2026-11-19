let listaUsuariosGlobal = []; // Para almacenar los usuarios y filtrar sin llamadas extra

async function verificarYcargarAdmin() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const res = await fetch(`${API_URL}/admin/usuarios`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            listaUsuariosGlobal = await res.json();
            document.getElementById("navAdminItem").style.display = "block"; // Mostrar en el sidebar
            renderizarTablaUsuarios(listaUsuariosGlobal);
        }
    } catch (err) {
        console.log("Usuario sin privilegios de administración.");
    }
}

function renderizarTablaUsuarios(usuarios) {
    const tbody = document.getElementById("tablaUsuariosAdmin");
    tbody.innerHTML = "";

    if (usuarios.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No se encontraron usuarios con este filtro.</td></tr>';
        return;
    }

    usuarios.forEach(u => {
        let badgeEstado = u.aprobado 
            ? '<span class="badge badge-success">Aprobado</span>' 
            : '<span class="badge badge-warning text-dark">Pendiente</span>';
        
        let btnAprobar = (!u.aprobado && u.rol.toLowerCase() === 'profesor')
            ? `<button class="btn btn-sm btn-success rounded-pill px-2 mb-1" onclick="aprobarUsuario(${u.id})"><i class="fas fa-check"></i> Aprobar</button>`
            : '';

        tbody.innerHTML += `
            <tr>
                <td>#${u.id}</td>
                <td class="font-weight-bold">${u.nombre}</td>
                <td>${u.email}</td>
                <td><span class="badge badge-secondary">${u.rol}</span></td>
                <td>${badgeEstado}</td>
                <td>
                    ${btnAprobar}
                    <div class="input-group input-group-sm" style="width: 160px;">
                        <select class="form-control form-control-sm" id="nuevoRol_${u.id}">
                            <option value="Estudiante" ${u.rol === 'Estudiante' ? 'selected' : ''}>Estudiante</option>
                            <option value="Profesor" ${u.rol === 'Profesor' ? 'selected' : ''}>Profesor</option>
                            <option value="Administrador" ${u.rol === 'Administrador' ? 'selected' : ''}>Admin</option>
                        </select>
                        <div class="input-group-append">
                            <button class="btn btn-outline-warning text-dark" onclick="cambiarRol(${u.id})" title="Guardar Rol"><i class="fas fa-save"></i></button>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    });
}

function filtrarUsuariosTabla() {
    const filtro = document.getElementById("filtroRolUsuarios").value;
    if (filtro === "todos") {
        renderizarTablaUsuarios(listaUsuariosGlobal);
    } else {
        const filtrados = listaUsuariosGlobal.filter(u => u.rol.toLowerCase() === filtro.toLowerCase());
        renderizarTablaUsuarios(filtrados);
    }
}

function mostrarSeccion(seccion) {
    const vistaProyectos = document.getElementById("vistaProyectos");
    const vistaAdmin = document.getElementById("vistaAdmin");
    const titulo = document.getElementById("tituloVistaPrincipal");

    if (seccion === 'proyectos') {
        vistaProyectos.style.display = "block";
        vistaAdmin.style.display = "none";
        titulo.textContent = "Panel de Proyectos";
    } else if (seccion === 'admin') {
        vistaProyectos.style.display = "none";
        vistaAdmin.style.display = "block";
        titulo.textContent = "Gestión de Usuarios y Roles";
    }
}

async function aprobarUsuario(id) {
    const token = localStorage.getItem("token");
    const res = await fetch(`${API_URL}/admin/usuarios/${id}/aprobar`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        alert("¡Profesor aprobado con éxito!");
        verificarYcargarAdmin();
    }
}

async function cambiarRol(id) {
    const token = localStorage.getItem("token");
    const nuevoRol = document.getElementById(`nuevoRol_${id}`).value;

    const res = await fetch(`${API_URL}/admin/usuarios/${id}/rol?nuevo_rol=${nuevoRol}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (res.ok) {
        alert("¡Rol actualizado con éxito!");
        verificarYcargarAdmin();
    } else {
        alert("No se pudo actualizar el rol.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    verificarYcargarAdmin();

    async function cargarCarrerasSelect() {
    const select = document.getElementById("selectCarreras");
    if (!select) return;

    try {
        const res = await fetch(`${API_URL}/carreras`);
        if (res.ok) {
            const carreras = await res.json();
            select.innerHTML = '<option value="">Selecciona una carrera...</option>';
            carreras.forEach(c => {
                // El usuario ve c.nombre, pero el formulario envía c.id
                select.innerHTML += `<option value="${c.id}">${c.nombre}</option>`;
            });
        }
    } catch (err) {
        select.innerHTML = '<option value="1">Turismo (Por defecto)</option>';
    }
}
});

async function cambiarRol(id) {
    const token = localStorage.getItem("token");
    const selectElement = document.getElementById(`nuevoRol_${id}`);
    const nuevoRol = selectElement.value;

    try {
        const res = await fetch(`${API_URL}/admin/usuarios/${id}/rol`, {
            method: 'PUT',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nuevo_rol: nuevoRol })
        });

        if (res.ok) {
            alert("¡Rol actualizado con éxito!");
            verificarYcargarAdmin(); // Recargar la tabla con los datos actualizados
        } else {
            const err = await res.json();
            alert(err.detail || "No se pudo actualizar el rol.");
        }
    } catch (err) {
        console.error("Error de red al cambiar rol:", err);
        alert("Error de conexión con el servidor.");
    }
}

async function cargarPerfilUsuario() {
    const token = localStorage.getItem("token");
    try {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
            const user = await res.json();
            document.getElementById("userDisplay").textContent = user.nombre;
            document.getElementById("dropdownRolInfo").textContent = `Rol: ${user.rol}`;
        }
    } catch (err) {
        console.error("Error cargando perfil:", err);
    }
}

function compartirProyecto(titulo, url) {
    // Si el navegador soporta la API nativa de compartir (móviles/Edge/Safari)
    if (navigator.share) {
        navigator.share({
            title: `Proyecto Unaturs: ${titulo}`,
            text: `Revisa este proyecto de investigación turística en Unaturs:`,
            url: url
        }).catch(console.error);
    } else {
        // Fallback para PC: Copiar enlace al portapapeles
        navigator.clipboard.writeText(url).then(() => {
            alert(`¡Enlace copiado al portapapeles!\nListo para compartir: ${url}`);
        });
    }
}