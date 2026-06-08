import { renderSwimlaneDiagram, getLocalizedText } from "./modules/swimlaneDiagram.js";

const state = {
  dashboard: null,
  rdAnalysis: null,
  months: [],
  currentMonth: null,
  currentReport: null,
  alerts: [],
  serviceFiles: [],
  dashboardTimelineMonth: null,
  dashboardTimelineItems: [],
  actionSummaryChartCounter: 0,
  swimlaneData: null,
  swimlaneLocale: "zh-CN"
};

async function fetchJson(url) {
  const requestUrl = url.includes("?") ? `${url}&_=${Date.now()}` : `${url}?_=${Date.now()}`;
  const response = await fetch(requestUrl, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

function statusBadge(status) {
  return `<span class="status ${status}">${status}</span>`;
}

function buildPieChartSegments(items) {
  const total = items.reduce((sum, item) => sum + (Number(item.count) || 0), 0);
  if (!total) {
    return { segments: [], total: 0 };
  }

  const colors = [
    "#2563eb",
    "#7c3aed",
    "#db2777",
    "#ea580c",
    "#d97706",
    "#16a34a",
    "#0891b2",
    "#4f46e5",
    "#dc2626",
    "#65a30d"
  ];

  let accumulated = 0;
  const segments = items.map((item, index) => {
    const value = Number(item.count) || 0;
    const ratio = value / total;
    const startAngle = accumulated * Math.PI * 2 - Math.PI / 2;
    accumulated += ratio;
    const endAngle = accumulated * Math.PI * 2 - Math.PI / 2;
    const largeArcFlag = ratio > 0.5 ? 1 : 0;
    const x1 = 50 + 40 * Math.cos(startAngle);
    const y1 = 50 + 40 * Math.sin(startAngle);
    const x2 = 50 + 40 * Math.cos(endAngle);
    const y2 = 50 + 40 * Math.sin(endAngle);
    const pathData = ratio >= 1
      ? "M 50 10 A 40 40 0 1 1 49.999 10 Z"
      : `M 50 50 L ${x1.toFixed(3)} ${y1.toFixed(3)} A 40 40 0 ${largeArcFlag} 1 ${x2.toFixed(3)} ${y2.toFixed(3)} Z`;

    return {
      ...item,
      color: colors[index % colors.length],
      ratio,
      percentage: (ratio * 100).toFixed(1),
      pathData
    };
  });

  return { segments, total };
}

function polarToCartesian(centerX, centerY, radius, angleInRadians) {
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians)
  };
}

function buildDonutArcPath(innerRadius, outerRadius, startAngle, endAngle) {
  const fullCircle = Math.abs(endAngle - startAngle) >= Math.PI * 2 - 0.0001;
  if (fullCircle) {
    return `
      M 50 ${50 - outerRadius}
      A ${outerRadius} ${outerRadius} 0 1 1 49.999 ${50 - outerRadius}
      M 50 ${50 - innerRadius}
      A ${innerRadius} ${innerRadius} 0 1 0 49.999 ${50 - innerRadius}
      Z
    `.replace(/\s+/g, " ").trim();
  }

  const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0;
  const outerStart = polarToCartesian(50, 50, outerRadius, startAngle);
  const outerEnd = polarToCartesian(50, 50, outerRadius, endAngle);
  const innerEnd = polarToCartesian(50, 50, innerRadius, endAngle);
  const innerStart = polarToCartesian(50, 50, innerRadius, startAngle);

  return `
    M ${outerStart.x.toFixed(3)} ${outerStart.y.toFixed(3)}
    A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${outerEnd.x.toFixed(3)} ${outerEnd.y.toFixed(3)}
    L ${innerEnd.x.toFixed(3)} ${innerEnd.y.toFixed(3)}
    A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerStart.x.toFixed(3)} ${innerStart.y.toFixed(3)}
    Z
  `.replace(/\s+/g, " ").trim();
}

