(() => {
  "use strict";
  const config = window.ROUTEWISE_CONFIG || { apiBaseUrl: "" };
  const API = String(config.apiBaseUrl || "").replace(/\/$/, "");
  const state = { deliveries: [], dashboard: null, overviewMap: null, routeMap: null, overviewLayer: null, routeLayer: null, routeLine: null, routeDepot: null, selectedProofId: null, reportRows: [] };
  const $ = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const labelStatus = (status) => ({ pending: "Pending", in_transit: "In transit", completed: "Completed", delayed: "Delayed" }[status] || status);
  const fmtDate = (value, withTime = false) => {
    if (!value) return "—";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "—";
    return new Intl.DateTimeFormat(undefined, withTime ? { dateStyle: "medium", timeStyle: "short" } : { month: "short", day: "numeric", year: "numeric" }).format(d);
  };
  const fmtDateTimeLocal = (value) => {
    const d = new Date(value); if (Number.isNaN(d.getTime())) return "";
    const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 16);
  };
  async function api(path, options = {}) {
    let response;
    try {
      response = await fetch(`${API}/api${path}`, { ...options, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) } });
    } catch (e) { throw new Error("Cannot reach the RouteWise API. Check the backend URL, that the service is running, and its CORS settings."); }
    if (response.status === 204) return null;
    let body;
    try { body = await response.json(); }
    catch (_) { throw new Error("The server returned a non-JSON response. Check that the API base URL points to the RouteWise backend."); }
    if (!response.ok) {
      let detail = body.detail;
      if (Array.isArray(detail)) detail = detail.map((x) => `${(x.loc || []).slice(-1)[0] || "Field"}: ${x.msg}`).join(" · ");
      throw new Error(detail || `Request failed (${response.status})`);
    }
    return body;
  }
  function toast(message, type = "success") {
    const el = document.createElement("div"); el.className = `toast${type === "error" ? " error" : ""}`; el.textContent = message;
    $("toastRegion").append(el); window.setTimeout(() => el.remove(), 4300);
  }
  function setConnection(ok, detail = "") {
    $("connectionDot").className = `connection-dot ${ok ? "ok" : "bad"}`;
    $("connectionText").textContent = ok ? "API connected" : "API unavailable";
    $("connectionHint").textContent = detail || (ok ? "Live delivery data" : "Check backend setup");
  }
  function setError(message) { const el = $("apiError"); el.textContent = message; el.classList.toggle("hidden", !message); }
  function statusBadge(status) { return `<span class="badge badge-${escapeHtml(status)}">${escapeHtml(labelStatus(status))}</span>`; }
  function priorityLabel(priority) { return `<span class="priority priority-${escapeHtml(priority)}">${escapeHtml(priority)}</span>`; }
  function renderStats() {
    const d = state.dashboard || { total: 0, pending: 0, in_transit: 0, completed: 0, delayed: 0, overdue: 0, high_priority: 0, completion_percent: 0 };
    $("statTotal").textContent = d.total; $("statPending").textContent = d.pending; $("statTransit").textContent = d.in_transit;
    $("statCompleted").textContent = d.completed; $("statDelayed").textContent = d.delayed; $("statHighPriority").textContent = d.high_priority;
    $("completionRate").textContent = `${d.completion_percent}%`;
    $("statUrgent").textContent = `${d.high_priority} active orders`; $("statOverdue").textContent = `${d.overdue} overdue`;
  }
  function renderRecent() {
    const rows = [...state.deliveries].sort((a, b) => new Date(a.deadline) - new Date(b.deadline)).slice(0, 6);
    $("recentRows").innerHTML = rows.length ? rows.map((d) => `<tr><td><div class="order-cell"><b>${escapeHtml(d.order_id)}</b><small>${escapeHtml(d.customer_name)}</small></div></td><td class="address-cell" title="${escapeHtml(d.address)}">${escapeHtml(d.address)}</td><td>${escapeHtml(fmtDate(d.deadline, true))}</td><td>${priorityLabel(d.priority)}</td><td>${statusBadge(d.status)}</td></tr>`).join("") : `<tr><td colspan="5" class="table-empty">${state.dashboard ? "No deliveries yet. Add a delivery to get started." : "Connect the backend to load delivery records."}</td></tr>`;
  }
  function renderInsights() {
    const now = Date.now();
    const open = state.deliveries.filter((d) => d.status !== "completed").map((d) => ({ ...d, overdue: new Date(d.deadline).getTime() < now }));
    const ranked = open.filter((d) => d.overdue || ["urgent", "high"].includes(d.priority)).sort((a, b) => Number(b.overdue) - Number(a.overdue) || ({ urgent: 0, high: 1, normal: 2, low: 3 }[a.priority] - { urgent: 0, high: 1, normal: 2, low: 3 }[b.priority]) || new Date(a.deadline) - new Date(b.deadline)).slice(0, 4);
    $("insightsList").innerHTML = ranked.length ? ranked.map((d) => {
      const reason = d.overdue ? `Deadline passed ${fmtDate(d.deadline, true)}; not marked completed.` : `${d.priority[0].toUpperCase() + d.priority.slice(1)} priority; deadline ${fmtDate(d.deadline, true)}.`;
      return `<div class="insight-item"><span class="insight-marker ${d.overdue ? "red" : ""}"></span><div><b>${escapeHtml(d.order_id)} · ${escapeHtml(d.customer_name)}</b><small>${escapeHtml(reason)} Prioritize for dispatch review.</small></div></div>`;
    }).join("") : `<div class="empty-inline">${state.deliveries.length ? "No overdue or high-priority open orders. Keep monitoring deadlines." : "Add deliveries to see operational recommendations."}</div>`;
  }
  function createMap(id) {
    if (!window.L || !$(id)) return null;
    const map = L.map(id, { scrollWheelZoom: false, zoomControl: true }).setView([39.5, -98.35], 4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
    return map;
  }
  function markerColor(status) { return ({ pending: "#4e7ee0", in_transit: "#e49b33", completed: "#28a078", delayed: "#cb5a52" })[status] || "#4e7ee0"; }
  function renderOverviewMap() {
    if (!state.overviewMap || !window.L) return;
    if (state.overviewLayer) state.overviewMap.removeLayer(state.overviewLayer);
    state.overviewLayer = L.featureGroup();
    state.deliveries.forEach((d) => {
      const marker = L.circleMarker([d.latitude, d.longitude], { radius: 7, color: "#fff", weight: 2, fillColor: markerColor(d.status), fillOpacity: .95 });
      marker.bindPopup(`<b>${escapeHtml(d.order_id)}</b><br>${escapeHtml(d.customer_name)}<br>${escapeHtml(labelStatus(d.status))}`); marker.addTo(state.overviewLayer);
    });
    state.overviewLayer.addTo(state.overviewMap);
    if (state.deliveries.length) state.overviewMap.fitBounds(state.overviewLayer.getBounds().pad(.15), { maxZoom: 12 });
  }
  function renderDeliveries() {
    const query = $("deliverySearch").value.trim().toLowerCase(); const status = $("statusFilter").value; const priority = $("priorityFilter").value;
    const rows = state.deliveries.filter((d) => (!status || d.status === status) && (!priority || d.priority === priority) && (!query || `${d.order_id} ${d.customer_name} ${d.address}`.toLowerCase().includes(query)));
    $("deliveryRows").innerHTML = rows.length ? rows.map((d) => `<tr><td><div class="order-cell"><b>${escapeHtml(d.order_id)}</b><small>${escapeHtml(d.customer_name)}</small></div></td><td class="address-cell" title="${escapeHtml(d.address)}">${escapeHtml(d.address)}</td><td>${escapeHtml(fmtDate(d.deadline, true))}</td><td>${priorityLabel(d.priority)}</td><td><label class="sr-only" for="status-${escapeHtml(d.id)}">Status for ${escapeHtml(d.order_id)}</label><select class="status-select" id="status-${escapeHtml(d.id)}" data-status-id="${escapeHtml(d.id)}"><option value="pending" ${d.status === "pending" ? "selected" : ""}>Pending</option><option value="in_transit" ${d.status === "in_transit" ? "selected" : ""}>In transit</option><option value="completed" ${d.status === "completed" ? "selected" : ""}>Completed</option><option value="delayed" ${d.status === "delayed" ? "selected" : ""}>Delayed</option></select></td><td><button class="row-action" data-proof-id="${escapeHtml(d.id)}" title="Upload proof of delivery" aria-label="Upload proof for ${escapeHtml(d.order_id)}">⇧</button><button class="row-action" data-history-id="${escapeHtml(d.id)}" title="View delivery history" aria-label="History for ${escapeHtml(d.order_id)}">◷</button></td><td><div class="row-actions"><button class="row-action" data-edit-id="${escapeHtml(d.id)}" title="Edit" aria-label="Edit ${escapeHtml(d.order_id)}">✎</button><button class="row-action" data-delete-id="${escapeHtml(d.id)}" title="Delete" aria-label="Delete ${escapeHtml(d.order_id)}">×</button></div></td></tr>`).join("") : `<tr><td colspan="7" class="table-empty">${state.deliveries.length ? "No records match these filters." : "No deliveries yet. Add a real order to get started."}</td></tr>`;
    $("deliveryCount").textContent = `Showing ${rows.length} of ${state.deliveries.length} delivery records`;
  }
  function renderRouteStops() {
    const candidates = state.deliveries.filter((d) => d.status !== "completed");
    $("routeStops").innerHTML = candidates.length ? candidates.map((d) => `<label class="route-stop"><input type="checkbox" class="route-checkbox" value="${escapeHtml(d.id)}"><span><b>${escapeHtml(d.order_id)} · ${escapeHtml(d.customer_name)}</b><small>${escapeHtml(d.address)} · ${escapeHtml(d.priority)} priority</small></span></label>`).join("") : `<div class="empty-inline">No active deliveries available for routing.</div>`;
    updateRouteSelectCount(); renderRouteLocationMap();
  }
  function updateRouteSelectCount() { const count = document.querySelectorAll(".route-checkbox:checked").length; $("routeSelectCount").textContent = `${count} selected`; }
  function renderRouteLocationMap() {
    if (!state.routeMap || !window.L) return;
    if (state.routeLayer) state.routeMap.removeLayer(state.routeLayer);
    state.routeLayer = L.featureGroup();
    const chosen = [...document.querySelectorAll(".route-checkbox:checked")].map((el) => state.deliveries.find((d) => d.id === el.value)).filter(Boolean);
    chosen.forEach((d) => L.circleMarker([d.latitude,d.longitude], { radius: 7, color: "#fff", weight: 2, fillColor: markerColor(d.status), fillOpacity: .95 }).bindPopup(`<b>${escapeHtml(d.order_id)}</b><br>${escapeHtml(d.customer_name)}`).addTo(state.routeLayer));
    const lat=Number($("depotLat").value), lon=Number($("depotLon").value);
    if ($("depotLat").value !== "" && $("depotLon").value !== "" && Number.isFinite(lat) && Number.isFinite(lon)) L.marker([lat,lon]).bindPopup(`<b>${escapeHtml($("depotLabel").value || "Depot")}</b>`).addTo(state.routeLayer);
    state.routeLayer.addTo(state.routeMap);
    if (chosen.length) state.routeMap.fitBounds(state.routeLayer.getBounds().pad(.15), { maxZoom: 12 });
    else if (lat || lon) state.routeMap.setView([lat,lon], 10);
  }
  function clearRouteMetrics() { $("routeMetrics").classList.add("hidden"); $("estimateChip").classList.add("hidden"); if (state.routeLine) { state.routeMap?.removeLayer(state.routeLine); state.routeLine=null; } }
  function fmtDistance(m) { return m >= 1000 ? `${(m/1000).toFixed(1)} km` : `${Math.round(m)} m`; }
  function fmtDuration(sec) { const mins=Math.round(sec/60); return mins >= 60 ? `${Math.floor(mins/60)} hr ${mins%60} min` : `${mins} min`; }
  async function optimizeRoute() {
    const ids=[...document.querySelectorAll(".route-checkbox:checked")].map((el)=>el.value);
    const lat=Number($("depotLat").value), lon=Number($("depotLon").value);
    if (!ids.length) { $("routeMessage").textContent="Select at least one delivery stop."; $("routeMessage").classList.remove("hidden","success"); return; }
    if ($("depotLat").value==="" || $("depotLon").value==="" || !Number.isFinite(lat)||lat < -90||lat>90||!Number.isFinite(lon)||lon < -180||lon>180) { $("routeMessage").textContent="Enter a valid depot latitude (−90 to 90) and longitude (−180 to 180)."; $("routeMessage").classList.remove("hidden","success"); return; }
    const button=$("optimizeRoute"); button.disabled=true; button.textContent="Requesting route…"; $("routeMessage").classList.add("hidden"); clearRouteMetrics();
    try {
      const result=await api("/routes/optimize", { method:"POST", body:JSON.stringify({depot:{latitude:lat,longitude:lon,label:$ ("depotLabel").value.trim()||"Depot"},delivery_ids:ids}) });
      $("routeDistance").textContent=fmtDistance(result.distance_meters); $("routeDuration").textContent=fmtDuration(result.duration_seconds); $("routeStopsTotal").textContent=result.stop_count;
      $("routeMetrics").classList.remove("hidden"); $("estimateChip").classList.remove("hidden");
      const ordered=(result.ordered_stops||[]).filter((x)=>x.type==="delivery").map((x,i)=>`${i+1}. ${x.order_id}`);
      $("routeMapCaption").textContent=`${result.service} · ${ordered.join(" → ")}`;
      if (result.geometry && result.geometry.coordinates && state.routeMap && window.L) {
        const latlngs=result.geometry.coordinates.map(([x,y])=>[y,x]); state.routeLine=L.polyline(latlngs,{color:"#2864db",weight:5,opacity:.8}).addTo(state.routeMap); state.routeMap.fitBounds(state.routeLine.getBounds().pad(.12));
      }
      $("routeMessage").textContent=result.disclaimer; $("routeMessage").classList.remove("hidden"); $("routeMessage").classList.add("success");
    } catch(e) { $("routeMessage").textContent=`Route unavailable: ${e.message}. No distance or travel-time estimate is shown.`; $("routeMessage").classList.remove("hidden","success"); $("routeMapCaption").textContent="Route service did not return a route"; }
    finally { button.disabled=false; button.innerHTML="⌁ Optimize selected route"; }
  }
  async function loadCore() {
    try {
      const [dashboard, deliveries]=await Promise.all([api("/dashboard"),api("/deliveries")]);
      if (!dashboard || typeof dashboard !== "object" || Array.isArray(dashboard) || !Array.isArray(deliveries)) throw new Error("The backend returned an unexpected data format. Check the API base URL and backend version.");
      state.dashboard=dashboard; state.deliveries=deliveries; setConnection(true); setError(""); renderStats(); renderRecent(); renderInsights(); renderDeliveries(); renderRouteStops(); renderOverviewMap();
    } catch(e) { setConnection(false); setError(`${e.message} The dashboard is empty until it can load real records. Start and configure the backend. No sample orders are loaded into this app.`); $("recentRows").innerHTML=`<tr><td colspan="5" class="table-empty">Backend connection required to load records.</td></tr>`; $("deliveryRows").innerHTML=`<tr><td colspan="7" class="table-empty">Backend connection required to load records.</td></tr>`; $("deliveryCount").textContent="No backend data loaded"; renderRouteStops(); }
  }
  function showPage(page) {
    document.querySelectorAll(".page").forEach((p)=>p.classList.toggle("active",p.id===`page-${page}`));
    document.querySelectorAll(".nav-link").forEach((n)=>n.classList.toggle("active",n.dataset.page===page));
    const title={dashboard:"Overview",deliveries:"Deliveries",routes:"Route planner",reports:"Reports"}[page]||"Overview"; $("pageTitle").textContent=title;
    history.replaceState(null,"",`#${page}`); $("sidebar").classList.remove("open"); $("mobileMenu").setAttribute("aria-expanded","false");
    if(page==="reports") loadReportRows();
    window.setTimeout(()=>{state.overviewMap?.invalidateSize();state.routeMap?.invalidateSize();},60);
  }
  function openNewDelivery() {
    $("deliveryForm").reset(); $("deliveryId").value=""; $("formTitle").textContent="Add a delivery"; $("saveDelivery").textContent="Save delivery"; $("formError").classList.add("hidden"); $("deliveryDialog").showModal();
  }
  function openEditDelivery(id) {
    const d=state.deliveries.find((x)=>x.id===id); if(!d)return;
    $("deliveryId").value=d.id; $("orderId").value=d.order_id; $("customerName").value=d.customer_name; $("address").value=d.address; $("latitude").value=d.latitude; $("longitude").value=d.longitude; $("priority").value=d.priority; $("deadline").value=fmtDateTimeLocal(d.deadline); $("deliveryStatus").value=d.status;
    $("formTitle").textContent=`Edit ${d.order_id}`; $("saveDelivery").textContent="Save changes"; $("formError").classList.add("hidden"); $("deliveryDialog").showModal();
  }
  async function saveDelivery(event) {
    event.preventDefault(); const form=$("deliveryForm"), err=$("formError"); err.classList.add("hidden");
    if(!form.reportValidity())return;
    const deadlineValue=$("deadline").value;
    const payload={order_id:$("orderId").value.trim(),customer_name:$("customerName").value.trim(),address:$("address").value.trim(),latitude:Number($("latitude").value),longitude:Number($("longitude").value),priority:$("priority").value,deadline:new Date(deadlineValue).toISOString(),status:$("deliveryStatus").value};
    const id=$("deliveryId").value, btn=$("saveDelivery"); btn.disabled=true;
    try { await api(id?`/deliveries/${encodeURIComponent(id)}`:"/deliveries",{method:id?"PATCH":"POST",body:JSON.stringify(payload)}); $("deliveryDialog").close(); toast(id?"Delivery updated":"Delivery added"); await loadCore(); }
    catch(e){err.textContent=e.message;err.classList.remove("hidden");}
    finally{btn.disabled=false;}
  }
  async function setStatus(id,status) {
    try { await api(`/deliveries/${encodeURIComponent(id)}/status`,{method:"PATCH",body:JSON.stringify({status})}); toast("Delivery status updated"); await loadCore(); }
    catch(e){toast(`Could not update status: ${e.message}`,"error");await loadCore();}
  }
  async function deleteDelivery(id) {
    const d=state.deliveries.find((x)=>x.id===id); if(!d||!window.confirm(`Delete delivery ${d.order_id}? Its history will also be deleted.`))return;
    try{await api(`/deliveries/${encodeURIComponent(id)}`,{method:"DELETE"});toast("Delivery deleted");await loadCore();}catch(e){toast(`Could not delete delivery: ${e.message}`,"error");}
  }
  async function geocode() {
    const q=$("address").value.trim(); if(q.length<4){toast("Enter a full delivery address first.","error");return;}
    const btn=$("geocodeButton");btn.disabled=true;btn.textContent="Searching…";
    try{const r=await api(`/geocode?q=${encodeURIComponent(q)}`);$("latitude").value=r.latitude;$("longitude").value=r.longitude;$("address").value=r.display_name;toast("Coordinates found with OpenStreetMap");}
    catch(e){toast(e.message,"error");}finally{btn.disabled=false;btn.textContent="Find coordinates";}
  }
  async function showHistory(id) {
    const d=state.deliveries.find((x)=>x.id===id);$("historyTitle").textContent=`History · ${d?.order_id||"Delivery"}`;$("historyBody").innerHTML="<div class='empty-inline'>Loading delivery history…</div>";$("historyDialog").showModal();
    try{const items=await api(`/deliveries/${encodeURIComponent(id)}/history`);$("historyBody").innerHTML=items.length?items.map((item)=>{if(item.event_type==="proof"){let p={};try{p=JSON.parse(item.new_value)}catch(_){}return `<div class="history-entry"><i class="history-bullet"></i><div><b>Proof of delivery uploaded</b><small>${escapeHtml(fmtDate(item.created_at,true))}</small>${p.secure_url?`<a href="${escapeHtml(p.secure_url)}" target="_blank" rel="noopener"><img class="history-image" src="${escapeHtml(p.secure_url)}" alt="Proof of delivery" loading="lazy"></a>`:""}</div></div>`;}return `<div class="history-entry"><i class="history-bullet"></i><div><b>${item.old_value?`${escapeHtml(labelStatus(item.old_value))} → `:"Created as "}${escapeHtml(labelStatus(item.new_value))}</b><small>${escapeHtml(fmtDate(item.created_at,true))}</small></div></div>`}).join(""):`<div class="empty-inline">No history recorded.</div>`;}catch(e){$("historyBody").innerHTML=`<div class="form-error">${escapeHtml(e.message)}</div>`;}
  }
  async function uploadProof(file) {
    if(!file)return;
    const id=state.selectedProofId;state.selectedProofId=null;
    const allowed=["image/jpeg","image/png","image/webp"];
    if(!allowed.includes(file.type)){toast("Use a JPEG, PNG, or WebP image.","error");return;}
    try{
      const signature=await api("/uploads/signature");
      if(file.size>signature.max_bytes){toast(`Image is too large. Maximum allowed size is ${(signature.max_bytes/1024/1024).toFixed(0)} MB.`,"error");return;}
      const form=new FormData();form.append("file",file);form.append("api_key",signature.api_key);form.append("timestamp",String(signature.timestamp));form.append("folder",signature.folder);form.append("upload_preset",signature.upload_preset);form.append("signature",signature.signature);
      const response=await fetch(`https://api.cloudinary.com/v1_1/${encodeURIComponent(signature.cloud_name)}/image/upload`,{method:"POST",body:form});
      let uploaded={};try{uploaded=await response.json()}catch(_){}
      if(!response.ok)throw new Error(uploaded.error?.message||`Cloudinary upload failed (${response.status})`);
      await api(`/deliveries/${encodeURIComponent(id)}/proof`,{method:"POST",body:JSON.stringify({secure_url:uploaded.secure_url,public_id:uploaded.public_id})});
      toast("Proof uploaded and attached to delivery history.");if($("historyDialog").open)await showHistory(id);
    }catch(e){toast(`Proof upload failed: ${e.message}`,"error");}
    finally{$("proofInput").value="";}
  }
  function csvCell(value) { let s=String(value??"");if(/^[=+\-@\t\r]/.test(s))s="'"+s;return `"${s.replace(/"/g,'""')}"`; }
  function exportCsv() {
    const records=state.reportRows;if(!records.length){toast("There are no filtered delivery records to export.","error");return;}
    const columns=["order_id","customer_name","address","latitude","longitude","priority","deadline","status","created_at","updated_at"];
    const lines=[columns.join(","),...records.map((r)=>columns.map((c)=>csvCell(r[c])).join(","))];const blob=new Blob(["\ufeff"+lines.join("\r\n")],{type:"text/csv;charset=utf-8"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`routewise-deliveries-${new Date().toISOString().slice(0,10)}.csv`;a.click();URL.revokeObjectURL(a.href);
  }
  async function loadReportRows() {
    const params=new URLSearchParams();const from=$("reportFrom").value,to=$("reportTo").value,status=$("reportStatus").value,priority=$("reportPriority").value;
    if(from)params.set("from_date",from);if(to)params.set("to_date",to);if(status)params.set("status",status);if(priority)params.set("priority",priority);
    const query=params.toString();$("reportRows").innerHTML=`<tr><td colspan="5" class="table-empty">Loading records…</td></tr>`;
    try{state.reportRows=await api(`/deliveries${query?`?${query}`:""}`);if(!Array.isArray(state.reportRows))throw new Error("The backend returned an unexpected report format.");$("reportRows").innerHTML=state.reportRows.length?state.reportRows.map((d)=>`<tr><td>${escapeHtml(d.order_id)}</td><td>${escapeHtml(d.customer_name)}</td><td>${escapeHtml(fmtDate(d.deadline,true))}</td><td>${priorityLabel(d.priority)}</td><td>${statusBadge(d.status)}</td></tr>`).join(""):`<tr><td colspan="5" class="table-empty">No records match these report filters.</td></tr>`;$("reportSummary").textContent=`${state.reportRows.length} matching deadline record${state.reportRows.length===1?"":"s"}`;}
    catch(e){state.reportRows=[];$("reportRows").innerHTML=`<tr><td colspan="5" class="table-empty">${escapeHtml(e.message)}</td></tr>`;$("reportSummary").textContent="Report data unavailable";}
  }
  function attachEvents() {
    document.querySelectorAll(".nav-link").forEach((el)=>el.addEventListener("click",()=>showPage(el.dataset.page)));
    document.querySelectorAll("[data-goto]").forEach((el)=>el.addEventListener("click",()=>showPage(el.dataset.goto)));
    $("mobileMenu").addEventListener("click",()=>{const open=$("sidebar").classList.toggle("open");$("mobileMenu").setAttribute("aria-expanded",String(open));});
    $("addDeliveryTop").addEventListener("click",openNewDelivery);$("addDelivery").addEventListener("click",openNewDelivery);$("deliveryForm").addEventListener("submit",saveDelivery);
    $("closeDialog").addEventListener("click",()=>$("deliveryDialog").close());$("cancelDialog").addEventListener("click",()=>$("deliveryDialog").close());$("closeHistory").addEventListener("click",()=>$("historyDialog").close());$("closeHistoryFooter").addEventListener("click",()=>$("historyDialog").close());
    $("geocodeButton").addEventListener("click",geocode);$("deliverySearch").addEventListener("input",renderDeliveries);$("statusFilter").addEventListener("change",renderDeliveries);$("priorityFilter").addEventListener("change",renderDeliveries);$("clearFilters").addEventListener("click",()=>{$("deliverySearch").value="";$("statusFilter").value="";$("priorityFilter").value="";renderDeliveries();});
    $("deliveryRows").addEventListener("change",(e)=>{if(e.target.matches("[data-status-id]"))setStatus(e.target.dataset.statusId,e.target.value);});
    $("deliveryRows").addEventListener("click",(e)=>{const b=e.target.closest("button");if(!b)return;if(b.dataset.editId)openEditDelivery(b.dataset.editId);if(b.dataset.deleteId)deleteDelivery(b.dataset.deleteId);if(b.dataset.historyId)showHistory(b.dataset.historyId);if(b.dataset.proofId){state.selectedProofId=b.dataset.proofId;$("proofInput").click();}});
    $("proofInput").addEventListener("change",(e)=>uploadProof(e.target.files[0]));$("routeStops").addEventListener("change",(e)=>{if(e.target.matches(".route-checkbox")){updateRouteSelectCount();renderRouteLocationMap();clearRouteMetrics();}});
    ["depotLat","depotLon","depotLabel"].forEach((id)=>$(id).addEventListener("input",renderRouteLocationMap));$("optimizeRoute").addEventListener("click",optimizeRoute);
    $("refreshDashboard").addEventListener("click",loadCore);$("applyReportFilters").addEventListener("click",loadReportRows);$("exportCsv").addEventListener("click",exportCsv);
  }
  async function start() {
    $("todayLabel").textContent=new Intl.DateTimeFormat(undefined,{weekday:"short",month:"short",day:"numeric"}).format(new Date());
    state.overviewMap=createMap("overviewMap");state.routeMap=createMap("routeMap");attachEvents();
    const page=location.hash.replace("#","");if(["dashboard","deliveries","routes","reports"].includes(page))showPage(page);
    await loadCore();
  }
  document.addEventListener("DOMContentLoaded",start);
})();
