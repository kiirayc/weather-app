function emojiFor(iconOrMain, isNight = false) { 
  const c = (iconOrMain || "").toLowerCase();

  if (c.startsWith("01")) return isNight ? "🌙" : "☀️"; 
  if (c.startsWith("02")) return "🌤️";
  if (c.startsWith("03")) return "⛅"; 
  if (c.startsWith("04")) return "☁️"; 
  if (c.startsWith("09")) return "🌧️";
  if (c.startsWith("10")) return "🌦️"; 
  if (c.startsWith("11")) return "⛈️"; 
  if (c.startsWith("13")) return "❄️";
  if (c.startsWith("50")) return "🌫️";

  const m = c;
  if (m.includes("thunder")) return "⛈️"; 
  if (m.includes("drizzle")) return "🌦️"; 
  if (m.includes("rain")) return "🌧️";
  if (m.includes("snow")) return "❄️"; 
  if (m.includes("mist") || m.includes("fog") || m.includes("haze") || m.includes("smoke")) return "🌫️";
  if (m.includes("cloud")) return "☁️"; 
  if (m.includes("clear")) return isNight ? "🌙" : "☀️"; 

  return "🌍"; 
}

function isNightFromIcon(icon) { 
  return typeof icon === "string" && icon.endsWith("n"); 
}

// Current weather
async function fetchCurrent(lat = null, lon = null) {
  let url = '/api/weather/current?';
  const q = $('q')?.value.trim() || '';

  if (lat && lon) {
    url += `lat=${lat}&lon=${lon}`;
  } else if (q) {
    url += `q=${encodeURIComponent(q)}`;
  } else {
    return alert('Enter a location or use geolocation');
  }

  const res = await fetch(url);
  const data = await res.json();

  const w0 = (data.weather && data.weather[0]) || {}; 
  const main = data.main || {};

  const city = data.name || '—'; 
  const country = data.sys && data.sys.country ? data.sys.country : '';
  const icon = w0.icon || ''; 
  const night = isNightFromIcon(icon); 
  const emoji = emojiFor(icon || w0.main || '', night);

  const feels = main.feels_like != null ? `${Math.round(main.feels_like)}°C` : '—';
  const temp  = main.temp != null ? `${Math.round(main.temp)}°C` : '—';
  const humid = main.humidity != null ? `${main.humidity}%` : '—';
  const wind  = data.wind && data.wind.speed != null ? `${Math.round(data.wind.speed)} m/s` : '—';
  const desc  = w0.description || w0.main || '—';

  $('currentOut').innerHTML = `
    <div class="emoji" aria-hidden="true">${emoji}</div>
    <div>
      <div style="font-size:1.1rem; font-weight:700;">
        ${city}${country ? ', ' + country : ''}
      </div>
      <div class="meta" style="margin-top:.25rem">
        <div class="kv">Condition</div><div>${desc}</div>
        <div class="kv">Temp</div><div>${temp}</div>
        <div class="kv">Feels like</div><div>${feels}</div>
        <div class="kv">Humidity</div><div>${humid}</div>
        <div class="kv">Wind</div><div>${wind}</div>
      </div>
    </div>`;
}

// Forecast
async function fetchForecast(lat = null, lon = null) {
  let url = '/api/weather/forecast?';
  const q = $('q')?.value.trim() || '';

  if (lat && lon) {
    url += `lat=${lat}&lon=${lon}`;
  } else if (q) {
    url += `q=${encodeURIComponent(q)}`;
  } else {
    return alert('Enter a location or use geolocation');
  }

  const res = await fetch(url); 
  const data = await res.json(); 
  const list = data.list || [];

  const byDay = {};
  for (const item of list) {
    const dayKey = new Date(item.dt * 1000).toISOString().split('T')[0];
    (byDay[dayKey] ??= []).push(item);
  }

  const days = Object.keys(byDay).slice(0, 5);

  if (!days.length) { 
    $('forecastOut').innerHTML = '<em class="muted">No forecast yet.</em>'; 
    return; 
  }

  let html = '';
  for (const day of days) {
    const bucket = byDay[day]; 
    const tmins = [], tmaxs = [], votes = {};

    for (const x of bucket) {
      const t = x.main && typeof x.main.temp === 'number' ? x.main.temp : null;
      if (t != null) { 
        tmins.push(x.main.temp_min ?? t); 
        tmaxs.push(x.main.temp_max ?? t); 
      }

      const w0 = (x.weather && x.weather[0]) || {}; 
      const ic = w0.icon || w0.main || 'clouds';
      votes[ic] = (votes[ic] || 0) + 1;
    }

    const tmin = tmins.length ? Math.round(Math.min(...tmins)) : '—';
    const tmax = tmaxs.length ? Math.round(Math.max(...tmaxs)) : '—';
    const topIcon = Object.entries(votes).sort((a, b) => b[1] - a[1])[0]?.[0] || 'clouds';
    const emoji = emojiFor(topIcon, isNightFromIcon(topIcon));

    html += `
      <div class="forecast-card">
        <div class="badge">${day}</div>
        <div class="emoji" aria-hidden="true">${emoji}</div>
        <div class="temp">${tmin}°C – ${tmax}°C</div>
      </div>`;
  }

  $('forecastOut').innerHTML = html;
}

// For rendering query results
function renderQuerySummary(q) {
  const loc = q.location 
    ? `${q.location.name}${q.location.country ? `, ${q.location.country}` : ''}` 
    : '—';
  const count = (q.observations || []).length;

  return `
    <div class="badge">Created #${q.id}</div>
    <div><strong>${loc}</strong></div>
    <div class="muted">${q.start_date} → ${q.end_date} · ${count} days</div>
    <div style="margin-top:.5rem;">
    </div>`;
}

function renderQueryDetail(data) {
  const obs = data.observations || [];
  if (!obs.length) { 
    $('detailPanel').innerHTML = '<em class="muted">No observations.</em>'; 
    return; 
  }

  let rows = '';
  for (const o of obs) {
    rows += `
      <tr>
        <td>${o.date}</td>
        <td>${o.t_min ?? '—'}</td>
        <td>${o.t_max ?? '—'}</td>
        <td>${o.t_mean ?? '—'}</td>
      </tr>`;
  }

  $('detailPanel').innerHTML = `
    <table>
      <thead>
        <tr><th>Date</th><th>Min °C</th><th>Max °C</th><th>Mean °C</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// Geolocation
function useGeo() {
  if (!navigator.geolocation) { 
    alert('Geolocation unsupported'); 
    return; 
  }

  navigator.geolocation.getCurrentPosition(
    async pos => {
      const { latitude, longitude } = pos.coords;
      await fetchCurrent(latitude, longitude);
      await fetchForecast(latitude, longitude);
    }, 
    err => alert(err.message), 
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

function toggleInfo() {
    const el = document.getElementById("infoText");
    el.style.display = (el.style.display === "none") ? "inline" : "none";
  }
