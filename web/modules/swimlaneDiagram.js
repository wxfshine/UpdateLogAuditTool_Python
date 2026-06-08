const SVG_NS = "http://www.w3.org/2000/svg";

function getLocalizedText(value, locale, fallbackLocale = "zh-CN") {
  if (!value) {
    return "--";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "object") {
    if (value[locale]) {
      return value[locale];
    }
    if (value[fallbackLocale]) {
      return value[fallbackLocale];
    }
    const fallbackValue = Object.values(value).find(Boolean);
    return fallbackValue || "--";
  }

  return String(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function validateSwimlaneData(data) {
  if (!data || typeof data !== "object") {
    throw new Error("Invalid swimlane data.");
  }

  for (const key of ["roles", "stages", "branches", "nodes", "edges"]) {
    if (!Array.isArray(data[key])) {
      throw new Error(`Swimlane data is missing array field: ${key}`);
    }
  }
}

function buildLayout(data) {
  const roles = [...data.roles].sort((a, b) => a.order - b.order);
  const stages = [...data.stages].sort((a, b) => a.order - b.order);
  const branchesByStage = new Map();
  const branchNodeCountsByRole = new Map();

  data.branches.forEach(branch => {
    if (!branchesByStage.has(branch.stageId)) {
      branchesByStage.set(branch.stageId, []);
    }
    branchesByStage.get(branch.stageId).push(branch);
  });

  branchesByStage.forEach(branches => {
    branches.sort((a, b) => a.order - b.order);
  });

  const roleHeaderWidth = 170;
  const stageHeaderHeight = 92;
  const laneWidth = 240;
  const branchBaseHeight = 136;
  const stageGap = 20;
  const contentPadding = 24;
  const nodeHeight = 68;
  const innerVerticalGap = 36;
  const branchVerticalPadding = 32;

  const rolePositions = new Map();
  roles.forEach((role, index) => {
    rolePositions.set(role.id, {
      x: roleHeaderWidth + index * laneWidth,
      width: laneWidth
    });
  });

  const nodesByBranchRole = new Map();
  data.nodes.forEach(node => {
    const key = `${node.branchId}::${node.roleId}`;
    if (!nodesByBranchRole.has(key)) {
      nodesByBranchRole.set(key, []);
    }
    nodesByBranchRole.get(key).push(node);
  });

  nodesByBranchRole.forEach(nodes => {
    nodes.sort((a, b) => a.order - b.order);
  });

  nodesByBranchRole.forEach((nodes, key) => {
    const [branchId, roleId] = key.split("::");
    if (!branchNodeCountsByRole.has(branchId)) {
      branchNodeCountsByRole.set(branchId, new Map());
    }
    branchNodeCountsByRole.get(branchId).set(roleId, nodes.length);
  });

  const stageLayouts = [];
  let currentY = stageHeaderHeight;

  stages.forEach(stage => {
    const branches = branchesByStage.get(stage.id) || [];
    const branchLayouts = [];
    let branchY = currentY;

    if (!branches.length) {
      branchLayouts.push({
        id: `${stage.id}__default_branch`,
        stageId: stage.id,
        order: 1,
        name: null,
        y: branchY,
        height: branchBaseHeight
      });
      branchY += branchBaseHeight;
    } else {
      branches.forEach(branch => {
        const roleCounts = branchNodeCountsByRole.get(branch.id);
        const maxNodesInRole = roleCounts ? Math.max(...roleCounts.values()) : 0;
        const calculatedHeight = maxNodesInRole > 0
          ? maxNodesInRole * nodeHeight + Math.max(0, maxNodesInRole - 1) * innerVerticalGap + branchVerticalPadding
          : branchBaseHeight;
        const branchHeight = Math.max(branchBaseHeight, calculatedHeight);

        branchLayouts.push({
          ...branch,
          y: branchY,
          height: branchHeight
        });
        branchY += branchHeight;
      });
    }

    const stageHeight = branchY - currentY;
    stageLayouts.push({
      ...stage,
      y: currentY,
      height: stageHeight,
      branches: branchLayouts
    });
    currentY = branchY + stageGap;
  });

  const branchPositionMap = new Map();
  stageLayouts.forEach(stage => {
    stage.branches.forEach(branch => {
      branchPositionMap.set(branch.id, branch);
    });
  });

const nodeWidth = 184;
  const nodeLayouts = new Map();

  // 按分支计算每个角色的最大节点数，确定统一的起始 Y
  const branchMaxNodes = new Map();
  nodesByBranchRole.forEach((nodes, key) => {
    const [branchId] = key.split("::");
    if (!branchMaxNodes.has(branchId)) branchMaxNodes.set(branchId, 0);
    if (nodes.length > branchMaxNodes.get(branchId)) branchMaxNodes.set(branchId, nodes.length);
  });

  // 按分支统一计算起始 Y，使同一分支不同角色的等序节点水平对齐
  const branchStartY = new Map();
  branchMaxNodes.forEach((maxCount, branchId) => {
    const branch = branchPositionMap.get(branchId);
    if (!branch) return;
    const totalHeight = maxCount * nodeHeight + Math.max(0, maxCount - 1) * innerVerticalGap;
    const startY = branch.y + Math.max(16, (branch.height - totalHeight) / 2);
    branchStartY.set(branchId, startY);
  });

  nodesByBranchRole.forEach((nodes, key) => {
    const [branchId, roleId] = key.split("::");
    const branch = branchPositionMap.get(branchId);
    const role = rolePositions.get(roleId);
    if (!branch || !role) {
      return;
    }

    const startY = branchStartY.get(branchId) || branch.y + 16;

    nodes.forEach((node, index) => {
      const x = role.x + (role.width - nodeWidth) / 2;
      const y = startY + index * (nodeHeight + innerVerticalGap);
      nodeLayouts.set(node.id, {
        ...node,
        x,
        y,
        width: nodeWidth,
        height: nodeHeight,
        centerX: x + nodeWidth / 2,
        centerY: y + nodeHeight / 2
      });
    });
  });

  return {
    roles,
    stages: stageLayouts,
    roleHeaderWidth,
    stageHeaderHeight,
    laneWidth,
    width: roleHeaderWidth + roles.length * laneWidth,
    height: currentY + contentPadding,
    nodeLayouts
  };
}

function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tagName);
  Object.entries(attributes).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      element.setAttribute(key, String(value));
    }
  });
  return element;
}