function buildConcentricActionSummaryData(items) {
  const palette = [
    "#38bdf8",
    "#818cf8",
    "#a78bfa",
    "#f472b6",
    "#fb7185",
    "#f59e0b",
    "#34d399",
    "#22c55e"
  ];
  const normalizedItems = (items || [])
    .map(item => ({
      ...item,
      count: Number(item.count) || 0
    }))
    .filter(item => item.count > 0);
  const total = normalizedItems.reduce((sum, item) => sum + item.count, 0);

  if (!total) {
    return {
      total: 0,
      categorySegments: [],
      actionSegments: []
    };
  }

  const categoryMap = new Map();

  normalizedItems.forEach(item => {
    const categoryName = item.category_name || "未命名大类";
    if (!categoryMap.has(categoryName)) {
      const categoryIndex = categoryMap.size;
      categoryMap.set(categoryName, {
        id: `cat-${categoryIndex}`,
        name: categoryName,
        count: 0,
        baseColor: palette[categoryIndex % palette.length],
        actionIndex: 0,
        actions: []
      });
    }
    const category = categoryMap.get(categoryName);
    category.count += item.count;
    category.actions.push({
      name: item.action_name || "未命名动作",
      count: item.count
    });
  });

  const categories = [...categoryMap.values()];
  let accumulated = 0;
  const actionSegments = [];

  categories.forEach(category => {
    category.actions.forEach(action => {
      const startAngle = accumulated * Math.PI * 2 - Math.PI / 2;
      accumulated += action.count / total;
      const endAngle = accumulated * Math.PI * 2 - Math.PI / 2;
      const actionIndex = category.actionIndex++;
      const opacity = Math.max(0.42, 0.94 - actionIndex * 0.1);
      const actionId = `act-${actionSegments.length}`;

      actionSegments.push({
        id: actionId,
        name: action.name,
        categoryName: category.name,
        categoryId: category.id,
        count: action.count,
        percentage: ((action.count / total) * 100).toFixed(1),
        fill: category.baseColor,
        opacity: opacity.toFixed(2),
        highlightKeys: `${category.id} ${actionId}`,
        pathData: buildDonutArcPath(30, 46, startAngle, endAngle)
      });
    });
  });

  accumulated = 0;
  const categorySegments = categories.map(category => {
    const startAngle = accumulated * Math.PI * 2 - Math.PI / 2;
    accumulated += category.count / total;
    const endAngle = accumulated * Math.PI * 2 - Math.PI / 2;

    return {
      id: category.id,
      name: category.name,
      count: category.count,
      percentage: ((category.count / total) * 100).toFixed(1),
      fill: category.baseColor,
      highlightKeys: category.id,
      pathData: buildDonutArcPath(14, 28, startAngle, endAngle)
    };
  });

  return {
    total,
    categorySegments,
    actionSegments
  };
}

