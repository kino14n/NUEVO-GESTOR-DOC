// =================== URL Base de la API ===================
// URL REAL de tu backend en Clever Cloud, construida con tu ID
const API_BASE_URL = 'https://app-61c0049d-13c8-450d-a8d3-b902dcaa4b61.cleverapps.io';

// =================== Sistema de Pestañas ===================
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.add('hidden'));
    document.getElementById('tab-' + btn.dataset.tab).classList.remove('hidden');
  });
});

window.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.tab-btn[data-tab="buscar"]').click();
});

// =================== MODAL AZUL REUTILIZABLE ===================
function showModal({title = '', message = '', okText = 'Aceptar', cancelText = 'Cancelar', onOk = null, onCancel = null, hideCancel = false}) {
  const overlay = document.getElementById('modal-overlay');
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-message').innerHTML = message;
  const btnOk = document.getElementById('modal-ok');
  const btnCancel = document.getElementById('modal-cancel');
  btnOk.textContent = okText;
  btnCancel.textContent = cancelText;

  btnOk.onclick = () => {
    overlay.classList.add('hidden');
    if (typeof onOk === 'function') onOk();
  };
  btnCancel.onclick = () => {
    overlay.classList.add('hidden');
    if (typeof onCancel === 'function') onCancel();
  };
  if (hideCancel) btnCancel.style.display = 'none';
  else btnCancel.style.display = 'inline-block';

  overlay.classList.remove('hidden');
}

// =================== BUSCAR ===================
document.getElementById('buscar-btn').addEventListener('click', () => {
  const input = document.getElementById('buscar-input').value.trim();
  if (!input) return alert('Ingresa texto para buscar');
  const resultadoDiv = document.getElementById('buscar-resultado');
  resultadoDiv.textContent = "Buscando: " + input + " ...";

  fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: input })
  })
    .then(res => res.json())
    .then(data => {
      resultadoDiv.innerHTML = '';
      if (!data.ok || !data.resultados || data.resultados.length === 0) {
        resultadoDiv.innerHTML = "<span>No se encontraron resultados.</span>";
      } else {
        data.resultados.forEach(doc => {
          const pdfUrl = `${API_BASE_URL}/static/uploads/${doc.path}`;
          resultadoDiv.innerHTML += `<div><b>${doc.name}</b> (${doc.date}): ${doc.codigos_extraidos} <a href="${pdfUrl}" target="_blank" class="text-blue-500 hover:underline">[Ver PDF]</a></div>`;
        });
      }
    })
    .catch(err => {
      resultadoDiv.innerHTML = "<span style='color:red'>Error de conexión al buscar. Revisa la URL del API y la configuración de CORS.</span>";
      console.error(err);
    });
});

// =================== LIMPIAR ===================
document.getElementById('limpiar-btn').addEventListener('click', () => {
  document.getElementById('buscar-input').value = '';
  document.getElementById('buscar-resultado').innerHTML = '';
});