function createForeignText(x, y, width, height, className, html) {
  const foreignObject = createSvgElement("foreignObject", { x, y, width, height });
  const div = document.createElement("div");
  div.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
  div.className = className;
  div.innerHTML = html;
  foreignObject.appendChild(div);
  return foreignObject;
}

function buildNodeClass(type) {
  return `swimlane-node swimlane-node-${type || "task"}`;
}

// 获取产出物类型的图标路径
function getArtifactIconPath(type) {
  const icons = {
    document: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z M14 3v5h5 M16 13H8 M16 17H8 M10 9H8",
    report: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z M14 3v5h5 M9 13l2 2 4-4",
    environment: "M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2z M9 2v16 M15 10l-2 2-2-2",
    data: "M12 2C7 2 3 4 3 7v10c0 3 4 5 9 5s9-2 9-5V7c0-3-4-5-9-5z M3 7c0 3 4 5 9 5s9-2 9-5 M3 12c0 3 4 5 9 5s9-2 9-5",
    record: "M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"
  };
  return icons[type] || icons.document;
}

// 创建产出物图标组
function createArtifactIconGroup(artifacts, x, y, locale, fallbackLocale) {
  const group = createSvgElement("g", { class: "swimlane-artifact-group" });
  const iconSize = 20;
  const spacing = 24;

  artifacts.forEach((artifact, index) => {
    const iconX = x + index * spacing;
    const iconY = y;

    // 图标背景
    const bg = createSvgElement("circle", {
      cx: iconX + iconSize / 2,
      cy: iconY + iconSize / 2,
      r: iconSize / 2 + 2,
      class: "swimlane-artifact-bg"
    });
    group.appendChild(bg);

    // 图标
    const icon = createSvgElement("path", {
      d: getArtifactIconPath(artifact.type),
      class: `swimlane-artifact-icon swimlane-artifact-icon-${artifact.type || "document"}`,
      transform: `translate(${iconX}, ${iconY}) scale(0.8)`
    });
    group.appendChild(icon);

    // 标题提示
    const title = createSvgElement("title", {});
    title.textContent = getLocalizedText(artifact.name, locale, fallbackLocale);
    group.appendChild(title);
  });

  return group;
}