function renderConcentricActionSummaryChart(items) {
  const { total, categorySegments, actionSegments } = buildConcentricActionSummaryData(items);

  if (!total) {
    return "";
  }

  const chartId = `action-summary-chart-${++state.actionSummaryChartCounter}`;

  return `
    <div class="action-summary-donut-card action-summary-concentric-card" data-action-summary-card="${chartId}">
      <div class="action-summary-donut-header">
        <h5 id="${chartId}-title">操作动作分类汇总</h5>
      </div>
      <div class="action-summary-concentric-layout">
        <div class="action-summary-donut-chart action-summary-concentric-chart tech-ring">
          <svg viewBox="0 0 100 100" class="pie-chart pie-chart-lg action-summary-concentric-svg" aria-labelledby="${chartId}-title">
            ${categorySegments.map(segment => `
              <path
                class="action-summary-segment action-summary-category-segment"
                d="${segment.pathData}"
                fill="${segment.fill}"
                tabindex="0"
                data-action-summary-target="${segment.highlightKeys}"
                data-action-summary-highlight="${segment.highlightKeys}"
                style="--segment-glow:${segment.fill}; --segment-opacity:0.96; --segment-dim-opacity:0.2;"
              >
                <title>大类：${escapeHtml(segment.name)}，${segment.count} 次，占比 ${segment.percentage}%</title>
              </path>
            `).join("")}
            ${actionSegments.map(segment => `
              <path
                class="action-summary-segment action-summary-action-segment"
                d="${segment.pathData}"
                fill="${segment.fill}"
                tabindex="0"
                data-action-summary-target="${segment.highlightKeys}"
                data-action-summary-highlight="${segment.highlightKeys}"
                style="--segment-glow:${segment.fill}; --segment-opacity:${segment.opacity}; --segment-dim-opacity:${Math.max(0.12, Number(segment.opacity) * 0.28).toFixed(2)};"
              >
                <title>动作：${escapeHtml(segment.name)}，所属大类：${escapeHtml(segment.categoryName)}，${segment.count} 次，占比 ${segment.percentage}%</title>
              </path>
            `).join("")}
            <circle cx="50" cy="50" r="12" fill="#061121"></circle>
            <circle cx="50" cy="50" r="11" fill="rgba(15, 23, 42, 0.97)" stroke="#60a5fa" stroke-width="0.7"></circle>
          </svg>
          <div class="pie-chart-center pie-chart-center-lg">
            <strong>${total}</strong>
            <span>总操作</span>
            <small class="action-summary-concentric-note">内环：大类 / 外环：操作动作</small>
          </div>
        </div>
        <div class="action-summary-concentric-legends">
          <div class="action-summary-legend-block">
            <h6>大类</h6>
            <div class="action-summary-legend-list">
              ${categorySegments.map(segment => `
                <button
                  type="button"
                  class="action-summary-legend-chip"
                  data-action-summary-target="${segment.highlightKeys}"
                  data-action-summary-highlight="${segment.highlightKeys}"
                >
                  <span class="legend-dot legend-dot-lg" style="background:${segment.fill}; color:${segment.fill}; --legend-glow:${segment.fill};"></span>
                  <span class="action-summary-inline-text">
                    <strong>${escapeHtml(segment.name)}</strong>
                    <span>${segment.count} 次 / ${segment.percentage}%</span>
                  </span>
                </button>
              `).join("")}
            </div>
          </div>
          <div class="action-summary-legend-block">
            <h6>操作动作</h6>
            <div class="action-summary-legend-list">
              ${actionSegments.map(segment => `
                <button
                  type="button"
                  class="action-summary-legend-chip"
                  data-action-summary-target="${segment.highlightKeys}"
                  data-action-summary-highlight="${segment.highlightKeys}"
                >
                  <span class="legend-dot legend-dot-lg" style="background:${segment.fill}; opacity:${segment.opacity}; color:${segment.fill}; --legend-glow:${segment.fill};"></span>
                  <span class="action-summary-inline-text">
                    <strong>${escapeHtml(segment.name)}</strong>
                    <span>${escapeHtml(segment.categoryName)} / ${segment.count} 次 / ${segment.percentage}%</span>
                  </span>
                </button>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function summarizeByField(items, fieldName, labelName) {
  const summaryMap = new Map();

  (items || []).forEach(item => {
    const label = item[fieldName] || `未命名${labelName}`;
    const count = Number(item.count) || 0;
    if (!summaryMap.has(label)) {
      summaryMap.set(label, {
        label,
        count: 0
      });
    }
    summaryMap.get(label).count += count;
  });

  return [...summaryMap.values()]
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .map(item => ({
      category_name: labelName,
      action_name: item.label,
      count: item.count
    }));
}

function renderActionSummaryDonutChart(title, centerLabel, items) {
  const { segments, total } = buildPieChartSegments(items);

  return `
    <div class="action-summary-donut-card">
      <div class="action-summary-donut-header">
        <h5>${escapeHtml(title)}</h5>
      </div>
      <div class="action-summary-donut-chart tech-ring">
        <svg viewBox="0 0 100 100" class="pie-chart pie-chart-lg" aria-label="${escapeHtml(title)}">
          ${segments.map(segment => `<path d="${segment.pathData}" fill="${segment.color}"></path>`).join("")}
          <circle cx="50" cy="50" r="24" fill="#061121"></circle>
          <circle cx="50" cy="50" r="22" fill="rgba(15, 23, 42, 0.96)" stroke="#1d4ed8" stroke-width="0.8"></circle>
        </svg>
        <div class="pie-chart-center pie-chart-center-lg">
          <strong>${total}</strong>
          <span>${escapeHtml(centerLabel)}</span>
        </div>
      </div>
      <div class="action-summary-inline-labels">
        ${segments.map(segment => `
          <div class="action-summary-inline-label">
            <span class="legend-dot legend-dot-lg" style="background:${segment.color}"></span>
            <div class="action-summary-inline-text">
              <strong>${escapeHtml(segment.action_name)}</strong>
              <span>${segment.count} 次 / ${segment.percentage}%</span>
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
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

function normalizeTimelineTime(value) {
  if (!value) {
    return 0;
  }

  const normalized = String(value).replace(" ", "T");
  const timestamp = Date.parse(normalized);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function buildFallbackDashboardTimelineItems() {
  const items = [];

  if (state.rdAnalysis?.people) {
    state.rdAnalysis.people.forEach(person => {
      (person.periods || []).forEach(period => {
        const analysis = period.analysis || {};

        (analysis.operation_records || []).forEach(record => {
          items.push({
            department_id: "rd",
            department_name: "研发部门",
            owner_name: person.person_name || "--",
            month: period.label || "--",
            event_time: record.start_time || record.sort_time || record.end_time || "",
            title: record.action_name || analysis.title || "研发操作",
            status: record.result || analysis.status || "completed",
            summary: record.operation_details || record.details || "",
            source_name: record.source_relative_path || record.source_file || ""
          });
        });

        (analysis.ocr_results || []).forEach(record => {
          items.push({
            department_id: "rd",
            department_name: "研发部门",
            owner_name: person.person_name || "--",
            month: period.label || "--",
            event_time: record.start_time || record.end_time || "",
            title: analysis.title || "PNG OCR 分析",
            status: analysis.status || "completed",
            summary: record.relative_path || "PNG 时间识别",
            source_name: record.relative_path || ""
          });
        });
      });
    });
  }

  (state.serviceFiles || []).forEach(file => {
    items.push({
      department_id: "service",
      department_name: "服务部门",
      owner_name: file.month || "--",
      month: file.month || "--",
      event_time: file.detected_time || file.modified_time || "",
      title: file.analysis?.title || file.summary || file.file_name || "服务部门文件",
      status: file.analysis?.status || "completed",
      summary: file.summary || "",
      source_name: file.relative_path || file.file_name || ""
    });
  });

  return items
    .filter(item => item.event_time)
    .sort((a, b) => normalizeTimelineTime(b.event_time) - normalizeTimelineTime(a.event_time))
    .slice(0, 80);
}

function getDashboardTimelineMonths(items) {
  const months = [...new Set((items || []).map(item => item.month).filter(Boolean))];
  return months.sort((a, b) => b.localeCompare(a));
}

function renderDashboardTimelineMonthOptions(items) {
  const select = document.getElementById("dashboard-timeline-month-select");
  if (!select) {
    return;
  }

  const months = getDashboardTimelineMonths(items);
  if (!months.length) {
    select.innerHTML = `<option value="">暂无月份</option>`;
    state.dashboardTimelineMonth = null;
    return;
  }

  if (!state.dashboardTimelineMonth || !months.includes(state.dashboardTimelineMonth)) {
    state.dashboardTimelineMonth = months[0];
  }

  select.innerHTML = months.map(month => `<option value="${month}">${month}</option>`).join("");
  select.value = state.dashboardTimelineMonth;
}

function refreshDashboardTimeline() {
  if (!state.dashboard) {
    return;
  }

  const items = state.dashboard.timeline_items?.length
    ? state.dashboard.timeline_items
    : buildFallbackDashboardTimelineItems();
  state.dashboardTimelineItems = items;
  renderDashboardTimelineMonthOptions(items);

  renderDashboardTimeline({ ...state.dashboard, timeline_items: items });
}

function renderDashboardTimeline(dashboard) {
  const meta = document.getElementById("dashboard-timeline-meta");
  const container = document.getElementById("dashboard-timeline");
  const pendingContainer = document.getElementById("dashboard-timeline-pending");
  const allItems = dashboard.timeline_items || [];
  const selectedMonth = state.dashboardTimelineMonth;
  const monthItems = selectedMonth
    ? allItems.filter(item => item.month === selectedMonth)
    : allItems;
  const timelineItems = monthItems.filter(item => String(item.status || "").toLowerCase() !== "pending");
  const pendingItems = monthItems.filter(item => String(item.status || "").toLowerCase() === "pending");

  meta.innerHTML = `<div class="badge subtle">${selectedMonth || "全部月份"}：时间线 ${timelineItems.length} 条，待处理 ${pendingItems.length} 条</div>`;

  if (!timelineItems.length) {
    container.innerHTML = `<div class="item">当前月份暂无可展示的跨部门时间线事件。</div>`;
  } else {
    container.innerHTML = `
      <div class="dashboard-timeline-list">
        ${timelineItems.map(item => `
          <div class="dashboard-timeline-item ${item.department_id}">
            <div class="dashboard-timeline-dot"></div>
            <div class="dashboard-timeline-card">
              <div class="dashboard-timeline-head">
                <div>
                  <div class="dashboard-timeline-title">${escapeHtml(item.title || "--")}</div>
                  <div class="dashboard-timeline-subtitle">${escapeHtml(item.department_name || "--")} / ${escapeHtml(item.owner_name || "--")}</div>
                </div>
                <div class="dashboard-timeline-time">${escapeHtml(item.event_time || "--")}</div>
              </div>
              <div class="kv compact-kv">
                <div class="k">部门</div><div>${escapeHtml(item.department_name || "--")}</div>
                <div class="k">归属</div><div>${escapeHtml(item.owner_name || "--")}</div>
                <div class="k">来源</div><div>${escapeHtml(item.source_name || "--")}</div>
                <div class="k">摘要</div><div class="timeline-details">${escapeHtml(item.summary || "--")}</div>
              </div>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  if (!pendingContainer) {
    return;
  }

  if (!pendingItems.length) {
    pendingContainer.innerHTML = `<div class="item">当前月份没有待处理事件。</div>`;
    return;
  }

  pendingContainer.innerHTML = `
    <div class="nested-table">
      ${pendingItems.map(item => `
        <div class="item compact-item">
          <div class="kv compact-kv">
            <div class="k">标题</div><div>${escapeHtml(item.title || "--")}</div>
            <div class="k">部门</div><div>${escapeHtml(item.department_name || "--")}</div>
            <div class="k">归属</div><div>${escapeHtml(item.owner_name || "--")}</div>
            <div class="k">具体时间</div><div>${escapeHtml(item.event_time || "--")}</div>
            <div class="k">来源</div><div>${escapeHtml(item.source_name || "--")}</div>
            <div class="k">摘要</div><div class="timeline-details">${escapeHtml(item.summary || "--")}</div>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderLiuQingDiagnostics(diagnostics) {
  if (!diagnostics || !diagnostics.summary) {
    return "";
  }

  const summary = diagnostics.summary;
  const fileStats = diagnostics.file_stats || [];
  const unclassifiedActions = diagnostics.unclassified_actions || [];
  const skippedSegments = diagnostics.skipped_segments || [];

  return `
    <div class="nested-table">
      <h4>解析诊断</h4>
      <div class="item compact-item">
        <div class="kv compact-kv">
          <div class="k">日志文件数</div><div>${summary.file_count || 0}</div>
          <div class="k">片段总数</div><div>${summary.segment_count || 0}</div>
          <div class="k">已解析片段</div><div>${summary.parsed_segment_count || 0}</div>
          <div class="k">跳过片段</div><div>${summary.skipped_segment_count || 0}</div>
          <div class="k">未归类动作</div><div>${summary.unclassified_action_count || 0}</div>
        </div>
      </div>
      ${fileStats.length ? `
        <div class="nested-table">
          <h5>按文件统计</h5>
          ${fileStats.map(item => `
            <div class="item compact-item">
              <div class="kv compact-kv">
                <div class="k">源文件</div><div>${escapeHtml(item.source_relative_path)}</div>
                <div class="k">片段总数</div><div>${item.segment_count}</div>
                <div class="k">已解析</div><div>${item.parsed_segment_count}</div>
                <div class="k">跳过</div><div>${item.skipped_segment_count}</div>
                <div class="k">未归类</div><div>${item.unclassified_action_count}</div>
              </div>
            </div>
          `).join("")}
        </div>
      ` : ""}
      ${unclassifiedActions.length ? `
        <div class="nested-table">
          <h5>未归类动作</h5>
          ${unclassifiedActions.map(item => `
            <div class="item compact-item">
              <div class="kv compact-kv">
                <div class="k">源文件</div><div>${escapeHtml(item.source_relative_path)}</div>
                <div class="k">片段序号</div><div>${item.segment_index}</div>
                <div class="k">原始动作</div><div>${escapeHtml(item.action_raw || "--")}</div>
                <div class="k">开始时间</div><div>${escapeHtml(item.start_time || "--")}</div>
                <div class="k">结束时间</div><div>${escapeHtml(item.end_time || "--")}</div>
              </div>
            </div>
          `).join("")}
        </div>
      ` : ""}
      ${skippedSegments.length ? `
        <div class="nested-table">
          <h5>被跳过片段</h5>
          ${skippedSegments.map(item => `
            <div class="item compact-item">
              <div class="kv compact-kv">
                <div class="k">源文件</div><div>${escapeHtml(item.source_relative_path)}</div>
                <div class="k">片段序号</div><div>${item.segment_index}</div>
                <div class="k">跳过原因</div><div>${escapeHtml(item.reason || "--")}</div>
                <div class="k">片段预览</div><div class="timeline-details">${escapeHtml(item.segment_preview || "--")}</div>
              </div>
            </div>
          `).join("")}
        </div>
      ` : ""}
    </div>
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
        <div class="k">\u6700\u65b0\u5feb\u7167</div><div>${rd.snapshot_time || "--"}</div>
        <div class="k">\u76ee\u5f55\u6570</div><div>${rd.period_count || 0}</div>
        <div class="k">\u8bf4\u660e</div><div>${rd.summary}</div>
      </div>
      <div class="step-list compact-list">
        ${(rd.people || []).map(item => `
          <div class="step-item">
            <strong>${item.person_name}</strong>
            <div>${statusBadge(item.status)}</div>
            <div>\u6708\u4efd\u76ee\u5f55\uff1a${item.period_count}</div>
          </div>
        `).join("")}
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

function renderLiuQingActionSummary(items) {
  if (!items || !items.length) {
    return "";
  }

  return `
    <div class="nested-table">
      ${renderConcentricActionSummaryChart(items)}
    </div>
  `;
}

function setActionSummaryHighlight(card, activeTokens) {
  if (!card) {
    return;
  }

  const highlightItems = card.querySelectorAll("[data-action-summary-highlight]");
  const tokens = (activeTokens || []).filter(Boolean);

  if (!tokens.length) {
    card.classList.remove("has-active-highlight");
    highlightItems.forEach(item => {
      item.classList.remove("is-active");
      item.classList.remove("is-dimmed");
    });
    return;
  }

  const tokenSet = new Set(tokens);

  highlightItems.forEach(item => {
    const itemTokens = (item.dataset.actionSummaryHighlight || "").split(/\s+/).filter(Boolean);
    const isActive = itemTokens.some(token => tokenSet.has(token));
    item.classList.toggle("is-active", isActive);
    item.classList.toggle("is-dimmed", !isActive);
  });

  card.classList.add("has-active-highlight");
}

function updateActionSummaryHighlight(target) {
  const card = target?.closest("[data-action-summary-card]");
  const tokens = (target?.dataset.actionSummaryTarget || "").split(/\s+/).filter(Boolean);
  setActionSummaryHighlight(card, tokens);
}

function renderLiuQingOperationTimeline(items) {
  if (!items || !items.length) {
    return "";
  }

  return `
    <div class="nested-table">
      <h4>\u64cd\u4f5c\u65f6\u95f4\u7ebf</h4>
      <div class="dashboard-timeline-list rd-operation-timeline-list">
        ${items.map(item => `
          <div class="dashboard-timeline-item rd">
            <div class="dashboard-timeline-dot"></div>
            <div class="dashboard-timeline-card">
              <div class="dashboard-timeline-head">
                <div>
                  <div class="dashboard-timeline-title">${escapeHtml(item.action_name || "--")}</div>
                  <div class="dashboard-timeline-subtitle">${escapeHtml(item.category_name || "--")} / ${escapeHtml(item.source_relative_path || item.source_file || "--")}</div>
                </div>
                <div class="dashboard-timeline-time">${escapeHtml(item.start_time || item.sort_time || "--")}</div>
              </div>
              <div class="kv compact-kv">
                <div class="k">\u64cd\u4f5c\u7ed3\u679c</div><div>${escapeHtml(item.result || "--")}</div>
                <div class="k">\u7ed3\u675f\u65f6\u95f4</div><div>${escapeHtml(item.end_time || "--")}</div>
                <div class="k">\u673a\u5668\u540d</div><div>${escapeHtml(item.computer_name || "--")}</div>
                <div class="k">\u64cd\u4f5c\u4eba\u5458</div><div>${escapeHtml(item.login_user || "--")}</div>
                <div class="k">\u6267\u884c\u7528\u6237</div><div>${escapeHtml(item.execution_user || "--")}</div>
                <div class="k">操作详情</div><div class="timeline-details">${escapeHtml(item.operation_details || item.details || "--")}</div>
              </div>
            </div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function renderRdReport(report) {
  const meta = document.getElementById("rd-snapshot-meta");
  const container = document.getElementById("rd-report");

  if (!report || !report.people) {
    meta.innerHTML = "";
    container.innerHTML = `<div class="item">\u6682\u65e0\u7814\u53d1\u90e8\u95e8\u6570\u636e\u3002</div>`;
    return;
  }

  meta.innerHTML = `<div class="badge subtle">\u5feb\u7167\u65f6\u95f4\uff1a${report.snapshot_time || report.generated_at || "--"}</div>`;
  container.innerHTML = `
    <div class="list">
      <div class="item">
        <div class="kv">
          <div class="k">\u5feb\u7167\u76ee\u5f55</div><div>${report.snapshot_name}</div>
          <div class="k">\u6587\u4ef6\u603b\u6570</div><div>${report.summary.file_count}</div>
          <div class="k">\u76ee\u5f55\u603b\u6570</div><div>${report.summary.period_count}</div>
          <div class="k">\u751f\u6210\u65f6\u95f4</div><div>${report.generated_at}</div>
        </div>
      </div>
      ${report.people.map(person => `
        <div class="item">
          <h3>${person.person_name}</h3>
          <div class="kv">
            <div class="k">\u72b6\u6001</div><div>${statusBadge(person.status)}</div>
            <div class="k">\u6708\u4efd\u76ee\u5f55\u6570</div><div>${person.period_count}</div>
          </div>
          ${person.periods.length ? `
            <div class="file-list">
              ${person.periods.map(period => `
                <div class="file-item">
                  <div class="kv">
                    <div class="k">\u5b50\u76ee\u5f55</div><div>${period.folder_name}</div>
                    <div class="k">\u5e74\u6708\u6807\u8bb0</div><div>${period.label}</div>
                    <div class="k">\u6587\u4ef6\u6570</div><div>${period.file_count}</div>
                    <div class="k">\u5206\u6790\u7ed3\u679c</div><div>${period.analysis.title}</div>
                  </div>
                  <ul>
                    ${period.analysis.details.map(detail => `<li>${detail}</li>`).join("")}
                  </ul>
                  ${renderLiuQingActionSummary(period.analysis.action_summary)}
                  ${renderLiuQingOperationTimeline(period.analysis.operation_records)}
                  ${renderLiuQingDiagnostics(period.analysis.parse_diagnostics)}
                  ${period.analysis.ocr_results && period.analysis.ocr_results.length ? `
                    <div class="nested-table">
                      ${period.analysis.ocr_results.map(item => `
                        <div class="item compact-item">
                          <div class="kv">
                            <div class="k">\u622a\u56fe\u6587\u4ef6</div><div>${item.relative_path}</div>
                            <div class="k">\u5f00\u59cb\u65f6\u95f4</div><div>${item.start_time || "--"}</div>
                            <div class="k">\u7ed3\u675f\u65f6\u95f4</div><div>${item.end_time || "--"}</div>
                          </div>
                        </div>
                      `).join("")}
                    </div>
                  ` : ""}
                </div>
              `).join("")}
            </div>
          ` : `<div class="item">\u5f53\u524d\u672a\u627e\u5230\u5339\u914d\u7684\u5e74\u6708\u5b50\u76ee\u5f55\u3002</div>`}
        </div>
      `).join("")}
    </div>
  `;
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
    <div class="compare-table-hint">当前展示研发部门 5 项关键流程对比，以及服务部门原有 4 项月度流程对比。</div>
    <div class="compare-table-container">
      <table class="table compare-table">
        <thead>
          <tr>
            <th rowspan="2">\u6708\u4efd</th>
            <th colspan="5">\u7814\u53d1\u90e8\u95e8</th>
            <th colspan="4">\u670d\u52a1\u90e8\u95e8</th>
            <th rowspan="2">\u603b\u4f53\u72b6\u6001</th>
          </tr>
          <tr>
            <th>\u4ece Catalog \u4e0a\u83b7\u5f97\u66f4\u65b0\u5305</th>
            <th>\u4eceWSUS \u4e0a\u83b7\u5f97Metadata</th>
            <th>\u5b8c\u6210 CMIT KB Metadata</th>
            <th>CMIT KB \u4e0a\u4f20\u6587\u4ef6\u5230 FTPS</th>
            <th>FTP\u4e0b\u8f7d\u66f4\u65b0\u6587\u4ef6\uff0c\u7136\u540e\u8fdb\u884c\u6d4b\u8bd5\u9a8c\u8bc1</th>
            <th>\u53d6\u5305Hash</th>
            <th>UC\u68c0\u67e5</th>
            <th>\u4e0a\u4f20\u5ba1\u6279</th>
            <th>\u8865\u4e01\u9a8c\u8bc1</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(item => `
            <tr>
              <td>${escapeHtml(item.month || "--")}</td>
              <td>${statusBadge(item.catalog_update_package_status || "not_found")}</td>
              <td>${statusBadge(item.wsus_metadata_status || "not_found")}</td>
              <td>${statusBadge(item.cmit_kb_metadata_status || "not_found")}</td>
              <td>${statusBadge(item.ftps_upload_status || "not_found")}</td>
              <td>${statusBadge(item.ftp_download_validation_status || "not_found")}</td>
              <td>${statusBadge(item.hash_status || "not_found")}</td>
              <td>${statusBadge(item.env_status || "not_found")}</td>
              <td>${statusBadge(item.approval_status || "not_found")}</td>
              <td>${statusBadge(item.validation_status || "not_found")}</td>
              <td>${statusBadge(item.overall_status || "not_found")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
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
  refreshDashboardTimeline();
}

async function loadRdReport() {
  state.rdAnalysis = await fetchJson("/api/departments/rd/latest");
  renderRdReport(state.rdAnalysis);
  refreshDashboardTimeline();
}

async function loadServiceFiles() {
  state.serviceFiles = await fetchJson("/api/files");
  refreshDashboardTimeline();
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

function renderSwimlaneMeta() {
  const meta = document.getElementById("swimlane-meta");
  if (!meta || !state.swimlaneData) {
    return;
  }

  const locale = state.swimlaneLocale;
  const fallbackLocale = state.swimlaneData.meta?.defaultLocale || "zh-CN";
  const description = getLocalizedText(state.swimlaneData.meta?.description, locale, fallbackLocale);
  const roleCount = state.swimlaneData.roles?.length || 0;
  const stageCount = state.swimlaneData.stages?.length || 0;
  const nodeCount = state.swimlaneData.nodes?.length || 0;

  meta.innerHTML = `
    <div class="badge subtle">${escapeHtml(description)}</div>
    <div class="badge subtle">${locale === "en-US" ? `Roles ${roleCount} / Stages ${stageCount} / Nodes ${nodeCount}` : `角色 ${roleCount} / 阶段 ${stageCount} / 节点 ${nodeCount}`}</div>
  `;
}

function renderSwimlane() {
  const container = document.getElementById("swimlane-diagram");
  if (!container || !state.swimlaneData) {
    return;
  }

  renderSwimlaneMeta();
  renderSwimlaneDiagram(container, state.swimlaneData, {
    locale: state.swimlaneLocale
  });
}

async function loadSwimlane() {
  state.swimlaneData = await fetchJson("/data/swimlane/workflow.cmit-update.example.json");
  renderSwimlane();
}

function updateSwimlaneLocale(locale) {
  state.swimlaneLocale = locale;
  document.querySelectorAll("[data-swimlane-locale]").forEach(button => {
    button.classList.toggle("active", button.dataset.swimlaneLocale === locale);
  });
  renderSwimlane();
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

  document.getElementById("dashboard-timeline-month-select")?.addEventListener("change", event => {
    state.dashboardTimelineMonth = event.target.value;
    refreshDashboardTimeline();
  });

  document.querySelectorAll("[data-swimlane-locale]").forEach(button => {
    button.addEventListener("click", () => {
      updateSwimlaneLocale(button.dataset.swimlaneLocale);
    });
  });

  document.addEventListener("mouseover", event => {
    const target = event.target.closest("[data-action-summary-target]");
    if (!target || (event.relatedTarget instanceof Element && target.contains(event.relatedTarget))) {
      return;
    }

    updateActionSummaryHighlight(target);
  });

  document.addEventListener("mouseout", event => {
    const target = event.target.closest("[data-action-summary-target]");
    if (!target) {
      return;
    }

    const card = target.closest("[data-action-summary-card]");
    const nextTarget = event.relatedTarget instanceof Element
      ? event.relatedTarget.closest("[data-action-summary-target]")
      : null;

    if (nextTarget && card && nextTarget.closest("[data-action-summary-card]") === card) {
      updateActionSummaryHighlight(nextTarget);
      return;
    }

    setActionSummaryHighlight(card, []);
  });

  document.addEventListener("focusin", event => {
    const target = event.target.closest("[data-action-summary-target]");
    if (target) {
      updateActionSummaryHighlight(target);
    }
  });

  document.addEventListener("focusout", event => {
    const target = event.target.closest("[data-action-summary-target]");
    if (!target) {
      return;
    }

    const card = target.closest("[data-action-summary-card]");
    const nextTarget = event.relatedTarget instanceof Element
      ? event.relatedTarget.closest("[data-action-summary-target]")
      : null;

    if (nextTarget && card && nextTarget.closest("[data-action-summary-card]") === card) {
      updateActionSummaryHighlight(nextTarget);
      return;
    }

    setActionSummaryHighlight(card, []);
  });
}

async function init() {
  bindEvents();
  await loadDashboard();
  await loadRdReport();
  await loadServiceFiles();
  await loadMonths();
  await loadCurrentMonth();
  await loadCompare();
  await loadAlerts();
  await loadSwimlane();
}

init().catch(error => {
  console.error(error);
  document.body.insertAdjacentHTML("beforeend", `<div class="panel">\u9875\u9762\u52a0\u8f7d\u5931\u8d25\uff1a${error.message}</div>`);
});
