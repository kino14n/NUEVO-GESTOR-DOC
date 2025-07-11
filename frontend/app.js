
const API = '/api/documentos';
let editingId = null;

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('searchBox').addEventListener('input', async function(e) {
    const val = e.target.value.trim();
    if (!val) {
      document.getElementById('suggestions').classList.add('hidden');
      return;
    }
    const resp = await fetch(API + '/suggest', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({codigo: val})
    });
    const codigos = await resp.json();
    mostrarSugerencias(codigos);
  });
  buscar();
});

function mostrarSugerencias(codigos) {
  const ul = document.getElementById('suggestions');
  ul.innerHTML = '';
  if (codigos.length === 0) {
    ul.classList.add('hidden');
    return;
  }
  codigos.forEach(codigo => {
    const li = document.createElement('li');
    li.textContent = codigo;
    li.className = "px-4 py-2 cursor-pointer hover:bg-blue-100";
    li.onclick = () => {
      document.getElementById('searchBox').value = codigo;
      ul.classList.add('hidden');
    };
    ul.appendChild(li);
  });
  ul.classList.remove('hidden');
}

async function buscar() {
  const query = document.getElementById('searchBox').value.trim();
  const resp = await fetch(API + '/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query})
  });
  const docs = await resp.json();
  renderResultados(docs);
}

function renderResultados(docs) {
  const tb = document.getElementById('resultados');
  tb.innerHTML = '';
  docs.forEach(doc => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="border px-4 py-2">${doc.codigo}</td>
      <td class="border px-4 py-2">${doc.nombre}</td>
      <td class="border px-4 py-2">${doc.descripcion || ''}</td>
      <td class="border px-4 py-2">${doc.fecha || ''}</td>
      <td class="border px-4 py-2">${doc.ruta_pdf ? `<a href="${doc.ruta_pdf}" target="_blank" class="text-blue-600 underline">Ver</a>` : ''}</td>
      <td class="border px-4 py-2 flex gap-2">
        <button class="bg-yellow-400 px-2 py-1 rounded" onclick='editarDoc(${JSON.stringify(doc)})'>Editar</button>
        <button class="bg-red-500 text-white px-2 py-1 rounded" onclick='eliminarDoc(${doc.id})'>Eliminar</button>
      </td>
    `;
    tb.appendChild(tr);
  });
}

function abrirModalAgregar() {
  editingId = null;
  document.getElementById('modalTitle').textContent = "Agregar Documento";
  document.getElementById('formDoc').reset();
  document.getElementById('archivoActual').textContent = "";
  document.getElementById('modal').classList.remove('hidden');
}
function cerrarModal() {
  document.getElementById('modal').classList.add('hidden');
}
function editarDoc(doc) {
  editingId = doc.id;
  document.getElementById('modalTitle').textContent = "Editar Documento";
  document.getElementById('docId').value = doc.id;
  document.getElementById('codigo').value = doc.codigo;
  document.getElementById('nombre').value = doc.nombre;
  document.getElementById('descripcion').value = doc.descripcion || '';
  document.getElementById('fecha').value = doc.fecha || '';
  document.getElementById('archivoActual').textContent = doc.ruta_pdf ? "Archivo actual: " + doc.ruta_pdf : "";
  document.getElementById('modal').classList.remove('hidden');
}

async function guardarDoc(e) {
  e.preventDefault();
  const codigo = document.getElementById('codigo').value.trim();
  const nombre = document.getElementById('nombre').value.trim();
  const descripcion = document.getElementById('descripcion').value.trim();
  const fecha = document.getElementById('fecha').value;
  const pdf = document.getElementById('pdf').files[0];

  let ruta_pdf = "";
  if (pdf) {
    const formData = new FormData();
    formData.append('file', pdf);
    const resp = await fetch(API + '/upload', {
      method: 'POST',
      body: formData
    });
    const data = await resp.json();
    if (data.success) {
      ruta_pdf = data.ruta;
    } else {
      toast('Error al subir PDF', true);
      return;
    }
  } else if (editingId) {
    ruta_pdf = document.getElementById('archivoActual').textContent.replace("Archivo actual: ", "");
  }

  const datos = {codigo, nombre, descripcion, fecha, ruta_pdf};
  let url = API + '/add';
  if (editingId) {
    url = API + `/edit/${editingId}`;
  }
  const resp = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(datos)
  });
  if ((await resp.json()).success) {
    toast('Guardado correctamente');
    cerrarModal();
    buscar();
  } else {
    toast('Error al guardar', true);
  }
}

async function eliminarDoc(id) {
  if (!confirm("¿Seguro de eliminar este documento?")) return;
  const resp = await fetch(API + `/delete/${id}`, {method: 'POST'});
  if ((await resp.json()).success) {
    toast('Eliminado correctamente');
    buscar();
  } else {
    toast('Error al eliminar', true);
  }
}

function toast(msg, error) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `fixed bottom-4 right-4 px-4 py-2 rounded shadow-lg ${error ? 'bg-red-500' : 'bg-green-500'} text-white`;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 2200);
}
