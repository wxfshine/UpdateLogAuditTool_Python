const state = {
  dashboard: null,
  months: [],
  currentMonth: null,
  currentReport: null,
  alerts: []
};

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

function statusBadge(status) {
  return `<span class="status ${status}">${status}</span>`;
}

function renderSummaryCards(dashboard) {
  const cards = dashboard.summary_cards;
  document.getElementById("summary-cards").innerHTML = `
    <div class="card"><div class="label">\u90e8\u95e8\u6570</div><div class="value">${cards.department_count}</div></div>
    <div class="card"><div class="label">\u6708\u4efd\u6570</div><div class="value">${cards.month_count}</div></div>
    <div class="card"><div class="label">\u6587\u4ef6\u6570</div><div class="value">${cards.file_count}</div></div>
    <div class="card"><div class="label">\u5f02\u5e38\u6570</div><div class="value">${cards.alert_count}</div></div>
    <div class="card"><div class="label">\u6700\u65b0\u6708\u4efd</div><div class="value">${cards.latest_month || "--"}</div></div>
  `;
}

function renderDepartmentCards(dashboard) {
  const rd = dashboard.departments.find(item => item.department_id === "rd");
  const latest = dashboard.latest_service_report;

  document.getElementById("rd-placeholder").innerHTML = `
    <div class="item">
      <div class="kv">
        <div class="k">\u6570\u636e\u6e90</div><div>${rd.source_type}</div>
        <div class="k">\u72b6\u6001</div><div>${statusBadge(rd.status)}</div>
        <div class="k">\u8bf4\u660e</div><div>${rd.summary}</div>
      </div>
    </div>
  `;

  document.getElementById("latest-service-report").innerHTML = latest ? `
    <div class="item">
      <div class="kv">
        <div class="k">\u6708\u4efd</div><div>${latest.month}</div>
        <div class="k">\u6587\u4ef6\u6570</div><div>${latest.file_count}</div>
        <div class="k">\u603b\u4f53\u72b6\u6001</div><div>${statusBadge(latest.overall_status)}</div>
        <div class="k">\u6700\u8fd1\u540c\u6b65</div><div>${dashboard.last_sync_time || "--"}</div>
      </div>
    </div>
    <div class="step-list">
      ${latest.steps.map(step => `
        <div class="step-item">
          <strong>${step.step_name}</strong>
          <div>${statusBadge(step.status)}</div>
          <div>${step.summary}</div>
        </div>
      `).join("")}
    </div>
  ` : `<div class="item">\u672a\u53d1\u73b0\u670d\u52a1\u90e8\u95e8\u6708\u62a5\u6570\u636e\u3002</div>`;
}

function renderMonthOptions(months) {
  const select = document.getElementById("month-select");
  select.innerHTML = months.map(item => `<option value="${item.month}">${item.month}</option>`).join("");
  if (state.currentMonth) {
    select.value = state.currentMonth;
  }
}