function renderSwimlaneDiagram(container, data, options = {}) {
  validateSwimlaneData(data);
  const locale = options.locale || data.meta?.defaultLocale || "zh-CN";
  const fallbackLocale = data.meta?.defaultLocale || "zh-CN";
  const layout = buildLayout(data);

  container.innerHTML = "";

  const wrapper = document.createElement("div");
  wrapper.className = "swimlane-diagram-wrapper";

  const header = document.createElement("div");
  header.className = "swimlane-diagram-header";
  header.innerHTML = `
    <div>
      <h3>${escapeHtml(getLocalizedText(data.meta?.title, locale, fallbackLocale))}</h3>
      <p>${escapeHtml(getLocalizedText(data.meta?.description, locale, fallbackLocale))}</p>
    </div>
  `;
  wrapper.appendChild(header);

  const scroller = document.createElement("div");
  scroller.className = "swimlane-diagram-scroller";

  const svg = createSvgElement("svg", {
    class: "swimlane-diagram-svg",
    viewBox: `0 0 ${layout.width} ${layout.height}`,
    width: layout.width,
    height: layout.height,
    role: "img",
    "aria-label": getLocalizedText(data.meta?.title, locale, fallbackLocale)
  });

  const defs = createSvgElement("defs");
  const marker = createSvgElement("marker", {
    id: `arrow-${locale.replace(/[^a-zA-Z0-9]/g, "-")}`,
    markerWidth: 10,
    markerHeight: 10,
    refX: 9,
    refY: 5,
    orient: "auto-start-reverse"
  });
  marker.appendChild(createSvgElement("path", {
    d: "M 0 0 L 10 5 L 0 10 z",
    fill: "#3b82f6"
  }));
  defs.appendChild(marker);
  svg.appendChild(defs);

  svg.appendChild(createSvgElement("rect", {
    x: 0,
    y: 0,
    width: layout.width,
    height: layout.height,
    fill: "#f8fbff",
    rx: 20
  }));

  const rolePositions = new Map();
  layout.roles.forEach((role, index) => {
    const x = layout.roleHeaderWidth + index * layout.laneWidth;
    rolePositions.set(role.id, { x, width: layout.laneWidth });

    svg.appendChild(createSvgElement("rect", {
      x,
      y: 0,
      width: layout.laneWidth,
      height: layout.height,
      fill: index % 2 === 0 ? "#f5f9ff" : "#eef5ff"
    }));

    svg.appendChild(createSvgElement("rect", {
      x,
      y: 0,
      width: layout.laneWidth,
      height: layout.stageHeaderHeight,
      fill: "#dbeafe",
      stroke: "#bfdbfe"
    }));

    svg.appendChild(createForeignText(
      x + 16,
      16,
      layout.laneWidth - 32,
      layout.stageHeaderHeight - 24,
      "swimlane-role-label",
      `<div>${escapeHtml(getLocalizedText(role.name, locale, fallbackLocale))}</div>`
    ));
  });

  svg.appendChild(createSvgElement("rect", {
    x: 0,
    y: 0,
    width: layout.roleHeaderWidth,
    height: layout.stageHeaderHeight,
    fill: "#1d4ed8"
  }));
  svg.appendChild(createForeignText(
    12,
    12,
    layout.roleHeaderWidth - 24,
    layout.stageHeaderHeight - 24,
    "swimlane-corner-label",
    `<div>${escapeHtml(locale === "en-US" ? "Stages / Roles" : "阶段 / 角色")}</div>`
  ));

  layout.stages.forEach((stage, stageIndex) => {
    svg.appendChild(createSvgElement("rect", {
      x: 0,
      y: stage.y,
      width: layout.roleHeaderWidth,
      height: stage.height,
      fill: stageIndex % 2 === 0 ? "#eff6ff" : "#e0edff",
      stroke: "#bfdbfe"
    }));

    svg.appendChild(createForeignText(
      14,
      stage.y + 12,
      layout.roleHeaderWidth - 28,
      stage.height - 24,
      "swimlane-stage-label",
      `<div>${escapeHtml(getLocalizedText(stage.name, locale, fallbackLocale))}</div>`
    ));

    stage.branches.forEach((branch, branchIndex) => {
      svg.appendChild(createSvgElement("line", {
        x1: layout.roleHeaderWidth,
        y1: branch.y,
        x2: layout.width,
        y2: branch.y,
        stroke: branchIndex === 0 ? "#cbd5e1" : "#dbe3f0",
        "stroke-width": 1
      }));

      if (branch.name) {
        svg.appendChild(createForeignText(
          layout.roleHeaderWidth + 8,
          branch.y + 6,
          180,
          18,
          "swimlane-branch-label",
          `<div>${escapeHtml(getLocalizedText(branch.name, locale, fallbackLocale))}</div>`
        ));
      }
    });
  });

  // 边路由管理器 - 用于避免边重叠和穿越节点
  const occupiedHorizY = new Map();  // 记录每个 y 坐标上已占用的 x 范围
  const nodeRect = [];  // 收集所有节点矩形区域

  // 提前收集所有节点的边界框
  layout.nodeLayouts.forEach(nl => {
    nodeRect.push({ x: nl.x, y: nl.y, w: nl.width, h: nl.height });
  });

  // 计算边的连接点
  function getConnectionPoint(node, edgeType, isSource, targetNode, specifiedSide) {
    const isDecision = node.type === "decision";

    if (specifiedSide) {
      if (specifiedSide === "right") return { x: node.x + node.width, y: node.centerY, side: "right" };
      if (specifiedSide === "left") return { x: node.x, y: node.centerY, side: "left" };
      if (specifiedSide === "top") return { x: node.centerX, y: node.y, side: "top" };
      if (specifiedSide === "bottom") return { x: node.centerX, y: node.y + node.height, side: "bottom" };
    }

    if (isDecision && isSource) {
      if (edgeType === "feedback") {
        if (targetNode && targetNode.centerX < node.centerX) return { x: node.x, y: node.centerY, side: "left" };
        if (targetNode && targetNode.centerX > node.centerX) return { x: node.x + node.width, y: node.centerY, side: "right" };
        return { x: node.x, y: node.centerY, side: "left" };
      }
      return { x: node.centerX, y: node.y + node.height, side: "bottom" };
    }

    if (isSource) {
      // 普通源节点：目标在左侧较远→从左侧出，目标在右侧较远→从右侧出
      // 这样可以实现 L 形（2段线）而非 Z 形（3段线）
      if (targetNode) {
        const dx = targetNode.centerX - node.centerX;
        if (dx < -80) return { x: node.x, y: node.centerY, side: "left" };    // 目标在左→从左侧水平出
        if (dx > 80) return { x: node.x + node.width, y: node.centerY, side: "right" }; // 目标在右→从右侧水平出
      }
      return { x: node.centerX, y: node.y + node.height, side: "bottom" };
    }

    // 目标点：根据与源的相对位置选择最优进入侧面
    if (targetNode) {
      const dx = targetNode.centerX - node.centerX; // 源相对于目标的水平偏移
      if (dx < -60) return { x: node.x, y: node.centerY, side: "left" };   // 源在目标左侧较远→从左侧进
      if (dx > 60) return { x: node.x + node.width, y: node.centerY, side: "right" }; // 源在目标右侧较远→从右侧进
    }
    return { x: node.centerX, y: node.y, side: "top" };
  }

  // 检查水平线段是否穿越任何节点
  function horizLineHitsNode(y, x1, x2) {
    const minX = Math.min(x1, x2);
    const maxX = Math.max(x1, x2);
    return nodeRect.some(r => y > r.y && y < r.y + r.h && minX < r.x + r.w && maxX > r.x);
  }

  // 检查水平线 y 是否与已有线段重叠或穿越节点
  function isHorizYOccupied(y, startX, endX) {
    const minGap = 12;
    // 检查边重叠
    const entries = occupiedHorizY.get(Math.round(y)) || [];
    const edgeOverlap = entries.some(([s, e]) => !(endX + minGap < s || startX - minGap > e));
    // 检查穿越节点
    const nodeHit = horizLineHitsNode(y, startX, endX);
    return edgeOverlap || nodeHit;
  }

  // 记录水平线占用
  function occupyHorizY(y, startX, endX) {
    const key = Math.round(y);
    if (!occupiedHorizY.has(key)) occupiedHorizY.set(key, []);
    occupiedHorizY.get(key).push([Math.min(startX, endX), Math.max(startX, endX)]);
  }

  // 找到可用的水平 y（逐级移动避让边重叠和节点）
  function findClearHorizY(preferredY, startX, endX) {
    let y = preferredY;
    for (let step = 0; step < 30; step++) {
      // 交替尝试向上和向下
      const candidates = [preferredY + step * 7, preferredY - step * 7];
      for (const c of candidates) {
        if (!isHorizYOccupied(c, startX, endX)) { y = c; break; }
      }
      if (y !== preferredY) break;
    }
    occupyHorizY(y, startX, endX);
    return y;
  }

  // 生成最优路径，保证不穿越节点，且末段方向匹配目标入口方向
  function buildPath(start, end) {
    const minSeg = 20;
    const sameX = Math.abs(start.x - end.x) < 5;
    const goingDown = start.y < end.y;

    // --- 1段线：同列垂直（仅限 top/bottom 入口）---
    if (sameX && (end.side === "top" || end.side === "bottom")) {
      return { d: `M ${start.x} ${start.y} L ${end.x} ${end.y}`, mx: start.x, my: (start.y + end.y) / 2 };
    }

    // --- 2段线（L 形）：最后一笔水平，箭头从侧面水平入节点 ---
    // bottom → left：当源节点中心在目标左边时，箭头自然右指入左边缘
    if (start.side === "bottom" && end.side === "left" && start.x < end.x) {
      const horY = findClearHorizY(end.y, start.x, end.x);
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY}`, mx: (start.x + end.x) / 2, my: horY };
    }
    // bottom → right：当源节点中心在目标右边时，箭头自然左指入右边缘
    if (start.side === "bottom" && end.side === "right" && start.x > end.x) {
      const horY = findClearHorizY(end.y, start.x, end.x);
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY}`, mx: (start.x + end.x) / 2, my: horY };
    }

    // --- 3段线（Z 形），末段垂直入节点顶部 ---
    // bottom → left（源在目标右边）：向下→水平→垂直下入左边缘
    if (start.side === "bottom" && end.side === "left") {
      const horY = findClearHorizY(end.y, start.x, end.x);
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY} L ${end.x} ${end.y}`, mx: (start.x + end.x) / 2, my: horY };
    }
    // bottom → right（源在目标左边）：向下→水平→垂直下入右边缘
    if (start.side === "bottom" && end.side === "right") {
      const horY = findClearHorizY(end.y, start.x, end.x);
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY} L ${end.x} ${end.y}`, mx: (start.x + end.x) / 2, my: horY };
    }
    // left/right → top（向下流）
    if ((start.side === "left" || start.side === "right") && end.side === "top" && goingDown) {
      const rowBottom = findNodeRowBottom(start.y);
      const horY = findClearHorizY(rowBottom + 6, start.x, end.x);
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY} L ${end.x} ${end.y}`, mx: (start.x + end.x) / 2, my: horY };
    }
    // left → top（向上反馈）
    if (start.side === "left" && end.side === "top" && !goingDown) {
      const exitX = Math.min(start.x, end.x) - minSeg;
      return { d: `M ${start.x} ${start.y} L ${exitX} ${start.y} L ${exitX} ${end.y} L ${end.x} ${end.y}`, mx: exitX, my: (start.y + end.y) / 2 };
    }
    // right → top（向上反馈）
    if (start.side === "right" && end.side === "top" && !goingDown) {
      const exitX = Math.max(start.x, end.x) + minSeg;
      return { d: `M ${start.x} ${start.y} L ${exitX} ${start.y} L ${exitX} ${end.y} L ${end.x} ${end.y}`, mx: exitX, my: (start.y + end.y) / 2 };
    }

    // --- 通用路径（3段 Z 形）---
    const horY = findClearHorizY((start.y + end.y) / 2, start.x, end.x);

    if (end.side === "top" || end.side === "bottom") {
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY} L ${end.x} ${end.y}`, mx: (start.x + end.x) / 2, my: horY };
    }
    if (end.side === "left") {
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY} L ${end.x} ${end.y}`, mx: (start.x + end.x) / 2, my: horY };
    }
    if (end.side === "right") {
      const exitX = end.x + minSeg;
      return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${exitX} ${horY} L ${exitX} ${end.y} L ${end.x} ${end.y}`, mx: (start.x + exitX) / 2, my: horY };
    }

    // 兜底
    return { d: `M ${start.x} ${start.y} L ${start.x} ${horY} L ${end.x} ${horY} L ${end.x} ${end.y}`, mx: (start.x + end.x) / 2, my: horY };
  }

  // 辅助函数：找到节点所在行的底部 Y（row start + nodeHeight，即间隙上方）
  function findNodeRowBottom(nodeCenterY) {
    for (const r of nodeRect) {
      if (nodeCenterY > r.y && nodeCenterY < r.y + r.h) {
        return r.y + r.h; // 该行的底部边缘
      }
    }
    return nodeCenterY + nodeHeight / 2;
  }

  data.edges.forEach(edge => {
    const fromNode = layout.nodeLayouts.get(edge.from);
    const toNode = layout.nodeLayouts.get(edge.to);
    if (!fromNode || !toNode) return;

    const markerId = `arrow-${locale.replace(/[^a-zA-Z0-9]/g, "-")}`;

    // 自环边（from === to）：用贝塞尔曲线从右侧出再入右侧
    if (edge.from === edge.to) {
      const node = fromNode;
      const loopOffset = 50;
      const loopHeight = 40;
      const startX = node.x + node.width;
      const startY = node.centerY;
      const cp1x = startX + loopOffset;
      const cp1y = startY - loopHeight;
      const cp2x = startX + loopOffset;
      const cp2y = startY + loopHeight;
      const pathData = `M ${startX} ${startY} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${startX} ${startY}`;

      svg.appendChild(createSvgElement("path", {
        d: pathData,
        fill: "none",
        stroke: edge.type === "feedback" ? "#f97316" : edge.type === "dependency" ? "#8b5cf6" : "#3b82f6",
        "stroke-width": 2.2,
        "stroke-dasharray": edge.type === "dependency" ? "7 5" : edge.type === "feedback" ? "10 6" : "none",
        "marker-end": `url(#${markerId})`
      }));

      if (edge.label) {
        const label = getLocalizedText(edge.label, locale, fallbackLocale);
        svg.appendChild(createForeignText(startX + loopOffset - 35, startY - loopHeight - 22, 70, 20, "swimlane-edge-label",
          `<div>${escapeHtml(label)}</div>`));
      }
      return;
    }

    const start = getConnectionPoint(fromNode, edge.type, true, toNode, edge.sourceSide);
    const end = getConnectionPoint(toNode, edge.type, false, fromNode, edge.targetSide);
    const { d: pathData, mx: midX, my: midY } = buildPath(start, end);

    svg.appendChild(createSvgElement("path", {
      d: pathData,
      fill: "none",
      stroke: edge.type === "feedback" ? "#f97316" : edge.type === "dependency" ? "#8b5cf6" : "#3b82f6",
      "stroke-width": 2.2,
      "stroke-dasharray": edge.type === "dependency" ? "7 5" : edge.type === "feedback" ? "10 6" : "none",
      "marker-end": `url(#${markerId})`
    }));

    if (edge.label) {
      const label = getLocalizedText(edge.label, locale, fallbackLocale);
      svg.appendChild(createForeignText(midX - 70, midY - 14, 140, 28, "swimlane-edge-label",
        `<div>${escapeHtml(label)}</div>`));
    }
  });

  data.nodes.forEach(node => {
    const nodeLayout = layout.nodeLayouts.get(node.id);
    if (!nodeLayout) {
      return;
    }

    // 判断节点使用菱形，其他节点使用圆角矩形
    if (node.type === "decision") {
      const cx = nodeLayout.x + nodeLayout.width / 2;
      const cy = nodeLayout.y + nodeLayout.height / 2;
      const rx = nodeLayout.width / 2;
      const ry = nodeLayout.height / 2;
      // 菱形顶点：上、右、下、左
      const points = `${cx},${nodeLayout.y} ${nodeLayout.x + nodeLayout.width},${cy} ${cx},${nodeLayout.y + nodeLayout.height} ${nodeLayout.x},${cy}`;
      svg.appendChild(createSvgElement("polygon", {
        points,
        class: buildNodeClass(node.type)
      }));
    } else {
      svg.appendChild(createSvgElement("rect", {
        x: nodeLayout.x,
        y: nodeLayout.y,
        width: nodeLayout.width,
        height: nodeLayout.height,
        rx: 16,
        class: buildNodeClass(node.type)
      }));
    }

    const outputText = [];
    const nodeArtifacts = [];
    if (Array.isArray(node.outputIds) && Array.isArray(data.artifacts)) {
      node.outputIds.forEach(outputId => {
        const artifact = data.artifacts.find(item => item.id === outputId);
        if (artifact) {
          outputText.push(getLocalizedText(artifact.name, locale, fallbackLocale));
          nodeArtifacts.push(artifact);
        }
      });
    }

    if (Array.isArray(node.outputs)) {
      node.outputs.forEach(output => {
        outputText.push(getLocalizedText(output, locale, fallbackLocale));
      });
    }

    svg.appendChild(createForeignText(
      nodeLayout.x + 12,
      nodeLayout.y + 10,
      nodeLayout.width - 24,
      nodeLayout.height - 20,
      "swimlane-node-content",
      `
        <div class="swimlane-node-title">${escapeHtml(getLocalizedText(node.title, locale, fallbackLocale))}</div>
        ${outputText.length ? `<div class="swimlane-node-output">${escapeHtml(outputText.join(locale === "en-US" ? " / " : " / "))}</div>` : ""}
      `
    ));

    // 渲染产出物图标（在节点右侧）
    if (nodeArtifacts.length > 0) {
      const iconGroupX = nodeLayout.x + nodeLayout.width - 8;
      const iconGroupY = nodeLayout.y + nodeLayout.height / 2 - 10;
      const iconGroup = createArtifactIconGroup(nodeArtifacts, iconGroupX, iconGroupY, locale, fallbackLocale);
      svg.appendChild(iconGroup);
    }
  });

  scroller.appendChild(svg);
  wrapper.appendChild(scroller);
  container.appendChild(wrapper);

  return {
    locale,
    width: layout.width,
    height: layout.height
  };
}

export { renderSwimlaneDiagram, getLocalizedText };