// =================== SUBIR (Lógica actualizada para URLs Pre-firmadas) ===================
document.getElementById('subir-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const nombre = document.getElementById('nombre-doc').value.trim();
  const archivo = document.getElementById('archivo-doc').files[0];
  const codigos = document.getElementById('codigos-doc').value.trim();
  const mensajeDiv = document.getElementById('subir-mensaje');

  if (!archivo || !nombre) {
    mensajeDiv.textContent = "Nombre y archivo son obligatorios.";
    showModal({ title: 'Error', message: 'Nombre y archivo son obligatorios.', hideCancel: true });
    return;
  }

  mensajeDiv.textContent = "Preparando subida...";
  showModal({ title: 'Subiendo Documento', message: 'Generando URL segura para la subida...', hideCancel: true });

  try {
    // 1. Solicitar una URL pre-firmada al backend
    const presignedUrlRes = await fetch(`${API_BASE_URL}/api/presigned_url`, {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_name: archivo.name,
        file_type: archivo.type
      })
    });
    const presignedUrlData = await presignedUrlRes.json();

    if (!presignedUrlData.ok) {
      throw new Error(presignedUrlData.error || 'Error al obtener URL pre-firmada.');
    }

    const presignedUrl = presignedUrlData.presigned_url; // La URL pre-firmada para PUT directo
    const s3_key = presignedUrlData.s3_key; // La clave que usaremos para guardar en BD

    mensajeDiv.textContent = "Subiendo archivo directamente a S3...";
    showModal({ title: 'Subiendo Documento', message: 'Archivo subiéndose directamente al almacenamiento...', hideCancel: true });

    // 2. Subir el archivo directamente a S3 usando la URL pre-firmada (método PUT)
    const s3UploadRes = await fetch(presignedUrl, {
        method: 'PUT', // Usamos PUT
        headers: {
            'Content-Type': archivo.type // Es importante enviar el Content-Type correcto aquí
        },
        body: archivo, // Pasamos el objeto File directamente
    });

    if (!s3UploadRes.ok) {
      const s3ErrorText = await s3UploadRes.text();
      throw new Error(`Error al subir a S3: ${s3UploadRes.status} - ${s3ErrorText}`);
    }

    mensajeDiv.textContent = "Archivo subido a S3. Confirmando en base de datos...";
    showModal({ title: 'Subida exitosa a S3', message: 'Confirmando registro en base de datos...', hideCancel: true });

    // 3. Confirmar la subida con el backend y guardar metadatos en la BD
    const confirmRes = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        s3_key: s3_key, // La clave única del archivo en S3
        name: nombre,
        codigos: codigos
      })
    });
    const confirmData = await confirmRes.json();

    if (confirmData.ok) {
      mensajeDiv.textContent = "¡Documento subido y registrado!";
      document.getElementById('subir-form').reset();
      showModal({ title: '¡Subida completa!', message: confirmData.msg || 'El documento se subió y registró correctamente.', hideCancel: true });
      consultarDocs(); // Refrescar la lista de documentos
    } else {
      throw new Error(confirmData.error || 'Error al confirmar la subida en la BD.');
    }

  } catch (err) {
    mensajeDiv.textContent = `Error: ${err.message}`;
    showModal({ title: 'Error de Subida', message: err.message, hideCancel: true });
    console.error("Error completo en subida:", err);
  }
});


// =================== CONSULTAR ===================
function renderDocs(docs) {
  const lista = document.getElementById('consultar-lista');
  if (!docs || !docs.length) {
    lista.innerHTML = "<span>No hay documentos.</span>";
    return;
  }
  let html = '<table class="w-full text-left border-collapse">';
  html += '<thead><tr class="border-b border-gray-300 bg-gray-50"><th class="p-2">Nombre</th><th class="p-2">Acciones</th></tr></thead><tbody>';
  docs.forEach(doc => {
    const pdfUrl = `${API_BASE_URL}/static/uploads/${doc.path}`;
    html += `<tr class="border-b border-gray-200 hover:bg-gray-100">
      <td class="p-2">${doc.name}</td>
      <td class="p-2">
        <button class="mr-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700" onclick="eliminarDoc(${doc.id})">Eliminar</button>
        <button class="mr-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" onclick="editarDoc(${doc.id}, '${doc.name.replace(/'/g,"\\'")}')">Editar</button>
        <a href="${pdfUrl}" target="_blank" class="text-blue-600 underline">Ver PDF</a>
      </td>
    </tr>`;
  });
  html += '</tbody></table>';
  lista.innerHTML = html;
}

function consultarDocs(filtro = '') {
  fetch(`${API_BASE_URL}/api/docs` + (filtro ? '?search=' + encodeURIComponent(filtro) : ''))
    .then(res => res.json())
    .then(data => renderDocs(data.docs || []))
    .catch(err => {
      document.getElementById('consultar-lista').innerHTML = 'Error al cargar documentos.';
      console.error(err);
    });
}

document.getElementById('consultar-busqueda').addEventListener('input', function () {
  consultarDocs(this.value);
});

document.querySelector('.tab-btn[data-tab="consultar"]').addEventListener('click', function () {
  consultarDocs();
});