function renderServiceReport(report) {
  const container = document.getElementById("service-month-report");
  if (!report) {
    container.innerHTML = `<div class="item">\u6682\u65e0\u6708\u62a5\u6570\u636e\u3002</div>`;
    return;
  }

  container.innerHTML = `
    <div class="list">
      <div class="item">
        <div class="kv">
          <div class="k">\u6708\u4efd</div><div>${report.month}</div>
          <div class="k">\u6587\u4ef6\u603b\u6570</div><div>${report.file_count}</div>
          <div class="k">\u603b\u4f53\u72b6\u6001</div><div>${statusBadge(report.overall_status)}</div>
          <div class="k">\u5b8c\u6210\u9636\u6bb5</div><div>${report.summary.completed_step_count}/${report.summary.total_step_count}</div>
        </div>
      </div>
      <div class="item">
        <h3>\u6d41\u7a0b\u72b6\u6001</h3>
        <div class="step-list">
          ${report.steps.map(step => `
            <div class="step-item">
              <strong>${step.step_name}</strong>
              <div>${statusBadge(step.status)}</div>
              <div>${step.summary}</div>
            </div>
          `).join("")}
        </div>
      </div>
      <div class="item">
        <h3>\u6587\u4ef6\u5206\u6790</h3>
        <div class="file-list">
          ${report.files.map(file => `
            <div class="file-item">
              <div class="kv">
                <div class="k">\u6587\u4ef6\u540d</div><div>${file.file_name}</div>
                <div class="k">\u5206\u7c7b</div><div>${file.category}</div>
                <div class="k">\u4fee\u6539\u65f6\u95f4</div><div>${file.modified_time}</div>
                <div class="k">\u6458\u8981</div><div>${file.summary}</div>
              </div>
              <ul>
                ${file.analysis.details.map(detail => `<li>${detail}</li>`).join("")}
              </ul>
              ${file.preview ? `<pre>${escapeHtml(file.preview)}</pre>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}

function renderCompare(items) {
  const container = document.getElementById("compare-table");
  if (!items.length) {
    container.innerHTML = `<div class="item">\u6682\u65e0\u5bf9\u6bd4\u6570\u636e\u3002</div>`;
    return;
  }

  container.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>\u6708\u4efd</th>
          <th>\u53d6\u5305Hash</th>
          <th>UC\u68c0\u67e5</th>
          <th>\u4e0a\u4f20\u5ba1\u6279</th>
          <th>\u8865\u4e01\u9a8c\u8bc1</th>
          <th>\u603b\u4f53\u72b6\u6001</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${item.month}</td>
            <td>${statusBadge(item.hash_status)}</td>
            <td>${statusBadge(item.env_status)}</td>
            <td>${statusBadge(item.approval_status)}</td>
            <td>${statusBadge(item.validation_status)}</td>
            <td>${statusBadge(item.overall_status)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderAlerts(alerts) {
  const container = document.getElementById("alerts-list");
  if (!alerts.length) {
    container.innerHTML = `<div class="item">\u5f53\u524d\u6ca1\u6709\u5f02\u5e38\uff0c\u9875\u9762\u5904\u4e8e\u6f14\u793a\u5b8c\u6210\u72b6\u6001\u3002</div>`;
    return;
  }

  container.innerHTML = `<div class="alert-list">${alerts.map(alert => `
    <div class="alert-item">
      <div class="kv">
        <div class="k">\u6708\u4efd</div><div>${alert.month}</div>
        <div class="k">\u6807\u9898</div><div>${alert.title}</div>
        <div class="k">\u7ea7\u522b</div><div>${alert.severity}</div>
        <div class="k">\u8bf4\u660e</div><div>${alert.message}</div>
      </div>
    </div>
  `).join("")}</div>`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function loadDashboard() {
  state.dashboard = await fetchJson("/api/dashboard");
  renderSummaryCards(state.dashboard);
  renderDepartmentCards(state.dashboard);
}

async function loadMonths() {
  const data = await fetchJson("/api/departments/service/months");
  state.months = data.months;
  state.currentMonth = state.months[0]?.month || null;
  renderMonthOptions(state.months);
}

async function loadCurrentMonth() {
  if (!state.currentMonth) {
    renderServiceReport(null);
    return;
  }
  state.currentReport = await fetchJson(`/api/departments/service/months/${state.currentMonth}`);
  renderServiceReport(state.currentReport);
}

async function loadCompare() {
  const data = await fetchJson("/api/compare/months");
  renderCompare(data.items);
}

async function loadAlerts() {
  state.alerts = await fetchJson("/api/alerts");
  renderAlerts(state.alerts);
}

function bindEvents() {
  document.querySelectorAll(".tab-button").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab-button").forEach(item => item.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(item => item.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.tab).classList.add("active");
    });
  });

  document.getElementById("month-select").addEventListener("change", async event => {
    state.currentMonth = event.target.value;
    await loadCurrentMonth();
  });
}

async function init() {
  bindEvents();
  await loadDashboard();
  await loadMonths();
  await loadCurrentMonth();
  await loadCompare();
  await loadAlerts();
}

init().catch(error => {
  console.error(error);
  document.body.insertAdjacentHTML("beforeend", `<div class="panel">\u9875\u9762\u52a0\u8f7d\u5931\u8d25\uff1a${error.message}</div>`);
});
