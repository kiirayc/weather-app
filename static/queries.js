function $(id) { 
  return document.getElementById(id); 
}

async function createQuery() {
  const btn = $('createBtn');
  const loc = $('loc')?.value.trim() || '';
  const sd  = $('sd')?.value || '';
  const ed  = $('ed')?.value || '';

  if (sd && ed && sd > ed) {
    if ($('createErr')) $('createErr').textContent = 'Start date must be before or equal to end date.';
    if ($('createMsg')) $('createMsg').innerHTML = '';
    if ($('createOut')) $('createOut').textContent = '';
    return;
  }

  if (btn) btn.disabled = true;

  const res = await fetch('/api/queries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ location: loc, start_date: sd, end_date: ed })
  });

  const body = await res.json().catch(() => null);
  if (btn) btn.disabled = false;

  if (!res.ok || !body || body.error) {
    const msg = (body && body.error) || 'Failed to create query.';
    if ($('createErr')) $('createErr').textContent = msg;
    if ($('createMsg')) $('createMsg').innerHTML = '';
    if ($('createOut')) $('createOut').textContent = '';
    return;
  }

  // Success paths
  if ($('createErr')) $('createErr').textContent = '';
  if ($('createMsg')) {
    $('createMsg').innerHTML = renderQuerySummary(body);
  } else if ($('createOut')) {
    $('createOut').textContent = `Created #${body.id} for ${body.location?.name || '—'} ${body.start_date} → ${body.end_date}`;
  } else {
    window.location.assign(`/queries/${body.id}/view`);
    return;
  }

  await loadQueries();
}

// Render the Saved Queries table (called after load + after updates)
async function loadQueries() {
  const res = await fetch("/api/queries");
  const queries = await res.json();
  const tbody = document.querySelector("#queriesTbl tbody");
  tbody.innerHTML = "";

  for (const q of queries) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${q.id}</td>
      <td>${q.location?.name || "—"}</td>
      <td>${q.start_date} → ${q.end_date}</td>
      <td>
        <button onclick="viewQuery(${q.id})">View</button>
        <button onclick="editQuery(${q.id})">Edit</button>
        <button onclick="deleteQuery(${q.id})">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

// Show edit form in detailPanel
async function editQuery(id) {
  const res = await fetch(`/api/queries/${id}`);
  if (!res.ok) {
    alert("Query not found");
    return;
  }
  const q = await res.json();

  document.getElementById("detailPanel").innerHTML = `
    <h4>Edit Query #${q.id}</h4>
    <form onsubmit="return false" style="display:flex; gap:.5rem; flex-wrap:wrap">
      <input id="editLoc" placeholder="Location" value="${q.location?.name || ''}" />
      <input id="editSd" type="date" value="${q.start_date}" />
      <input id="editEd" type="date" value="${q.end_date}" />
      <button onclick="updateQuery(${q.id})">Save</button>
    </form>
    <div id="updateMsg" style="margin-top:.5rem; color:green;"></div>
    <div id="updateErr" style="margin-top:.5rem; color:red;"></div>
  `;
}

// Call PUT /api/queries/:id
async function updateQuery(id) {
  const loc = document.getElementById("editLoc").value.trim();
  const sd = document.getElementById("editSd").value;
  const ed = document.getElementById("editEd").value;

  const payload = { location: loc, start_date: sd, end_date: ed };

  const res = await fetch(`/api/queries/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const msgBox = document.getElementById("updateMsg");
  const errBox = document.getElementById("updateErr");

  if (res.ok) {
    const data = await res.json();
    msgBox.textContent = "✅ Query updated successfully!";
    errBox.textContent = "";
    console.log("Updated query:", data);

    // Reload the queries table
    loadQueries();
  } else {
    const err = await res.json();
    errBox.textContent = err.error || "❌ Update failed";
    msgBox.textContent = "";
  }
}

// Delete query
async function deleteQuery(id) {
  if (!confirm("Delete this query?")) return;
  const res = await fetch(`/api/queries/${id}`, { method: "DELETE" });
  if (res.ok) {
    loadQueries();
  } else {
    alert("Failed to delete query.");
  }
}

async function viewQuery(id) {
  const res = await fetch('/api/queries/' + id);
  const data = await res.json();

  if (!res.ok) { 
    $('detailPanel').innerHTML = `<span style="color:#b91c1c">${data.error || 'Failed to load.'}</span>`; 
    return; 
  }

  renderQueryDetail(data);
}

document.addEventListener('DOMContentLoaded', loadQueries);