// ========== Eliminar documento ==========
window.eliminarDoc = function (id) {
  showModal({
    title: 'Confirmar eliminación',
    message: '¿Estás seguro que deseas eliminar este documento?',
    okText: 'Sí, eliminar',
    onOk: () => {
      fetch(`${API_BASE_URL}/api/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      })
      .then(res => res.json())
      .then(data => {
        if (data.ok) {
          consultarDocs();
          showModal({ title: 'Eliminado', message: 'El documento fue eliminado.', hideCancel: true });
        } else {
          showModal({ title: 'Error', message: data.msg || 'Error al eliminar.', hideCancel: true });
        }
      })
      .catch(err => {
        showModal({ title: 'Error', message: 'Error de conexión al eliminar.', hideCancel: true });
        console.error(err);
      });
    }
  });
};

// ========== Editar documento ==========
window.editarDoc = function (id, nombreActual) {
  const nuevoNombre = prompt('Nuevo nombre:', nombreActual);
  if (!nuevoNombre || nuevoNombre.trim() === '' || nuevoNombre === nombreActual) return;
  
  const nuevosCodigos = prompt('Nuevos códigos (separados por coma):', '');

  fetch(`${API_BASE_URL}/api/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: id, name: nuevoNombre, codigos: nuevosCodigos })
  })
  .then(res => res.json())
  .then(data => {
    if (data.ok) {
      consultarDocs();
      showModal({ title: 'Editado', message: 'El documento fue actualizado.', hideCancel: true });
    } else {
      showModal({ title: 'Error', message: data.msg || 'Error al editar.', hideCancel: true });
    }
  })
  .catch(err => {
    showModal({ title: 'Error', message: 'Error de conexión al editar.', hideCancel: true });
    console.error(err);
  });
};

// ========== Descargar CSV y ZIP (CORREGIDO) ==========
document.getElementById('descargar-csv').addEventListener('click', function () {
  window.open(`${API_BASE_URL}/api/export_csv`);
});

document.getElementById('descargar-pdfs').addEventListener('click', function () {
  showModal({
    title: 'Descargando ZIP...',
    message: 'Preparando el archivo ZIP con todos los documentos. Esto puede tardar un momento.',
    hideCancel: true
  });

  fetch(`${API_BASE_URL}/api/export_zip`, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archivos: [] })
  })
  .then(response => {
      if (!response.ok) throw new Error('Respuesta del servidor no fue OK');
      return response.blob();
  })
  .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'documentos.zip';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      document.getElementById('modal-overlay').classList.add('hidden');
  })
  .catch(err => {
      console.error('Error al descargar el ZIP:', err);
      showModal({
        title: 'Error de Descarga',
        message: 'No se pudo generar el archivo ZIP. Inténtalo de nuevo.',
        hideCancel: true
      });
  });
});

// =================== BÚSQUEDA POR CÓDIGO ===================
document.getElementById('codigo-form').addEventListener('submit', function (e) {
  e.preventDefault();
  const codigo = document.getElementById('codigo-input').value.trim();
  const resultado = document.getElementById('codigo-resultado');
  if (!codigo) return;
  resultado.textContent = 'Buscando código: ' + codigo + ' ...';

  fetch(`${API_BASE_URL}/api/suggest?q=` + encodeURIComponent(codigo))
    .then(res => res.json())
    .then(data => {
      resultado.innerHTML = '';
      if (!data.ok || !data.codes || !data.codes.length) {
        resultado.innerHTML = '<span>No se encontró el código.</span>';
      } else {
        resultado.innerHTML = `<strong>Resultados para "${codigo}":</strong><ul>`;
        data.codes.forEach(code => {
          resultado.innerHTML += `<li>${code}</li>`;
        });
        resultado.innerHTML += '</ul>';
      }
    })
    .catch(err => {
      resultado.innerHTML = "<span style='color:red'>Error en búsqueda por código.</span>";
      console.error(err);
    });
});

document.getElementById('codigo-input').addEventListener('input', function () {
  const val = this.value.trim();
  const sugerencias = document.getElementById('codigo-sugerencias');
  if (!val) {
    sugerencias.innerHTML = '';
    return;
  }
  
  fetch(`${API_BASE_URL}/api/suggest?q=` + encodeURIComponent(val))
    .then(res => res.json())
    .then(data => {
      sugerencias.innerHTML = '';
      if (data.ok && data.codes) {
        data.codes.forEach(codigo => {
          const li = document.createElement('li');
          li.className = 'p-2 cursor-pointer hover:bg-gray-100';
          li.textContent = codigo;
          li.onclick = () => {
            document.getElementById('codigo-input').value = codigo;
            sugerencias.innerHTML = '';
            document.getElementById('codigo-form').dispatchEvent(new Event('submit'));
          };
          sugerencias.appendChild(li);
        });
      }
    })
    .catch(() => {
      sugerencias.innerHTML = '';
    });
});