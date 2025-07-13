vz// =================== Sistema de Pestañas ===================
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
  console.log("Frontend listo. Sistema de pestañas OK.");
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

  fetch('https://nuevo-gestor-doc.onrender.com/api/search', {
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
          resultadoDiv.innerHTML += `<div><b>${doc.name}</b> (${doc.date}): ${doc.codigos_extraidos}</div>`;
        });
      }
    })
    .catch(err => {
      resultadoDiv.innerHTML = "<span style='color:red'>Error al buscar.</span>";
      console.error(err);
    });
});

// =================== LIMPIAR ===================
document.getElementById('limpiar-btn').addEventListener('click', () => {
  document.getElementById('buscar-input').value = '';
  document.getElementById('buscar-resultado').innerHTML = '';
});

// =================== SUBIR ===================
document.getElementById('subir-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const nombre = document.getElementById('nombre-doc').value.trim();
  const fecha = document.getElementById('fecha-doc').value;
  const archivo = document.getElementById('archivo-doc').files[0];
  const codigos = document.getElementById('codigos-doc').value.trim();
  const mensajeDiv = document.getElementById('subir-mensaje');

  if (!archivo) {
    mensajeDiv.textContent = "Selecciona un archivo PDF.";
    return;
  }

  if (!nombre) {
    mensajeDiv.textContent = "Debes ingresar un nombre.";
    return;
  }

  const formData = new FormData();
  formData.append('file', archivo);     // <--- Flask espera 'file'
  formData.append('name', nombre);      // <--- Flask espera 'name'
  formData.append('codigos', codigos);  // <--- Flask espera 'codigos'
  // formData.append('fecha', fecha);   // Si tu backend lo requiere

  mensajeDiv.textContent = "Subiendo...";

  fetch('https://nuevo-gestor-doc.onrender.com/api/upload', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        mensajeDiv.textContent = "¡Documento subido!";
        document.getElementById('subir-form').reset();
        showModal({
          title: '¡Subida exitosa!',
          message: 'El documento se subió correctamente.',
          hideCancel: true
        });
      } else {
        mensajeDiv.textContent = data.error || "Error al subir.";
        showModal({
          title: 'Error',
          message: data.error || "Error al subir.",
          hideCancel: true
        });
      }
    })
    .catch(err => {
      mensajeDiv.textContent = "Error al subir.";
      showModal({
        title: 'Error',
        message: "Error al subir.",
        hideCancel: true
      });
      console.error(err);
    });
});

// =================== CONSULTAR ===================
function renderDocs(docs) {
  const lista = document.getElementById('consultar-lista');
  if (!docs || !docs.length) {
    lista.innerHTML = "<span>No hay documentos.</span>";
    return;
  }
  let html = '<table class="w-full text-left border-collapse">';
  html +=
    '<thead><tr class="border-b border-gray-300 bg-gray-50"><th class="p-2">Nombre</th><th class="p-2">Acciones</th></tr></thead><tbody>';
  docs.forEach(doc => {
    html += `<tr class="border-b border-gray-200 hover:bg-gray-100">
      <td class="p-2">${doc.name}</td>
      <td class="p-2">
        <button class="mr-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700" onclick="eliminarDoc(${doc.id})">Eliminar</button>
        <button class="mr-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" onclick="editarDoc(${doc.id}, '${doc.name.replace(/'/g,"\\'")}')">Editar</button>
        <a href="https://nuevo-gestor-doc.onrender.com/static/uploads/${doc.path}" target="_blank" class="text-blue-600 underline">Ver PDF</a>
      </td>
    </tr>`;
  });
  html += '</tbody></table>';
  lista.innerHTML = html;
}

function consultarDocs(filtro = '') {
  fetch('https://nuevo-gestor-doc.onrender.com/api/docs' + (filtro ? '?search=' + encodeURIComponent(filtro) : ''))
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
    cancelText: 'Cancelar',
    onOk: () => {
      fetch('https://nuevo-gestor-doc.onrender.com/api/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      })
        .then(res => res.json())
        .then(data => {
          if (data.ok) {
            consultarDocs();
            showModal({
              title: 'Eliminado',
              message: 'El documento fue eliminado correctamente.',
              hideCancel: true
            });
          } else {
            showModal({
              title: 'Error',
              message: data.msg || 'Error al eliminar.',
              hideCancel: true
            });
          }
        })
        .catch(err => {
          showModal({
            title: 'Error',
            message: 'Error al eliminar.',
            hideCancel: true
          });
          console.error(err);
        });
    }
  });
};

// ========== Editar documento ==========
window.editarDoc = function (id, nombreActual) {
  const nuevoNombre = prompt('Nuevo nombre:', nombreActual);
  if (!nuevoNombre || nuevoNombre === nombreActual) return;
  fetch('https://nuevo-gestor-doc.onrender.com/api/edit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, name: nuevoNombre })
  })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        consultarDocs();
        showModal({
          title: 'Editado',
          message: 'El documento fue editado correctamente.',
          hideCancel: true
        });
      } else {
        showModal({
          title: 'Error',
          message: data.msg || 'Error al editar.',
          hideCancel: true
        });
      }
    })
    .catch(err => {
      showModal({
        title: 'Error',
        message: 'Error al editar.',
        hideCancel: true
      });
      console.error(err);
    });
};

// ========== Descargar CSV y ZIP ==========
document.getElementById('descargar-csv').addEventListener('click', function () {
  window.open('https://nuevo-gestor-doc.onrender.com/api/export_csv');
});
document.getElementById('descargar-pdfs').addEventListener('click', function () {
  window.open('https://nuevo-gestor-doc.onrender.com/api/export_zip');
});

// =================== BÚSQUEDA POR CÓDIGO ===================
document.getElementById('codigo-form').addEventListener('submit', function (e) {
  e.preventDefault();
  const codigo = document.getElementById('codigo-input').value.trim();
  const resultado = document.getElementById('codigo-resultado');
  resultado.textContent = 'Buscando código: ' + codigo + ' ...';

  fetch('https://nuevo-gestor-doc.onrender.com/api/suggest?q=' + encodeURIComponent(codigo))
    .then(res => res.json())
    .then(data => {
      resultado.innerHTML = '';
      if (!data.ok || !data.codes || !data.codes.length) {
        resultado.innerHTML = '<span>No se encontró el código.</span>';
      } else {
        data.codes.forEach(code => {
          resultado.innerHTML += `<div><b>${code}</b></div>`;
        });
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
  sugerencias.innerHTML = '';
  if (!val) return;
  fetch('https://nuevo-gestor-doc.onrender.com/api/suggest?q=' + encodeURIComponent(val))
    .then(res => res.json())
    .then(data => {
      sugerencias.innerHTML = '';
      if (data.ok && data.codes) {
        data.codes.forEach(codigo => {
          const li = document.createElement('li');
          li.textContent = codigo;
          li.onclick = () => {
            document.getElementById('codigo-input').value = codigo;
            sugerencias.innerHTML = '';
          };
          sugerencias.appendChild(li);
        });
      }s
    })
    .catch(() => {
      sugerencias.innerHTML = '';
    });
});

console.log('Gestor documental JS conectado y funcional.');
s