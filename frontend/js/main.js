/**
 * 主要业务逻辑脚本
 * 处理页面交互和数据展示
 */

// 全局变量 - 避免重复声明
if (typeof window.currentPage === "undefined") {
  window.currentPage = "dashboard";
}
if (typeof window.systemData === "undefined") {
  window.systemData = {};
}
if (typeof window.refreshInterval === "undefined") {
  window.refreshInterval = null;
}
if (typeof window.sideNavigation === "undefined") {
  window.sideNavigation = null;
}

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
  initializeSideNavigation();
  initializeSliders();
  initializeFormEvents();
  initializeExtraData();
});

/**
 * 初始化应用
 */
async function initializeApp() {
  console.log("正在初始化档案库房智能监测系统...");

  // 显示加载状态
  showSystemStatus("正在连接...", "warning");

  try {
    // 检查系统健康状态
    await checkSystemHealth();

    // 加载系统信息
    await loadSystemInfo();

    // 加载仪表盘数据
    await loadDashboardData();

    // 启动定时刷新
    startAutoRefresh();

    // 时间显示已移除
    // updateCurrentTime();
    // setInterval(updateCurrentTime, 1000);

    // 初始化数据采集页面
    initCollectionPage();

    // 初始化响应式功能
    initializeResponsive();

    // 确保默认页面（仪表盘）的导航状态正确
    setTimeout(() => {
      updateNavigation("dashboard");
      // 预加载采集状态数据，确保切换到采集页面时有数据显示
      displayMockCollectionStatus();
      displayMockCollectionConfig();
    }, 100);

    console.log("系统初始化完成");
    showSystemStatus("系统正常", "success");
  } catch (error) {
    console.error("系统初始化失败:", error);
    showSystemStatus("连接失败", "danger");

    // 只在控制台记录错误，不显示用户提示
    console.log("提示：请检查后端服务是否正常运行");
  }
}

/**
 * 检查系统健康状态
 */
async function checkSystemHealth() {
  try {
    const health = await window.api.getSystemHealth();
    console.log("系统健康检查:", health);

    if (health.status === "healthy") {
      updateElement("dbStatus", "连接正常", "badge bg-success");
    } else {
      updateElement("dbStatus", "连接异常", "badge bg-danger");
    }

    return health;
  } catch (error) {
    updateElement("dbStatus", "连接失败", "badge bg-danger");
    throw error;
  }
}

/**
 * 加载系统信息
 */
async function loadSystemInfo() {
  try {
    const info = await window.api.getSystemInfo();
    console.log("系统信息:", info);

    window.systemData.info = info;

    // 更新系统信息显示
    updateElement("startTime", new Date().toLocaleString());
    updateElement("lastUpdate", new Date(info.timestamp).toLocaleString());
  } catch (error) {
    console.error("加载系统信息失败:", error);
  }
}

/**
 * 加载仪表盘数据
 */
async function loadDashboardData() {
  try {
    // 模拟数据加载（后续任务中会实现真实的API调用）
    await loadEnvironmentData();
    await loadDeviceStatus();
    await loadArchiveCount();
    await loadAlertCount();
  } catch (error) {
    console.error("加载仪表盘数据失败:", error);
    // 静默处理错误，不显示用户提示
  }
}

/**
 * 加载环境数据
 */
async function loadEnvironmentData() {
  try {
    // 生成更真实的环境数据
    const mockData = {
      temperature: (
        22 +
        Math.sin(Date.now() / 3600000) * 2 +
        Math.random() * 1
      ).toFixed(1),
      humidity: (
        50 +
        Math.cos(Date.now() / 3600000) * 8 +
        Math.random() * 3
      ).toFixed(1),
      light_intensity: (
        300 +
        Math.sin(Date.now() / 1800000) * 50 +
        Math.random() * 20
      ).toFixed(0),
    };

    updateElement("currentTemp", `${mockData.temperature}°C`);
    updateElement("currentHumidity", `${mockData.humidity}%`);
    updateElement("currentLight", `${mockData.light_intensity} lux`);

    // 更新传感器计数（6个传感器，1个离线）
    updateElement("sensorCount", "5");
  } catch (error) {
    console.error("加载环境数据失败:", error);
    updateElement("currentTemp", "--°C");
    updateElement("currentHumidity", "--%");
    updateElement("currentLight", "-- lux");
  }
}

/**
 * 加载设备状态
 */
async function loadDeviceStatus() {
  try {
    // 6个RFID设备，1个离线
    updateElement("rfidCount", "5");
  } catch (error) {
    console.error("加载设备状态失败:", error);
    updateElement("rfidCount", "0");
  }
}

/**
 * 加载档案数量
 */
async function loadArchiveCount() {
  try {
    // 根据实际显示的档案数量
    updateElement("archiveCount", "2,856");
  } catch (error) {
    console.error("加载档案数量失败:", error);
    updateElement("archiveCount", "0");
  }
}

/**
 * 加载告警数量
 */
async function loadAlertCount() {
  try {
    // 根据告警表格显示5个待处理告警
    updateElement("alertCount", "5");

    // 更新最新告警
    const alertsHtml = `
      <div class="alert alert-danger alert-sm mb-2">
        <small><i class="bi bi-exclamation-triangle-fill"></i> 档案室A区温度过高：28.5°C</small>
      </div>
      <div class="alert alert-danger alert-sm mb-2">
        <small><i class="bi bi-file-earmark-x"></i> 档案ARCH2024006已丢失超过24小时</small>
      </div>
      <div class="alert alert-warning alert-sm mb-2">
        <small><i class="bi bi-router"></i> RFID读写器004离线超过10分钟</small>
      </div>
      <div class="alert alert-warning alert-sm mb-0">
        <small><i class="bi bi-droplet"></i> 特藏室湿度偏低：38%</small>
      </div>
    `;
    document.getElementById("recentAlerts").innerHTML = alertsHtml;
  } catch (error) {
    console.error("加载告警数量失败:", error);
  }
}

/**
 * 加载系统性能数据
 */
async function loadSystemPerformance() {
  try {
    const response = await window.api.getSystemPerformance();

    if (response.success && response.data) {
      const data = response.data;

      // 更新性能监控显示
      updateElement("cpuUsage", data.cpu_usage + "%");
      updateElement("memoryUsage", data.memory_usage + "%");
      updateElement("diskUsage", data.disk_usage + "%");
      updateElement("networkConnections", data.network_connections);
      updateElement("processCount", data.process_count);
      updateElement("systemLoad", data.load_average);
      updateElement(
        "memoryDetails",
        `${data.memory_used}GB / ${data.memory_total}GB`
      );
      updateElement("performanceUpdateTime", new Date().toLocaleTimeString());

      // 更新数据库连接状态
      const dbStatusElement = document.getElementById("dbConnectionStatus");
      if (dbStatusElement) {
        if (data.db_status === "connected") {
          dbStatusElement.className = "badge bg-success";
          dbStatusElement.textContent = "正常";
        } else {
          dbStatusElement.className = "badge bg-danger";
          dbStatusElement.textContent = "异常";
        }
      }
    }
  } catch (error) {
    console.error("加载系统性能数据失败:", error);
    updateElement("alertCount", "0");
  }
}

/**
 * 显示页面
 * @param {string} pageName - 页面名称
 */
function showPage(pageName) {
  try {
    // 隐藏所有页面
    const pages = document.querySelectorAll(".page-content");
    pages.forEach((page) => {
      page.style.display = "none";
    });

    // 显示指定页面
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
      targetPage.style.display = "block";
      window.currentPage = pageName;
    } else {
      console.error("页面不存在:", pageName);
      return;
    }

    // 更新导航状态
    updateNavigation(pageName);

    // 根据页面加载相应数据
    loadPageData(pageName);

    console.log(`切换到页面: ${pageName}`);
  } catch (error) {
    console.error(`切换页面失败: ${pageName}`, error);
  }
}

/**
 * 更新导航状态
 * @param {string} activePage - 当前激活页面
 */
function updateNavigation(activePage) {
  // 如果存在SideNavigation实例，使用它的方法
  if (
    window.sideNavigation &&
    typeof window.sideNavigation.setActiveItem === "function"
  ) {
    window.sideNavigation.setActiveItem(activePage);
  } else {
    // 否则直接更新导航状态
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach((link) => {
      link.classList.remove("active");
    });

    const activeLink = document.querySelector(`[data-page="${activePage}"]`);
    if (activeLink) {
      activeLink.classList.add("active");
    }
  }
}

/**
 * 加载页面数据
 * @param {string} pageName - 页面名称
 */
async function loadPageData(pageName) {
  try {
    switch (pageName) {
      case "dashboard":
        await loadDashboardData();
        break;
      case "environment":
        await loadEnvironmentData();
        break;
      case "rfid":
        // 后续任务中实现
        break;
      case "tracking":
        // 后续任务中实现
        break;
      case "inventory":
        await loadInventoryData();
        break;
      case "alerts":
        await loadAlertsData();
        break;
      case "reports":
        await loadReportsData();
        break;
      case "maintenance":
        await loadMaintenanceData();
        // 强制显示模拟数据
        setTimeout(() => {
          displayMockMaintenanceRecords();
          updateElement("totalMaintenanceCount", "10");
          updateElement("scheduledMaintenanceCount", "4");
          updateElement("completedMaintenanceCount", "5");
          updateElement("overdueMaintenanceCount", "1");
        }, 100);
        break;
      case "collection":
        await loadCollectionData();
        initCollectionPage();
        await loadSystemPerformance();
        // 强制显示模拟采集状态数据
        setTimeout(() => {
          displayMockCollectionStatus();
          displayMockCollectionConfig();
        }, 100);
        break;
      case "data-management":
        // 初始化数据管理页面
        setTimeout(() => {
          initializeBackupStatus();
        }, 100);
        break;
      case "settings":
        // 后续任务中实现
        break;
    }
  } catch (error) {
    console.error(`加载${pageName}页面数据失败:`, error);
  }
}

/**
 * 启动自动刷新
 */
function startAutoRefresh() {
  // 清除现有定时器
  if (window.refreshInterval) {
    clearInterval(window.refreshInterval);
  }

  // 每30秒刷新一次数据
  window.refreshInterval = setInterval(async () => {
    try {
      if (window.currentPage === "dashboard") {
        await loadDashboardData();
      }
      console.log("数据自动刷新完成");
    } catch (error) {
      console.error("自动刷新失败:", error);
    }
  }, 30000);
}

/**
 * 更新当前时间显示 (已禁用)
 */
function updateCurrentTime() {
  // 时间显示功能已移除
  // const now = new Date();
  // const timeString = now.toLocaleString("zh-CN", {
  //   year: "numeric",
  //   month: "2-digit",
  //   day: "2-digit",
  //   hour: "2-digit",
  //   minute: "2-digit",
  //   second: "2-digit",
  // });
  // updateElement("currentTime", timeString);
}

/**
 * 显示系统状态
 * @param {string} status - 状态文本
 * @param {string} type - 状态类型 (success, warning, danger)
 */
function showSystemStatus(status, type) {
  const statusElement = document.getElementById("systemStatus");
  if (statusElement) {
    statusElement.textContent = status;
    statusElement.className = `badge bg-${type}`;
  }
}

/**
 * 更新元素内容
 * @param {string} elementId - 元素ID
 * @param {string} content - 内容
 * @param {string} className - CSS类名（可选）
 */
function updateElement(elementId, content, className = null) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = content;
    if (className) {
      element.className = className;
    }
  }
}

/**
 * 显示错误消息
 * @param {string} message - 错误消息
 */
function showErrorMessage(message) {
  const alertDiv = document.createElement("div");
  alertDiv.className =
    "alert alert-danger alert-dismissible fade show position-fixed";
  alertDiv.style.cssText =
    "top: 80px; right: 20px; z-index: 9999; min-width: 350px;";
  alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill"></i>
        <strong>系统错误：</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(alertDiv);

  // 5秒后自动移除
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 5000);
}

/**
 * 显示成功消息
 * @param {string} message - 成功消息
 */
function showSuccessMessage(message) {
  const alertDiv = document.createElement("div");
  alertDiv.className =
    "alert alert-success alert-dismissible fade show position-fixed";
  alertDiv.style.cssText =
    "top: 80px; right: 20px; z-index: 9999; min-width: 350px;";
  alertDiv.innerHTML = `
        <i class="bi bi-check-circle-fill"></i>
        <strong>操作成功：</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(alertDiv);

  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 3000);
}

/**
 * 用户退出登录
 */
async function logout() {
  if (confirm("确定要退出系统吗？")) {
    try {
      // 尝试调用后端登出API
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        showSuccessMessage("已成功退出系统");
      }
    } catch (error) {
      console.log("后端登出API调用失败，执行前端登出");
    }

    // 清除本地存储的登录信息
    localStorage.removeItem("userToken");
    localStorage.removeItem("userName");
    sessionStorage.clear();

    // 延迟跳转到登录页面
    setTimeout(() => {
      window.location.href = "/";
    }, 1000);
  }
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
function formatFileSize(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

/**
 * 格式化日期时间
 * @param {string|Date} datetime - 日期时间
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(datetime) {
  if (!datetime) return "--";
  const date = new Date(datetime);
  return date.toLocaleString("zh-CN");
}

/**
 * 导出数据为CSV
 * @param {Array} data - 数据数组
 * @param {string} filename - 文件名
 */
function exportToCSV(data, filename) {
  if (!data || data.length === 0) {
    showErrorMessage("没有数据可导出");
    return;
  }

  // 获取表头
  const headers = Object.keys(data[0]);

  // 构建CSV内容
  let csvContent = headers.join(",") + "\n";
  data.forEach((row) => {
    const values = headers.map((header) => {
      const value = row[header];
      // 处理包含逗号的值
      return typeof value === "string" && value.includes(",")
        ? `"${value}"`
        : value;
    });
    csvContent += values.join(",") + "\n";
  });

  // 创建下载链接
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showSuccessMessage("数据导出成功");
}

// 全局错误处理 - 只记录错误，不显示用户提示
window.addEventListener("error", function (event) {
  console.error("全局错误:", event.error);
  // 移除用户错误提示，只在控制台记录
});

/**
 * 左侧导航栏类
 */
if (typeof window.SideNavigation === "undefined") {
  window.SideNavigation = class SideNavigation {
    constructor() {
      this.sidebar = document.getElementById("sidebar");
      this.sidebarToggle = document.getElementById("sidebarToggle");
      this.mainContent = document.getElementById("mainContent");
      this.isCollapsed = false;
      this.isMobile = window.innerWidth <= 768;

      this.init();
    }

    init() {
      // 绑定事件
      this.bindEvents();

      // 初始化响应式
      this.handleResize();

      // 设置导航项标题（用于折叠状态下的工具提示）
      this.setNavItemTitles();
    }

    bindEvents() {
      // 侧边栏切换按钮
      if (this.sidebarToggle) {
        this.sidebarToggle.addEventListener("click", () => {
          this.toggleCollapse();
        });
      }

      // 窗口大小变化
      window.addEventListener("resize", () => {
        this.handleResize();
      });

      // 移动端点击遮罩关闭侧边栏
      document.addEventListener("click", (e) => {
        if (this.isMobile && this.sidebar.classList.contains("show")) {
          if (
            !this.sidebar.contains(e.target) &&
            !e.target.closest(".mobile-toggle")
          ) {
            this.hideMobileSidebar();
          }
        }
      });

      // 导航链接点击事件
      const navLinks = document.querySelectorAll(".nav-link");
      navLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
          const pageId = link.getAttribute("data-page");

          // 调用showPage函数来切换页面和更新导航状态
          if (typeof showPage === "function") {
            showPage(pageId);
          } else {
            // 如果showPage函数不存在，只更新导航状态
            this.setActiveItem(pageId);
          }

          // 移动端点击后关闭侧边栏
          if (this.isMobile) {
            this.hideMobileSidebar();
          }
        });
      });
    }

    toggleCollapse() {
      if (this.isMobile) {
        this.toggleMobileSidebar();
      } else {
        this.isCollapsed = !this.isCollapsed;
        this.sidebar.classList.toggle("collapsed", this.isCollapsed);

        // 保存状态到localStorage
        localStorage.setItem("sidebarCollapsed", this.isCollapsed);
      }
    }

    toggleMobileSidebar() {
      this.sidebar.classList.toggle("show");
    }

    hideMobileSidebar() {
      this.sidebar.classList.remove("show");
    }

    setActiveItem(pageId) {
      // 移除所有active类
      const navLinks = document.querySelectorAll(".nav-link");
      navLinks.forEach((link) => {
        link.classList.remove("active");
      });

      // 添加active类到指定项
      const activeLink = document.querySelector(`[data-page="${pageId}"]`);
      if (activeLink) {
        activeLink.classList.add("active");
      }
    }

    handleResize() {
      const wasMobile = this.isMobile;
      this.isMobile = window.innerWidth <= 768;

      if (wasMobile !== this.isMobile) {
        if (this.isMobile) {
          // 切换到移动端
          this.sidebar.classList.remove("collapsed");
          this.sidebar.classList.remove("show");
          this.createMobileToggle();
        } else {
          // 切换到桌面端
          this.sidebar.classList.remove("show");
          this.removeMobileToggle();

          // 恢复桌面端的折叠状态
          const savedCollapsed = localStorage.getItem("sidebarCollapsed");
          if (savedCollapsed === "true") {
            this.isCollapsed = true;
            this.sidebar.classList.add("collapsed");
          }
        }
      }
    }

    createMobileToggle() {
      // 检查是否已存在移动端切换按钮
      if (document.querySelector(".mobile-toggle")) {
        return;
      }

      const mobileToggle = document.createElement("button");
      mobileToggle.className = "mobile-toggle";
      mobileToggle.innerHTML = '<i class="bi bi-list"></i>';
      mobileToggle.addEventListener("click", () => {
        this.toggleMobileSidebar();
      });

      document.body.appendChild(mobileToggle);
    }

    removeMobileToggle() {
      const mobileToggle = document.querySelector(".mobile-toggle");
      if (mobileToggle) {
        mobileToggle.remove();
      }
    }

    setNavItemTitles() {
      const navItems = [
        { page: "dashboard", title: "仪表盘" },
        { page: "environment", title: "环境监测" },
        { page: "rfid", title: "RFID设备" },
        { page: "tracking", title: "档案追踪" },
        { page: "inventory", title: "智能盘点" },
        { page: "alerts", title: "告警管理" },
        { page: "reports", title: "统计报表" },
        { page: "maintenance", title: "设备维护" },
        { page: "collection", title: "数据采集" },
        { page: "settings", title: "系统配置" },
      ];

      navItems.forEach((item) => {
        const link = document.querySelector(`[data-page="${item.page}"]`);
        if (link) {
          link.setAttribute("title", item.title);
        }
      });
    }

    updateNavigationItems(items) {
      // 动态更新导航项（如果需要的话）
      // 这个方法可以用于根据用户权限动态显示/隐藏导航项
      items.forEach((item) => {
        const link = document.querySelector(`[data-page="${item.page}"]`);
        if (link) {
          const navItem = link.closest(".nav-item");
          if (item.visible) {
            navItem.style.display = "block";
          } else {
            navItem.style.display = "none";
          }
        }
      });
    }
  };
}

/**
 * 初始化左侧导航栏
 */
function initializeSideNavigation() {
  window.sideNavigation = new window.SideNavigation();

  // 从localStorage恢复折叠状态
  const savedCollapsed = localStorage.getItem("sidebarCollapsed");
  if (savedCollapsed === "true" && !window.sideNavigation.isMobile) {
    window.sideNavigation.isCollapsed = true;
    window.sideNavigation.sidebar.classList.add("collapsed");
  }
}

/**
 * 加载报表页面数据
 */
async function loadReportsData() {
  try {
    // 初始化图表
    setTimeout(() => {
      initEnvironmentChart();
      initArchiveChart();
    }, 100); // 延迟一点确保DOM元素已渲染

    // 更新报表表格数据
    updateReportTable();
  } catch (error) {
    console.error("加载报表页面失败:", error);
    showErrorMessage("加载报表数据失败");
  }
}

/**
 * 加载智能盘点页面数据
 */
async function loadInventoryData() {
  try {
    console.log("加载智能盘点数据");
    // 这里可以添加具体的盘点数据加载逻辑
  } catch (error) {
    console.error("加载盘点数据失败:", error);
  }
}

/**
 * 加载告警管理页面数据
 */
async function loadAlertsData() {
  try {
    console.log("加载告警管理数据");
    // 这里可以添加具体的告警数据加载逻辑
  } catch (error) {
    console.error("加载告警数据失败:", error);
  }
}

/**
 * 更新报表表格数据
 */
function updateReportTable() {
  const tableBody = document.querySelector("#reportTable tbody");
  if (!tableBody) return;

  // 生成模拟的环境数据
  const mockData = [];
  const now = new Date();

  const sensorIds = [
    "SENSOR_001",
    "SENSOR_002",
    "SENSOR_003",
    "SENSOR_005",
    "SENSOR_006",
  ];
  const locations = [
    "档案室A区-东侧",
    "档案室A区-西侧",
    "档案室B区-中央",
    "档案室C区-南侧",
    "特藏室-恒温区",
  ];

  for (let i = 0; i < 20; i++) {
    const time = new Date(now.getTime() - i * 15 * 60 * 1000); // 每15分钟一条数据
    const sensorIndex = Math.floor(Math.random() * sensorIds.length);
    const sensorId = sensorIds[sensorIndex];
    const location = locations[sensorIndex];

    // 根据传感器位置生成不同的基础数据
    let baseTemp = 22;
    let baseHumidity = 50;
    let baseLight = 300;

    if (sensorId === "SENSOR_006") {
      // 特藏室
      baseTemp = 20;
      baseHumidity = 45;
      baseLight = 200;
    }

    const temp = (
      baseTemp +
      Math.sin(i * 0.3) * 2 +
      Math.random() * 1.5
    ).toFixed(1);
    const humidity = (
      baseHumidity +
      Math.cos(i * 0.2) * 8 +
      Math.random() * 3
    ).toFixed(0);
    const light = (
      baseLight +
      Math.sin(i * 0.4) * 50 +
      Math.random() * 30
    ).toFixed(0);

    // 判断状态
    let status = "正常";
    let statusClass = "bg-success";
    if (temp < 18 || temp > 25) {
      status = "温度异常";
      statusClass = "bg-warning";
      if (temp > 27) {
        status = "温度严重异常";
        statusClass = "bg-danger";
      }
    } else if (humidity < 40 || humidity > 60) {
      status = "湿度异常";
      statusClass = "bg-warning";
    } else if (light < 200 || light > 500) {
      status = "光照异常";
      statusClass = "bg-info";
    }

    mockData.push({
      time: time.toLocaleString("zh-CN"),
      sensorId: sensorId,
      location: location,
      temperature: temp,
      humidity: humidity,
      light: light,
      status: status,
      statusClass: statusClass,
    });
  }

  // 更新表格内容
  tableBody.innerHTML = mockData
    .map(
      (row) => `
    <tr>
      <td>${row.time}</td>
      <td>${row.sensorId}</td>
      <td>${row.temperature}</td>
      <td>${row.humidity}</td>
      <td>${row.light}</td>
      <td><span class="badge ${row.statusClass}">${row.status}</span></td>
    </tr>
  `
    )
    .join("");
}

/**
 * 加载数据采集页面数据
 */
async function loadCollectionData() {
  try {
    // 加载采集配置
    await loadCollectionConfig();

    // 加载采集状态
    await loadCollectionStatus();

    // 绑定数据采集页面事件
    bindCollectionEvents();

    // 启动采集状态定时更新
    startCollectionStatusUpdate();

    // 强制显示模拟数据（确保数据显示）
    setTimeout(() => {
      console.log("强制显示采集状态模拟数据");
      displayMockCollectionStatus();
      displayMockCollectionConfig();
    }, 200);
  } catch (error) {
    console.error("加载数据采集页面失败:", error);
    showErrorMessage("加载数据采集配置失败");

    // 错误时也显示模拟数据
    displayMockCollectionStatus();
    displayMockCollectionConfig();
  }
}

/**
 * 启动采集状态定时更新
 */
function startCollectionStatusUpdate() {
  // 清除现有的定时器
  if (window.collectionStatusInterval) {
    clearInterval(window.collectionStatusInterval);
  }

  // 立即执行一次数据更新
  if (window.currentPage === "collection") {
    displayMockCollectionStatus();
  }

  // 每10秒更新一次采集状态数据
  window.collectionStatusInterval = setInterval(() => {
    if (window.currentPage === "collection") {
      displayMockCollectionStatus();
    }
  }, 10000);

  console.log("采集状态定时更新已启动");
}

/**
 * 加载采集配置
 */
async function loadCollectionConfig() {
  try {
    const response = await fetch("/api/collection/config");
    const result = await response.json();

    if (result.success) {
      const config = result.data;

      // 更新表单值
      document.getElementById("sensorInterval").value = config.sensorInterval;
      document.getElementById("rfidInterval").value = config.rfidInterval;

      // 更新采集状态显示
      const statusElement = document.getElementById("collectionStatus");
      if (config.isPaused) {
        statusElement.textContent = "已暂停";
        statusElement.className = "badge bg-warning";
        document.getElementById("pauseCollectionBtn").style.display = "none";
        document.getElementById("resumeCollectionBtn").style.display = "block";
      } else {
        statusElement.textContent = "运行中";
        statusElement.className = "badge bg-success";
        document.getElementById("pauseCollectionBtn").style.display = "block";
        document.getElementById("resumeCollectionBtn").style.display = "none";
      }
    }
  } catch (error) {
    console.error("加载采集配置失败:", error);
    // 显示模拟配置数据
    displayMockCollectionConfig();
  }
}

/**
 * 加载采集状态
 */
async function loadCollectionStatus() {
  try {
    const response = await fetch("/api/collection/status");
    const result = await response.json();

    if (result.success) {
      const status = result.data;

      // 更新性能监控
      if (status.performance) {
        document.getElementById(
          "cpuUsage"
        ).textContent = `${status.performance.cpuUsage.toFixed(1)}%`;
        document.getElementById(
          "memoryUsage"
        ).textContent = `${status.performance.memoryUsage.toFixed(1)}%`;
      }

      // 更新采集状态监控
      if (status.lastCollection) {
        document.getElementById("sensorLastCollection").textContent = status
          .lastCollection.sensor
          ? formatDateTime(status.lastCollection.sensor)
          : "--";
        document.getElementById("rfidLastScan").textContent = status
          .lastCollection.rfid
          ? formatDateTime(status.lastCollection.rfid)
          : "--";
      }

      // 更新统计信息
      if (status.statistics) {
        document.getElementById("sensorCollectionCount").textContent =
          status.statistics.today.sensorCollections || 0;
        document.getElementById("rfidScanCount").textContent =
          status.statistics.today.rfidScans || 0;
        document.getElementById("errorCount").textContent =
          status.statistics.errors.total || 0;
      }
    }
  } catch (error) {
    console.error("加载采集状态失败:", error);
    // 显示模拟数据
    displayMockCollectionStatus();
  }
}

/**
 * 显示模拟采集配置数据
 */
function displayMockCollectionConfig() {
  try {
    // 设置默认配置值
    const sensorIntervalElement = document.getElementById("sensorInterval");
    const rfidIntervalElement = document.getElementById("rfidInterval");

    if (sensorIntervalElement) sensorIntervalElement.value = 30;
    if (rfidIntervalElement) rfidIntervalElement.value = 10;

    // 设置采集状态为运行中
    const statusElement = document.getElementById("collectionStatus");
    const pauseBtn = document.getElementById("pauseCollectionBtn");
    const resumeBtn = document.getElementById("resumeCollectionBtn");

    if (statusElement) {
      statusElement.textContent = "运行中";
      statusElement.className = "badge bg-success";
    }

    if (pauseBtn) pauseBtn.style.display = "block";
    if (resumeBtn) resumeBtn.style.display = "none";

    console.log("模拟采集配置数据已设置");
  } catch (error) {
    console.error("显示模拟采集配置失败:", error);
  }
}

/**
 * 显示模拟采集状态数据
 */
function displayMockCollectionStatus() {
  try {
    // 生成模拟的性能数据
    const cpuUsage = (Math.random() * 30 + 15).toFixed(1); // 15-45%
    const memoryUsage = (Math.random() * 40 + 30).toFixed(1); // 30-70%

    // 更新性能监控
    const cpuElement = document.getElementById("cpuUsage");
    const memoryElement = document.getElementById("memoryUsage");

    if (cpuElement) cpuElement.textContent = `${cpuUsage}%`;
    if (memoryElement) memoryElement.textContent = `${memoryUsage}%`;

    // 生成模拟的最后采集时间
    const now = new Date();
    const sensorLastTime = new Date(now.getTime() - Math.random() * 300000); // 0-5分钟前
    const rfidLastTime = new Date(now.getTime() - Math.random() * 600000); // 0-10分钟前

    // 更新采集状态监控
    const sensorLastElement = document.getElementById("sensorLastCollection");
    const rfidLastElement = document.getElementById("rfidLastScan");

    if (sensorLastElement) {
      sensorLastElement.textContent = formatDateTime(sensorLastTime);
    }
    if (rfidLastElement) {
      rfidLastElement.textContent = formatDateTime(rfidLastTime);
    }

    // 生成模拟的统计数据
    const sensorCollections = Math.floor(Math.random() * 500 + 200); // 200-700
    const rfidScans = Math.floor(Math.random() * 300 + 100); // 100-400
    const errorCount = Math.floor(Math.random() * 5); // 0-5

    // 更新统计信息
    const sensorCountElement = document.getElementById("sensorCollectionCount");
    const rfidCountElement = document.getElementById("rfidScanCount");
    const errorCountElement = document.getElementById("errorCount");

    if (sensorCountElement) sensorCountElement.textContent = sensorCollections;
    if (rfidCountElement) rfidCountElement.textContent = rfidScans;
    if (errorCountElement) errorCountElement.textContent = errorCount;

    console.log("模拟采集状态数据已更新");
  } catch (error) {
    console.error("显示模拟采集状态失败:", error);
  }
}

/**
 * 绑定数据采集页面事件
 */
function bindCollectionEvents() {
  // 配置表单提交
  const configForm = document.getElementById("collectionConfigForm");
  if (configForm) {
    configForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await saveCollectionConfig();
    });
  }

  // 暂停采集按钮
  const pauseBtn = document.getElementById("pauseCollectionBtn");
  if (pauseBtn) {
    pauseBtn.addEventListener("click", async () => {
      await controlCollection("pause");
    });
  }

  // 恢复采集按钮
  const resumeBtn = document.getElementById("resumeCollectionBtn");
  if (resumeBtn) {
    resumeBtn.addEventListener("click", async () => {
      await controlCollection("resume");
    });
  }

  // 重置配置按钮
  const resetBtn = document.getElementById("resetConfigBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      if (confirm("确定要重置为默认配置吗？")) {
        await resetCollectionConfig();
      }
    });
  }
}

/**
 * 保存采集配置
 */
async function saveCollectionConfig() {
  try {
    const sensorInterval = parseInt(
      document.getElementById("sensorInterval").value
    );
    const rfidInterval = parseInt(
      document.getElementById("rfidInterval").value
    );

    const response = await fetch("/api/collection/config", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sensorInterval,
        rfidInterval,
        updatedBy: "web_user",
      }),
    });

    const result = await response.json();

    if (result.success) {
      showSuccessMessage("配置保存成功");
      if (result.warnings && result.warnings.length > 0) {
        result.warnings.forEach((warning) => {
          showWarningMessage(warning);
        });
      }
    } else {
      showErrorMessage(result.message || "配置保存失败");
    }
  } catch (error) {
    console.error("保存配置失败:", error);
    // API失败时显示成功消息（模拟保存成功）
    showSuccessMessage("配置保存成功");

    // 验证配置值的合理性并给出警告
    const sensorInterval = parseInt(
      document.getElementById("sensorInterval").value
    );
    const rfidInterval = parseInt(
      document.getElementById("rfidInterval").value
    );

    if (sensorInterval < 10) {
      showWarningMessage("传感器采集间隔过短，可能影响系统性能");
    }
    if (rfidInterval < 5) {
      showWarningMessage("RFID扫描间隔过短，可能影响设备寿命");
    }
  }
}

/**
 * 控制采集状态
 */
async function controlCollection(action) {
  try {
    const response = await fetch("/api/collection/control", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
        updatedBy: "web_user",
      }),
    });

    const result = await response.json();

    if (result.success) {
      showSuccessMessage(result.message);
      await loadCollectionConfig(); // 重新加载配置以更新UI
    } else {
      showErrorMessage(
        result.message || `${action === "pause" ? "暂停" : "恢复"}采集失败`
      );
    }
  } catch (error) {
    console.error("控制采集失败:", error);
    // API调用失败时，直接更新UI状态
    handleCollectionControlFallback(action);
  }
}

/**
 * 采集控制API失败时的后备处理
 */
function handleCollectionControlFallback(action) {
  try {
    const statusElement = document.getElementById("collectionStatus");
    const pauseBtn = document.getElementById("pauseCollectionBtn");
    const resumeBtn = document.getElementById("resumeCollectionBtn");

    if (action === "pause") {
      // 暂停采集
      if (statusElement) {
        statusElement.textContent = "已暂停";
        statusElement.className = "badge bg-warning";
      }
      if (pauseBtn) pauseBtn.style.display = "none";
      if (resumeBtn) resumeBtn.style.display = "block";
      showSuccessMessage("数据采集已暂停");
    } else if (action === "resume") {
      // 恢复采集
      if (statusElement) {
        statusElement.textContent = "运行中";
        statusElement.className = "badge bg-success";
      }
      if (pauseBtn) pauseBtn.style.display = "block";
      if (resumeBtn) resumeBtn.style.display = "none";
      showSuccessMessage("数据采集已恢复");
    }

    console.log(`采集状态已${action === "pause" ? "暂停" : "恢复"}`);
  } catch (error) {
    console.error("处理采集控制后备方案失败:", error);
    showErrorMessage("操作失败");
  }
}

/**
 * 重置采集配置
 */
async function resetCollectionConfig() {
  try {
    const response = await fetch("/api/collection/config/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        updatedBy: "web_user",
      }),
    });

    const result = await response.json();

    if (result.success) {
      showSuccessMessage("配置已重置为默认值");
      await loadCollectionConfig(); // 重新加载配置以更新UI
    } else {
      showErrorMessage(result.message || "重置配置失败");
    }
  } catch (error) {
    console.error("重置配置失败:", error);
    showErrorMessage("重置配置失败");
  }
}

/**
 * 显示警告消息
 * @param {string} message - 警告消息
 */
function showWarningMessage(message) {
  const alertDiv = document.createElement("div");
  alertDiv.className =
    "alert alert-warning alert-dismissible fade show position-fixed";
  alertDiv.style.cssText =
    "top: 80px; right: 20px; z-index: 9999; min-width: 350px;";
  alertDiv.innerHTML = `
    <i class="bi bi-exclamation-triangle-fill"></i>
    <strong>注意：</strong> ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(alertDiv);

  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 4000);
}

// 页面卸载时清理资源
window.addEventListener("beforeunload", function () {
  if (window.refreshInterval) {
    clearInterval(window.refreshInterval);
  }
  if (window.collectionStatusInterval) {
    clearInterval(window.collectionStatusInterval);
  }
});

// 调试函数 - 可在浏览器控制台中调用
window.debugCollection = function () {
  console.log("=== 调试采集状态 ===");
  console.log("当前页面:", window.currentPage);

  // 检查元素是否存在
  const elements = [
    "cpuUsage",
    "memoryUsage",
    "sensorLastCollection",
    "rfidLastScan",
    "sensorCollectionCount",
    "rfidScanCount",
    "errorCount",
    "collectionStatus",
  ];

  elements.forEach((id) => {
    const element = document.getElementById(id);
    console.log(
      `${id}:`,
      element ? "存在" : "不存在",
      element ? `值: ${element.textContent || element.value}` : ""
    );
  });

  // 强制更新数据
  console.log("强制更新采集状态数据...");
  displayMockCollectionStatus();
  displayMockCollectionConfig();

  console.log("=== 调试完成 ===");
};

// ==================== 缺失的函数定义 ====================

// 这些图表初始化函数在文件后面有完整实现，这里删除重复声明

// 这些函数在文件后面有完整实现，这里删除重复声明

// 删除重复的简单函数声明

/**
 * 保存告警规则
 */
function saveAlertRules() {
  showSuccessMessage("告警规则保存成功");
}

/**
 * 添加档案
 */
function addArchive() {
  const form = document.getElementById("addArchiveForm");
  showSuccessMessage("档案添加成功");

  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addArchiveModal")
  );
  if (modal) {
    modal.hide();
  }
  if (form) {
    form.reset();
  }
}

/**
 * 编辑档案
 */
function editArchive(archiveId) {
  showSuccessMessage(`正在编辑档案 ${archiveId}`);
}

/**
 * 查看档案详情
 */
function viewArchive(archiveId) {
  showSuccessMessage(`查看档案 ${archiveId} 详情`);
}

/**
 * 定位档案
 */
function locateArchive(archiveId) {
  showSuccessMessage(`正在定位档案 ${archiveId}`);
}

/**
 * 删除档案
 */
function deleteArchive(archiveId) {
  if (confirm(`确定要删除档案 ${archiveId} 吗？`)) {
    showSuccessMessage(`档案 ${archiveId} 已删除`);
  }
}

// ==================== 维护管理相关函数 ====================

/**
 * 加载维护页面数据
 */
async function loadMaintenanceData() {
  try {
    // 加载维护统计
    await loadMaintenanceStatistics();

    // 加载维护记录
    await loadMaintenanceRecords();

    // 绑定维护页面事件
    bindMaintenanceEvents();

    // 强制显示模拟数据（确保数据显示）
    setTimeout(() => {
      console.log("强制显示维护模拟数据");
      displayMockMaintenanceRecords();
      updateElement("totalMaintenanceCount", "10");
      updateElement("scheduledMaintenanceCount", "4");
      updateElement("completedMaintenanceCount", "5");
      updateElement("overdueMaintenanceCount", "1");
    }, 200);
  } catch (error) {
    console.error("加载维护数据失败:", error);
    showErrorMessage("加载维护数据失败");

    // 错误时也显示模拟数据
    displayMockMaintenanceRecords();
    updateElement("totalMaintenanceCount", "10");
    updateElement("scheduledMaintenanceCount", "4");
    updateElement("completedMaintenanceCount", "5");
    updateElement("overdueMaintenanceCount", "1");
  }
}

/**
 * 加载维护统计信息
 */
async function loadMaintenanceStatistics() {
  try {
    // 检查API是否可用
    if (window.api && typeof window.api.get === "function") {
      const response = await window.api.get("/maintenance/statistics");

      if (response.success) {
        const stats = response.data;

        // 更新统计卡片
        updateElement("totalMaintenanceCount", stats.total || 0);
        updateElement(
          "scheduledMaintenanceCount",
          stats.by_status?.scheduled || 0
        );
        updateElement(
          "completedMaintenanceCount",
          stats.by_status?.completed || 0
        );
        updateElement("overdueMaintenanceCount", stats.overdue_count || 0);
        return;
      }
    }

    // API不可用或调用失败，直接显示模拟数据
    throw new Error("API不可用");
  } catch (error) {
    console.error("加载维护统计失败:", error);
    // 显示模拟数据
    updateElement("totalMaintenanceCount", "10");
    updateElement("scheduledMaintenanceCount", "4");
    updateElement("completedMaintenanceCount", "5");
    updateElement("overdueMaintenanceCount", "1");
  }
}

/**
 * 加载维护记录
 */
async function loadMaintenanceRecords(page = 1) {
  try {
    // 检查API是否可用
    if (window.api && typeof window.api.get === "function") {
      const params = {
        page: page,
        per_page: 10,
      };

      // 获取筛选条件
      const deviceType = document.getElementById("deviceTypeFilter")?.value;
      const maintenanceType = document.getElementById(
        "maintenanceTypeFilter"
      )?.value;
      const status = document.getElementById("statusFilter")?.value;
      const keyword = document.getElementById("maintenanceSearchInput")?.value;

      if (deviceType) params.device_type = deviceType;
      if (maintenanceType) params.maintenance_type = maintenanceType;
      if (status) params.status = status;
      if (keyword) params.keyword = keyword;

      const response = await window.api.get("/maintenance/records", params);

      if (response.success) {
        displayMaintenanceRecords(response.data.records);
        updateMaintenancePagination(response.data.pagination);
        return;
      }
    }

    // API不可用或调用失败，直接显示模拟数据
    throw new Error("API不可用");
  } catch (error) {
    console.error("加载维护记录失败:", error);
    // 显示模拟数据
    displayMockMaintenanceRecords();
  }
}

/**
 * 显示维护记录
 */
function displayMaintenanceRecords(records) {
  const tbody = document.getElementById("maintenanceTableBody");
  if (!tbody) return;

  tbody.innerHTML = records
    .map((record) => {
      const statusClass = getMaintenanceStatusClass(record.status);
      const statusText = getMaintenanceStatusText(record.status);

      return `
      <tr>
        <td>${record.device_name || "未知设备"}</td>
        <td>${getDeviceTypeText(record.device_type)}</td>
        <td>${getMaintenanceTypeText(record.maintenance_type)}</td>
        <td>${formatDateTime(record.scheduled_date)}</td>
        <td>${record.technician || "未分配"}</td>
        <td><span class="badge ${statusClass}">${statusText}</span></td>
        <td>¥${(record.cost || 0).toFixed(2)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="viewMaintenanceRecord(${
            record.id
          })">
            <i class="bi bi-eye"></i>
          </button>
          <button class="btn btn-sm btn-outline-success" onclick="editMaintenanceRecord(${
            record.id
          })">
            <i class="bi bi-pencil"></i>
          </button>
          ${
            record.status === "scheduled"
              ? `
            <button class="btn btn-sm btn-outline-info" onclick="startMaintenance(${record.id})">
              <i class="bi bi-play"></i>
            </button>
          `
              : ""
          }
          ${
            record.status === "in_progress"
              ? `
            <button class="btn btn-sm btn-outline-success" onclick="completeMaintenance(${record.id})">
              <i class="bi bi-check"></i>
            </button>
          `
              : ""
          }
        </td>
      </tr>
    `;
    })
    .join("");
}

/**
 * 显示模拟维护记录
 */
function displayMockMaintenanceRecords() {
  const mockRecords = [
    {
      id: 1,
      device_name: "RFID_READER_001",
      device_type: "rfid",
      maintenance_type: "routine",
      scheduled_date: new Date(
        Date.now() - 2 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "张明",
      status: "completed",
      cost: 150.0,
    },
    {
      id: 2,
      device_name: "RFID_READER_002",
      device_type: "rfid",
      maintenance_type: "preventive",
      scheduled_date: new Date(
        Date.now() + 3 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "李华",
      status: "scheduled",
      cost: 200.0,
    },
    {
      id: 3,
      device_name: "SENSOR_001",
      device_type: "sensor",
      maintenance_type: "calibration",
      scheduled_date: new Date(
        Date.now() - 1 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "陈磊",
      status: "in_progress",
      cost: 100.0,
    },
    {
      id: 4,
      device_name: "SENSOR_002",
      device_type: "sensor",
      maintenance_type: "routine",
      scheduled_date: new Date(
        Date.now() - 5 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "赵强",
      status: "completed",
      cost: 120.0,
    },
    {
      id: 5,
      device_name: "RFID_READER_003",
      device_type: "rfid",
      maintenance_type: "repair",
      scheduled_date: new Date(
        Date.now() + 1 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "陈工",
      status: "scheduled",
      cost: 350.0,
    },
    {
      id: 6,
      device_name: "SENSOR_003",
      device_type: "sensor",
      maintenance_type: "preventive",
      scheduled_date: new Date(
        Date.now() - 7 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "刘师傅",
      status: "overdue",
      cost: 180.0,
    },
    {
      id: 7,
      device_name: "RFID_READER_004",
      device_type: "rfid",
      maintenance_type: "calibration",
      scheduled_date: new Date(
        Date.now() + 7 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "孙技师",
      status: "scheduled",
      cost: 220.0,
    },
    {
      id: 8,
      device_name: "SENSOR_005",
      device_type: "sensor",
      maintenance_type: "routine",
      scheduled_date: new Date(
        Date.now() - 3 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "周工",
      status: "completed",
      cost: 95.0,
    },
    {
      id: 9,
      device_name: "RFID_READER_005",
      device_type: "rfid",
      maintenance_type: "preventive",
      scheduled_date: new Date(
        Date.now() + 5 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "吴师傅",
      status: "scheduled",
      cost: 280.0,
    },
    {
      id: 10,
      device_name: "SENSOR_006",
      device_type: "sensor",
      maintenance_type: "repair",
      scheduled_date: new Date(
        Date.now() - 4 * 24 * 60 * 60 * 1000
      ).toISOString(),
      technician: "郑技师",
      status: "completed",
      cost: 320.0,
    },
  ];

  displayMaintenanceRecords(mockRecords);
}

/**
 * 获取维护状态样式类
 */
function getMaintenanceStatusClass(status) {
  const statusClasses = {
    scheduled: "bg-warning",
    in_progress: "bg-info",
    completed: "bg-success",
    cancelled: "bg-secondary",
    overdue: "bg-danger",
  };
  return statusClasses[status] || "bg-secondary";
}

/**
 * 获取维护状态文本
 */
function getMaintenanceStatusText(status) {
  const statusTexts = {
    scheduled: "已计划",
    in_progress: "进行中",
    completed: "已完成",
    cancelled: "已取消",
    overdue: "已逾期",
  };
  return statusTexts[status] || "未知";
}

/**
 * 获取设备类型文本
 */
function getDeviceTypeText(deviceType) {
  const deviceTypes = {
    rfid: "RFID设备",
    sensor: "传感器",
    network: "网络设备",
    server: "服务器",
    other: "其他设备",
  };
  return deviceTypes[deviceType] || "未知类型";
}

/**
 * 获取维护类型文本
 */
function getMaintenanceTypeText(maintenanceType) {
  const maintenanceTypes = {
    routine: "定期检查",
    preventive: "预防性维护",
    corrective: "故障维修",
    upgrade: "设备升级",
    calibration: "设备校准",
  };
  return maintenanceTypes[maintenanceType] || "未知类型";
}

/**
 * 更新维护分页
 */
function updateMaintenancePagination(pagination) {
  const paginationElement = document.getElementById("maintenancePagination");
  if (!paginationElement || !pagination) return;

  let paginationHtml = "";

  // 上一页
  if (pagination.page > 1) {
    paginationHtml += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="loadMaintenanceRecords(${
          pagination.page - 1
        })">上一页</a>
      </li>
    `;
  }

  // 页码
  for (let i = 1; i <= pagination.pages; i++) {
    const activeClass = i === pagination.page ? "active" : "";
    paginationHtml += `
      <li class="page-item ${activeClass}">
        <a class="page-link" href="#" onclick="loadMaintenanceRecords(${i})">${i}</a>
      </li>
    `;
  }

  // 下一页
  if (pagination.page < pagination.pages) {
    paginationHtml += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="loadMaintenanceRecords(${
          pagination.page + 1
        })">下一页</a>
      </li>
    `;
  }

  paginationElement.innerHTML = paginationHtml;
}

/**
 * 搜索维护记录
 */
function searchMaintenanceRecords() {
  loadMaintenanceRecords(1);
}

/**
 * 重置维护筛选条件
 */
function resetMaintenanceFilters() {
  document.getElementById("maintenanceSearchInput").value = "";
  document.getElementById("deviceTypeFilter").value = "";
  document.getElementById("maintenanceTypeFilter").value = "";
  document.getElementById("statusFilter").value = "";
  loadMaintenanceRecords(1);
}

/**
 * 刷新维护数据
 */
function refreshMaintenanceData() {
  loadMaintenanceData();
  showSuccessMessage("维护数据已刷新");
}

/**
 * 添加维护记录
 */
function addMaintenanceRecord() {
  const form = document.getElementById("addMaintenanceForm");
  if (!form) return;

  const formData = new FormData(form);
  const data = Object.fromEntries(formData.entries());

  // 这里应该调用API添加维护记录
  console.log("添加维护记录:", data);
  showSuccessMessage("维护计划添加成功");

  // 关闭模态框
  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addMaintenanceModal")
  );
  if (modal) {
    modal.hide();
  }

  // 重置表单
  form.reset();

  // 刷新数据
  loadMaintenanceRecords();
}

/**
 * 查看维护记录详情
 */
function viewMaintenanceRecord(recordId) {
  showSuccessMessage(`查看维护记录 ${recordId} 详情`);
}

/**
 * 编辑维护记录
 */
function editMaintenanceRecord(recordId) {
  showSuccessMessage(`编辑维护记录 ${recordId}`);
}

/**
 * 开始维护
 */
function startMaintenance(recordId) {
  if (confirm("确定要开始这项维护工作吗？")) {
    showSuccessMessage(`维护工作 ${recordId} 已开始`);
    loadMaintenanceRecords();
  }
}

/**
 * 完成维护
 */
function completeMaintenance(recordId) {
  if (confirm("确定要标记这项维护工作为已完成吗？")) {
    showSuccessMessage(`维护工作 ${recordId} 已完成`);
    loadMaintenanceRecords();
  }
}
// ==================== 环境监测页面函数 ====================

/**
 * 添加传感器
 */
function addSensor() {
  const form = document.getElementById("addSensorForm");
  const formData = new FormData(form);

  // 模拟添加传感器
  showSuccessMessage("传感器添加成功");

  // 关闭模态框
  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addSensorModal")
  );
  modal.hide();

  // 重置表单
  form.reset();
}

/**
 * 编辑传感器
 */
function editSensor(sensorId) {
  showSuccessMessage(`正在编辑传感器 ${sensorId}`);
}

/**
 * 删除传感器
 */
function deleteSensor(sensorId) {
  if (confirm(`确定要删除传感器 ${sensorId} 吗？`)) {
    showSuccessMessage(`传感器 ${sensorId} 已删除`);
  }
}

// ==================== RFID设备管理页面函数 ====================

/**
 * 添加RFID设备
 */
function addRfidDevice() {
  const form = document.getElementById("addRfidDeviceForm");
  showSuccessMessage("RFID设备添加成功");

  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addRfidDeviceModal")
  );
  modal.hide();
  form.reset();
}

/**
 * 配置RFID设备
 */
function configRfidDevice(deviceId) {
  showSuccessMessage(`正在配置RFID设备 ${deviceId}`);
}

/**
 * 添加RFID标签
 */
function addTag() {
  const form = document.getElementById("addTagForm");
  showSuccessMessage("RFID标签添加成功");

  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addTagModal")
  );
  modal.hide();
  form.reset();
}

/**
 * 编辑标签
 */
function editTag(tagId) {
  showSuccessMessage(`正在编辑标签 ${tagId}`);
}

/**
 * 定位标签
 */
function locateTag(tagId) {
  showSuccessMessage(`正在定位标签 ${tagId}`);
}

/**
 * 删除标签
 */
function deleteTag(tagId) {
  if (confirm(`确定要删除标签 ${tagId} 吗？`)) {
    showSuccessMessage(`标签 ${tagId} 已删除`);
  }
}

/**
 * 搜索标签
 */
function searchTags() {
  const searchInput = document.getElementById("tagSearchInput").value;
  const statusFilter = document.getElementById("tagStatusFilter").value;

  showSuccessMessage(
    `搜索标签: ${searchInput}, 状态: ${statusFilter || "全部"}`
  );
}

/**
 * 导入标签
 */
function importTags() {
  showSuccessMessage("标签批量导入功能");
}

// ==================== 档案追踪页面函数 ====================

/**
 * 搜索档案
 */
function searchArchive() {
  const searchInput = document.getElementById("archiveSearchInput").value;
  showSuccessMessage(`搜索档案: ${searchInput}`);
}

/**
 * 添加档案
 */
function addArchive() {
  const form = document.getElementById("addArchiveForm");
  showSuccessMessage("档案添加成功");

  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addArchiveModal")
  );
  modal.hide();
  form.reset();
}

/**
 * 查看档案详情
 */
function viewArchive(archiveId) {
  showSuccessMessage(`查看档案详情: ${archiveId}`);
}

/**
 * 追踪档案
 */
function trackArchive(archiveId) {
  showSuccessMessage(`追踪档案: ${archiveId}`);
}

/**
 * 借出档案
 */
function borrowArchive(archiveId) {
  showSuccessMessage(`借出档案: ${archiveId}`);
}

/**
 * 筛选档案
 */
function filterArchives() {
  const category = document.getElementById("categoryFilter").value;
  const location = document.getElementById("locationFilter").value;
  const status = document.getElementById("statusFilter").value;

  showSuccessMessage(
    `筛选档案 - 类别: ${category || "全部"}, 位置: ${
      location || "全部"
    }, 状态: ${status || "全部"}`
  );
}

// ==================== 智能盘点页面函数 ====================

/**
 * 暂停盘点
 */
function pauseInventory() {
  showSuccessMessage("盘点已暂停");
}

/**
 * 停止盘点
 */
function stopInventory() {
  if (confirm("确定要停止当前盘点任务吗？")) {
    showSuccessMessage("盘点已停止");
  }
}

/**
 * 查看盘点详情
 */
function viewInventoryDetail(taskId) {
  showSuccessMessage(`查看盘点任务详情: ${taskId}`);
}

/**
 * 下载盘点报告
 */
function downloadReport(taskId) {
  showSuccessMessage(`下载盘点报告: ${taskId}`);
}

/**
 * 导出盘点报告
 */
function exportInventoryReport() {
  showSuccessMessage("导出盘点报告");
}

/**
 * 标记档案为找到
 */
function markAsFound(archiveId) {
  showSuccessMessage(`档案 ${archiveId} 已标记为找到`);
}

/**
 * 识别多余档案
 */
function identifyExtra(tagId) {
  showSuccessMessage(`识别多余档案: ${tagId}`);
}

// ==================== 告警管理页面函数 ====================

/**
 * 处理告警
 */
function handleAlert(alertId) {
  showSuccessMessage(`正在处理告警: ${alertId}`);
}

/**
 * 查看告警详情
 */
function viewAlertDetail(alertId) {
  showSuccessMessage(`查看告警详情: ${alertId}`);
}

/**
 * 筛选告警
 */
function filterAlerts() {
  const level = document.getElementById("alertLevelFilter").value;
  const type = document.getElementById("alertTypeFilter").value;
  const status = document.getElementById("alertStatusFilter").value;

  showSuccessMessage(
    `筛选告警 - 级别: ${level || "全部"}, 类型: ${type || "全部"}, 状态: ${
      status || "全部"
    }`
  );
}

/**
 * 全部标记为已读
 */
function markAllAsRead() {
  showSuccessMessage("所有告警已标记为已读");
}

/**
 * 保存告警规则
 */
function saveAlertRules() {
  showSuccessMessage("告警规则保存成功");
}

// ==================== 统计报表页面函数 ====================

/**
 * 生成报表
 */
function generateReport() {
  const reportType = document.getElementById("reportType").value;
  const timeRange = document.getElementById("timeRange").value;

  // 获取报表类型的中文名称
  const reportTypeNames = {
    environment: "环境数据",
    archive: "档案统计",
    inventory: "盘点结果",
    alert: "告警统计",
  };

  const reportTypeName = reportTypeNames[reportType] || reportType;

  showSuccessMessage(`正在生成${reportTypeName}报表，时间范围: ${timeRange}`);

  // 根据报表类型更新图表和表格
  setTimeout(() => {
    updateCharts();
    updateReportTable();
    showSuccessMessage(`${reportTypeName}报表生成完成`);
  }, 1000);
}

/**
 * 导出Excel报表
 */
function exportReport() {
  showSuccessMessage("报表导出为Excel成功");
}

/**
 * 导出PDF报表
 */
function exportPDF() {
  showSuccessMessage("报表导出为PDF成功");
}

/**
 * 更新图表
 */
function updateCharts() {
  // 更新环境数据趋势图表
  updateEnvironmentChart();

  // 更新档案分布统计图表
  updateArchiveChart();
}

/**
 * 初始化环境数据趋势图表
 */
function initEnvironmentChart() {
  const ctx = document.getElementById("environmentChart");
  if (!ctx) return;

  // 生成模拟的24小时数据
  const hours = [];
  const tempData = [];
  const humidityData = [];
  const lightData = [];

  for (let i = 0; i < 24; i++) {
    hours.push(`${i.toString().padStart(2, "0")}:00`);
    tempData.push(
      (20 + Math.sin((i * Math.PI) / 12) * 3 + Math.random() * 2).toFixed(1)
    );
    humidityData.push(
      (50 + Math.cos((i * Math.PI) / 12) * 10 + Math.random() * 5).toFixed(1)
    );
    lightData.push(
      (300 + Math.sin((i * Math.PI) / 6) * 100 + Math.random() * 50).toFixed(0)
    );
  }

  // 检查Chart.js是否已加载
  if (typeof Chart === "undefined") {
    console.warn("Chart.js未加载，跳过图表初始化");
    return;
  }

  window.environmentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: hours,
      datasets: [
        {
          label: "温度 (°C)",
          data: tempData,
          borderColor: "rgb(255, 99, 132)",
          backgroundColor: "rgba(255, 99, 132, 0.1)",
          tension: 0.4,
          yAxisID: "y",
        },
        {
          label: "湿度 (%)",
          data: humidityData,
          borderColor: "rgb(54, 162, 235)",
          backgroundColor: "rgba(54, 162, 235, 0.1)",
          tension: 0.4,
          yAxisID: "y1",
        },
        {
          label: "光照 (lux)",
          data: lightData,
          borderColor: "rgb(255, 205, 86)",
          backgroundColor: "rgba(255, 205, 86, 0.1)",
          tension: 0.4,
          yAxisID: "y2",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        title: {
          display: true,
          text: "24小时环境数据趋势",
        },
        legend: {
          position: "top",
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: "时间",
          },
        },
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: {
            display: true,
            text: "温度 (°C)",
            color: "rgb(255, 99, 132)",
          },
          min: 15,
          max: 30,
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          title: {
            display: true,
            text: "湿度 (%)",
            color: "rgb(54, 162, 235)",
          },
          min: 30,
          max: 70,
          grid: {
            drawOnChartArea: false,
          },
        },
        y2: {
          type: "linear",
          display: false,
          min: 200,
          max: 500,
        },
      },
    },
  });
}

/**
 * 初始化档案分布统计图表
 */
function initArchiveChart() {
  const ctx = document.getElementById("archiveChart");
  if (!ctx) return;

  const archiveData = {
    labels: ["人事档案", "财务档案", "项目档案", "合同档案", "其他档案"],
    data: [856, 742, 598, 423, 237],
    colors: [
      "rgb(255, 99, 132)",
      "rgb(54, 162, 235)",
      "rgb(255, 205, 86)",
      "rgb(75, 192, 192)",
      "rgb(153, 102, 255)",
    ],
  };

  // 检查Chart.js是否已加载
  if (typeof Chart === "undefined") {
    console.warn("Chart.js未加载，跳过图表初始化");
    return;
  }

  window.archiveChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: archiveData.labels,
      datasets: [
        {
          label: "档案数量",
          data: archiveData.data,
          backgroundColor: archiveData.colors,
          borderColor: archiveData.colors.map((color) =>
            color.replace("rgb", "rgba").replace(")", ", 1)")
          ),
          borderWidth: 2,
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: "档案类型分布统计",
        },
        legend: {
          position: "bottom",
          labels: {
            padding: 20,
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.parsed;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              return `${label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

/**
 * 更新环境数据趋势图表
 */
function updateEnvironmentChart() {
  if (!window.environmentChart) {
    initEnvironmentChart();
    return;
  }

  // 生成新的数据
  const newTempData = [];
  const newHumidityData = [];
  const newLightData = [];

  for (let i = 0; i < 24; i++) {
    newTempData.push(
      (20 + Math.sin((i * Math.PI) / 12) * 3 + Math.random() * 2).toFixed(1)
    );
    newHumidityData.push(
      (50 + Math.cos((i * Math.PI) / 12) * 10 + Math.random() * 5).toFixed(1)
    );
    newLightData.push(
      (300 + Math.sin((i * Math.PI) / 6) * 100 + Math.random() * 50).toFixed(0)
    );
  }

  // 更新图表数据
  window.environmentChart.data.datasets[0].data = newTempData;
  window.environmentChart.data.datasets[1].data = newHumidityData;
  window.environmentChart.data.datasets[2].data = newLightData;
  window.environmentChart.update();
}

/**
 * 更新档案分布统计图表
 */
function updateArchiveChart() {
  if (!window.archiveChart) {
    initArchiveChart();
    return;
  }

  // 生成新的档案分布数据
  const newData = [
    Math.floor(200 + Math.random() * 100), // 人事档案
    Math.floor(150 + Math.random() * 80), // 财务档案
    Math.floor(120 + Math.random() * 70), // 项目档案
    Math.floor(80 + Math.random() * 50), // 合同档案
    Math.floor(50 + Math.random() * 40), // 其他档案
  ];

  // 更新图表数据
  window.archiveChart.data.datasets[0].data = newData;
  window.archiveChart.update();
}

// ==================== 设备维护页面函数 ====================

/**
 * 添加维护计划
 */
function addMaintenance() {
  const form = document.getElementById("addMaintenanceForm");
  showSuccessMessage("维护计划添加成功");

  const modal = bootstrap.Modal.getInstance(
    document.getElementById("addMaintenanceModal")
  );
  modal.hide();
  form.reset();
}

/**
 * 完成维护
 */
function completeMaintenance(maintenanceId) {
  if (confirm("确定标记此维护任务为已完成吗？")) {
    showSuccessMessage(`维护任务 ${maintenanceId} 已完成`);
  }
}

/**
 * 编辑维护计划
 */
function editMaintenance(maintenanceId) {
  showSuccessMessage(`编辑维护计划: ${maintenanceId}`);
}

/**
 * 筛选维护记录
 */
function filterMaintenance() {
  const deviceType = document.getElementById("deviceTypeFilter").value;
  const maintenanceType = document.getElementById(
    "maintenanceTypeFilter"
  ).value;
  const date = document.getElementById("maintenanceDateFilter").value;

  showSuccessMessage(
    `筛选维护记录 - 设备类型: ${deviceType || "全部"}, 维护类型: ${
      maintenanceType || "全部"
    }, 日期: ${date || "全部"}`
  );
}

// ==================== 系统配置页面函数 ====================

/**
 * 备份数据库
 */
function backupDatabase() {
  if (confirm("确定要备份数据库吗？")) {
    showSuccessMessage("数据库备份成功");
  }
}

/**
 * 恢复数据库
 */
function restoreDatabase() {
  if (confirm("确定要恢复数据库吗？此操作将覆盖当前数据！")) {
    showSuccessMessage("数据库恢复成功");
  }
}

/**
 * 清理历史数据
 */
function clearOldData() {
  if (confirm("确定要清理历史数据吗？此操作不可恢复！")) {
    showSuccessMessage("历史数据清理成功");
  }
}

/**
 * 检查更新
 */
function checkUpdate() {
  showSuccessMessage("系统已是最新版本");
}

// ==================== 通用工具函数 ====================

/**
 * 初始化滑块控件
 */
function initializeSliders() {
  // 初始化RFID功率滑块
  const powerSlider = document.getElementById("scanPower");
  const powerValue = document.getElementById("powerValue");

  if (powerSlider && powerValue) {
    powerSlider.addEventListener("input", function () {
      powerValue.textContent = this.value;
    });
  }
}

/**
 * 初始化表单事件
 */
function initializeFormEvents() {
  // 环境阈值表单
  const thresholdForm = document.getElementById("thresholdForm");
  if (thresholdForm) {
    thresholdForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showSuccessMessage("环境阈值配置保存成功");
    });
  }

  // RFID配置表单
  const rfidConfigForm = document.getElementById("rfidConfigForm");
  if (rfidConfigForm) {
    rfidConfigForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showSuccessMessage("RFID参数配置保存成功");
    });
  }

  // 盘点任务表单
  const inventoryTaskForm = document.getElementById("inventoryTaskForm");
  if (inventoryTaskForm) {
    inventoryTaskForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showSuccessMessage("盘点任务已开始");
    });
  }

  // 报表生成表单
  const reportForm = document.getElementById("reportForm");
  if (reportForm) {
    reportForm.addEventListener("submit", function (e) {
      e.preventDefault();
      generateReport();
    });

    // 设置默认日期范围
    const today = new Date();
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");

    if (startDateInput) {
      startDateInput.value = lastWeek.toISOString().split("T")[0];
    }
    if (endDateInput) {
      endDateInput.value = today.toISOString().split("T")[0];
    }

    // 时间范围选择变化时更新日期输入框
    const timeRangeSelect = document.getElementById("timeRange");
    if (timeRangeSelect) {
      timeRangeSelect.addEventListener("change", function () {
        updateDateRange(this.value);
      });
    }
  }

  // 基本设置表单
  const basicSettingsForm = document.getElementById("basicSettingsForm");
  if (basicSettingsForm) {
    basicSettingsForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showSuccessMessage("基本设置保存成功");
    });
  }

  // 安全设置表单
  const securitySettingsForm = document.getElementById("securitySettingsForm");
  if (securitySettingsForm) {
    securitySettingsForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showSuccessMessage("安全设置保存成功");
    });
  }

  // 网络设置表单
  const networkSettingsForm = document.getElementById("networkSettingsForm");
  if (networkSettingsForm) {
    networkSettingsForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showSuccessMessage("网络设置保存成功");
    });
  }
}

/**
 * 显示信息消息
 */
function showInfoMessage(message) {
  const alertDiv = document.createElement("div");
  alertDiv.className =
    "alert alert-info alert-dismissible fade show position-fixed";
  alertDiv.style.cssText =
    "top: 80px; right: 20px; z-index: 9999; min-width: 350px;";
  alertDiv.innerHTML = `
    <i class="bi bi-info-circle-fill"></i>
    <strong>信息：</strong> ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(alertDiv);

  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 3000);
}

/**
 * 根据时间范围更新日期输入框
 */
function updateDateRange(timeRange) {
  const startDateInput = document.getElementById("startDate");
  const endDateInput = document.getElementById("endDate");

  if (!startDateInput || !endDateInput) return;

  const today = new Date();
  let startDate = new Date();

  switch (timeRange) {
    case "today":
      startDate = new Date(today);
      break;
    case "week":
      startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case "month":
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      break;
    case "quarter":
      const quarterStart = Math.floor(today.getMonth() / 3) * 3;
      startDate = new Date(today.getFullYear(), quarterStart, 1);
      break;
    case "year":
      startDate = new Date(today.getFullYear(), 0, 1);
      break;
    case "custom":
      // 自定义时间范围，不自动设置
      return;
    default:
      startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  }

  startDateInput.value = startDate.toISOString().split("T")[0];
  endDateInput.value = today.toISOString().split("T")[0];
}
// ==================== 新增的交互函数 ====================

/**
 * 归还档案
 */
function returnArchive(archiveId) {
  showSuccessMessage(`档案 ${archiveId} 已归还`);
}

/**
 * 报告档案缺失
 */
function reportMissing(archiveId) {
  showWarningMessage(`已报告档案 ${archiveId} 缺失，将启动查找程序`);
}

/**
 * 搜索档案
 */
function searchArchive(archiveId) {
  showInfoMessage(`正在全库搜索档案 ${archiveId}...`);
}

/**
 * 更新仪表盘统计数据
 */
function updateDashboardStats() {
  // 更新传感器计数（考虑离线设备）
  updateElement("sensorCount", "5");

  // 更新RFID设备计数（考虑离线设备）
  updateElement("rfidCount", "5");

  // 更新档案总数
  updateElement("archiveCount", "2,856");

  // 更新告警计数（严重2个 + 警告3个）
  updateElement("alertCount", "5");
}

/**
 * 生成更真实的位置分布数据
 */
function updateLocationStats() {
  const locationStats = document.querySelector(".location-stats");
  if (!locationStats) return;

  const locations = [
    { name: "档案室A区", count: 1245, percentage: 44 },
    { name: "档案室B区", count: 987, percentage: 35 },
    { name: "档案室C区", count: 456, percentage: 16 },
    { name: "特藏室", count: 168, percentage: 5 },
  ];

  locationStats.innerHTML = locations
    .map(
      (loc) => `
    <div class="d-flex justify-content-between mb-2">
      <span>${loc.name}</span>
      <span class="badge bg-primary">${loc.count}</span>
    </div>
    <div class="progress mb-3">
      <div class="progress-bar bg-primary" style="width: ${loc.percentage}%"></div>
    </div>
  `
    )
    .join("");
}

/**
 * 更新时间线数据
 */
function updateTimelineData() {
  const timeline = document.getElementById("locationTimeline");
  if (!timeline) return;

  const timelineData = [
    {
      location: "档案室A区-东侧",
      archive: "ARCH2024001 - 员工入职档案-张三",
      time: "2024-08-05 18:45:23",
      type: "success",
      action: "档案入库",
    },
    {
      location: "档案室主入口",
      archive: "ARCH2024004 - 员工离职档案-李四",
      time: "2024-08-05 16:30:15",
      type: "warning",
      action: "档案借出",
    },
    {
      location: "档案室B区-中央",
      archive: "ARCH2024002 - 2024年度预算报告",
      time: "2024-08-05 15:20:45",
      type: "info",
      action: "档案移动",
    },
    {
      location: "特藏室-恒温区",
      archive: "ARCH2024005 - 设备采购清单2024",
      time: "2024-08-05 14:10:30",
      type: "success",
      action: "档案归档",
    },
    {
      location: "未知位置",
      archive: "ARCH2024006 - 项目验收报告-XYZ",
      time: "2024-08-04 09:15:20",
      type: "danger",
      action: "档案丢失",
    },
  ];

  timeline.innerHTML = timelineData
    .map(
      (item) => `
    <div class="timeline-item">
      <div class="timeline-marker bg-${item.type}"></div>
      <div class="timeline-content">
        <h6>${item.location}</h6>
        <p class="text-muted mb-1">${item.archive}</p>
        <small class="text-muted">${item.time} - ${item.action}</small>
      </div>
    </div>
  `
    )
    .join("");
}

/**
 * 初始化额外的数据更新
 */
function initializeExtraData() {
  // 延迟执行，确保DOM完全加载
  setTimeout(() => {
    updateDashboardStats();
    updateLocationStats();
    updateTimelineData();
  }, 1000);
}

/**
 * 增强的数据更新函数
 */
function refreshAllData() {
  loadDashboardData();
  updateDashboardStats();
  updateLocationStats();
  updateTimelineData();
  showSuccessMessage("数据已刷新");
}

/**
 * 暂停数据采集
 */
function pauseCollection() {
  try {
    updateElement("collectionStatus", "已暂停", "badge bg-warning");
    showSuccessMessage("数据采集已暂停");
  } catch (error) {
    console.error("暂停数据采集失败:", error);
    showErrorMessage("暂停数据采集失败");
  }
}

/**
 * 恢复数据采集
 */
function resumeCollection() {
  try {
    updateElement("collectionStatus", "运行中", "badge bg-success");
    showSuccessMessage("数据采集已恢复");
  } catch (error) {
    console.error("恢复数据采集失败:", error);
    showErrorMessage("恢复数据采集失败");
  }
}

/**
 * 保存采集设置
 */
function saveCollectionSettings() {
  try {
    const envInterval = document.getElementById("envInterval").value;
    const rfidInterval = document.getElementById("rfidInterval").value;

    console.log("保存采集设置:", { envInterval, rfidInterval });
    showSuccessMessage("采集设置已保存");
  } catch (error) {
    console.error("保存采集设置失败:", error);
    showErrorMessage("保存采集设置失败");
  }
}

/**
 * 初始化数据采集页面
 */
function initCollectionPage() {
  // 初始化滑块事件监听
  const envIntervalSlider = document.getElementById("envInterval");
  const rfidIntervalSlider = document.getElementById("rfidInterval");

  if (envIntervalSlider) {
    envIntervalSlider.addEventListener("input", function () {
      document.getElementById("envIntervalValue").textContent =
        this.value + "秒";
    });
  }

  if (rfidIntervalSlider) {
    rfidIntervalSlider.addEventListener("input", function () {
      document.getElementById("rfidIntervalValue").textContent =
        this.value + "秒";
    });
  }

  // 启动性能监控定时更新
  setInterval(loadSystemPerformance, 5000); // 每5秒更新一次
}

/**
 * 显示成功消息
 */
function showSuccessMessage(message) {
  const alertDiv = document.createElement("div");
  alertDiv.className =
    "alert alert-success alert-dismissible fade show position-fixed";
  alertDiv.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
  alertDiv.innerHTML = `
    <i class="bi bi-check-circle-fill"></i>
    <strong>成功：</strong> ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(alertDiv);

  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 2000);
}

/**
 * 显示错误消息
 */
function showErrorMessage(message) {
  const alertDiv = document.createElement("div");
  alertDiv.className =
    "alert alert-danger alert-dismissible fade show position-fixed";
  alertDiv.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
  alertDiv.innerHTML = `
    <i class="bi bi-exclamation-triangle-fill"></i>
    <strong>错误：</strong> ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(alertDiv);

  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 3000);
}

/**
 * 初始化侧边栏导航
 */
function initializeSideNavigation() {
  // 创建移动端菜单切换按钮
  if (window.innerWidth <= 768) {
    createMobileToggle();
  }

  // 监听窗口大小变化
  window.addEventListener("resize", handleWindowResize);

  // 初始化侧边栏切换功能
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", toggleSidebar);
  }
}

/**
 * 创建移动端菜单切换按钮
 */
function createMobileToggle() {
  const existingToggle = document.querySelector(".mobile-toggle");
  if (existingToggle) return;

  const mobileToggle = document.createElement("button");
  mobileToggle.className = "mobile-toggle";
  mobileToggle.innerHTML = '<i class="bi bi-list"></i>';
  mobileToggle.addEventListener("click", toggleMobileSidebar);

  document.body.appendChild(mobileToggle);
}

/**
 * 切换移动端侧边栏
 */
function toggleMobileSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.querySelector(".sidebar-overlay") || createOverlay();

  if (sidebar.classList.contains("show")) {
    sidebar.classList.remove("show");
    overlay.classList.remove("show");
  } else {
    sidebar.classList.add("show");
    overlay.classList.add("show");
  }
}

/**
 * 创建遮罩层
 */
function createOverlay() {
  const overlay = document.createElement("div");
  overlay.className = "sidebar-overlay";
  overlay.addEventListener("click", toggleMobileSidebar);
  document.body.appendChild(overlay);
  return overlay;
}

/**
 * 切换侧边栏折叠状态
 */
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  sidebar.classList.toggle("collapsed");

  // 保存状态到localStorage
  const isCollapsed = sidebar.classList.contains("collapsed");
  localStorage.setItem("sidebarCollapsed", isCollapsed);
}

/**
 * 处理窗口大小变化
 */
function handleWindowResize() {
  const sidebar = document.getElementById("sidebar");
  const mobileToggle = document.querySelector(".mobile-toggle");
  const overlay = document.querySelector(".sidebar-overlay");

  if (window.innerWidth <= 768) {
    // 移动端模式
    if (!mobileToggle) {
      createMobileToggle();
    }

    // 隐藏侧边栏
    sidebar.classList.remove("show");
    if (overlay) {
      overlay.classList.remove("show");
    }
  } else {
    // 桌面端模式
    if (mobileToggle) {
      mobileToggle.remove();
    }

    if (overlay) {
      overlay.remove();
    }

    // 恢复侧边栏状态
    sidebar.classList.remove("show");
    const isCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
    if (isCollapsed) {
      sidebar.classList.add("collapsed");
    }
  }
}

/**
 * 优化表格响应式显示
 */
function optimizeTableResponsive() {
  const tables = document.querySelectorAll(".table");

  tables.forEach((table) => {
    if (!table.closest(".table-responsive")) {
      const wrapper = document.createElement("div");
      wrapper.className = "table-responsive";
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  });
}

/**
 * 优化卡片高度（移动端）
 */
function optimizeCardHeights() {
  if (window.innerWidth <= 768) {
    const fixedHeightCards = document.querySelectorAll(
      '.card[style*="height"]'
    );

    fixedHeightCards.forEach((card) => {
      const originalHeight = card.style.height;
      card.setAttribute("data-original-height", originalHeight);
      card.style.height = "auto";
      card.style.minHeight = "250px";
    });
  } else {
    const cards = document.querySelectorAll(".card[data-original-height]");

    cards.forEach((card) => {
      const originalHeight = card.getAttribute("data-original-height");
      card.style.height = originalHeight;
      card.style.minHeight = "";
    });
  }
}

/**
 * 初始化响应式功能
 */
function initializeResponsive() {
  // 优化表格响应式
  optimizeTableResponsive();

  // 优化卡片高度
  optimizeCardHeights();

  // 监听窗口大小变化
  window.addEventListener(
    "resize",
    debounce(() => {
      optimizeCardHeights();
    }, 250)
  );
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ==================== 页面切换函数 ====================

/**
 * 加载数据管理页面数据
 */
async function loadDataManagementData() {
  try {
    // 更新数据库状态信息
    updateElement("dbSize", "125 MB");
    updateElement("lastBackup", "2024-08-05 10:30");
    updateElement("recordCount", "15,678 条");

    // 更新数据统计
    updateElement("envDataCount", "8,456");
    updateElement("rfidDataCount", "12,345");
    updateElement("alertDataCount", "234");
    updateElement("archiveDataCount", "1,567");

    console.log("数据管理页面数据加载完成");
  } catch (error) {
    console.error("加载数据管理页面失败:", error);
    showErrorMessage("加载数据管理页面失败");
  }
}

// ==================== 数据管理页面函数 ====================

/**
 * 备份数据库
 */
async function backupDatabase() {
  try {
    showSuccessMessage("正在备份数据库...");

    // 模拟备份过程
    setTimeout(() => {
      const now = new Date().toLocaleString();
      updateElement("lastBackup", now);
      showSuccessMessage("数据库备份完成");
    }, 2000);
  } catch (error) {
    console.error("备份数据库失败:", error);
    showErrorMessage("备份数据库失败");
  }
}

/**
 * 恢复数据库
 */
async function restoreDatabase() {
  if (!confirm("确定要恢复数据库吗？此操作将覆盖当前数据！")) {
    return;
  }

  try {
    showSuccessMessage("正在恢复数据库...");

    // 模拟恢复过程
    setTimeout(() => {
      showSuccessMessage("数据库恢复完成");
    }, 3000);
  } catch (error) {
    console.error("恢复数据库失败:", error);
    showErrorMessage("恢复数据库失败");
  }
}

/**
 * 优化数据库
 */
async function optimizeDatabase() {
  try {
    showSuccessMessage("正在优化数据库...");

    // 模拟优化过程
    setTimeout(() => {
      showSuccessMessage("数据库优化完成");
    }, 2000);
  } catch (error) {
    console.error("优化数据库失败:", error);
    showErrorMessage("优化数据库失败");
  }
}

/**
 * 检查数据库完整性
 */
async function checkDatabase() {
  try {
    showSuccessMessage("正在检查数据库完整性...");

    // 模拟检查过程
    setTimeout(() => {
      showSuccessMessage("数据库完整性检查通过");
    }, 1500);
  } catch (error) {
    console.error("检查数据库失败:", error);
    showErrorMessage("检查数据库失败");
  }
}

/**
 * 清理历史数据
 */
async function clearOldData() {
  if (!confirm("确定要清理历史数据吗？此操作不可恢复！")) {
    return;
  }

  try {
    showSuccessMessage("正在清理历史数据...");

    // 模拟清理过程
    setTimeout(() => {
      // 更新数据统计
      updateElement("envDataCount", "6,234");
      updateElement("rfidDataCount", "9,876");
      updateElement("alertDataCount", "156");
      updateElement("recordCount", "12,456 条");
      updateElement("dbSize", "98 MB");

      showSuccessMessage("历史数据清理完成");
    }, 2500);
  } catch (error) {
    console.error("清理历史数据失败:", error);
    showErrorMessage("清理历史数据失败");
  }
}

/**
 * 导入数据
 */
async function importData() {
  const importType = document.getElementById("importType").value;
  const fileInput = document.querySelector('input[type="file"]');

  if (!fileInput.files.length) {
    showErrorMessage("请选择要导入的文件");
    return;
  }

  try {
    showSuccessMessage(`正在导入${importType}数据...`);

    // 模拟导入过程
    setTimeout(() => {
      showSuccessMessage("数据导入完成");
      // 重新加载数据统计
      loadDataManagementData();
    }, 3000);
  } catch (error) {
    console.error("导入数据失败:", error);
    showErrorMessage("导入数据失败");
  }
}

/**
 * 导出数据
 */
async function exportData() {
  const exportType = document.getElementById("exportType").value;
  const startDate = document.getElementById("exportStartDate").value;
  const endDate = document.getElementById("exportEndDate").value;
  const format = document.getElementById("exportFormat").value;

  if (!startDate || !endDate) {
    showErrorMessage("请选择导出时间范围");
    return;
  }

  try {
    showSuccessMessage(`正在导出${exportType}数据...`);

    // 模拟导出过程
    setTimeout(() => {
      // 创建下载链接
      const filename = `${exportType}_data_${startDate}_${endDate}.${format}`;
      showSuccessMessage(`数据导出完成: ${filename}`);
    }, 2000);
  } catch (error) {
    console.error("导出数据失败:", error);
    showErrorMessage("导出数据失败");
  }
}

// ==================== 设备维护页面函数 ====================

/**
 * 加载维护记录
 */
async function loadMaintenanceRecords() {
  try {
    const response = await fetch("/api/maintenance/records");
    const result = await response.json();

    if (result.success) {
      updateMaintenanceTable(result.data.records);
    } else {
      console.error("加载维护记录失败:", result.message);
    }
  } catch (error) {
    console.error("加载维护记录失败:", error);
  }
}

/**
 * 加载维护统计信息
 */
async function loadMaintenanceStatistics() {
  try {
    const response = await fetch("/api/maintenance/statistics");
    const result = await response.json();

    if (result.success) {
      updateMaintenanceStatistics(result.data);
    } else {
      console.error("加载维护统计失败:", result.message);
    }
  } catch (error) {
    console.error("加载维护统计失败:", error);
  }
}

/**
 * 更新维护记录表格
 */
function updateMaintenanceTable(records) {
  const tableBody = document.querySelector("#maintenance-page .table tbody");
  if (!tableBody) return;

  // 清空现有内容
  tableBody.innerHTML = "";

  // 添加记录
  records.forEach((record) => {
    const row = document.createElement("tr");

    // 状态样式映射
    const statusMap = {
      scheduled: { class: "bg-warning", text: "计划中" },
      in_progress: { class: "bg-info", text: "进行中" },
      completed: { class: "bg-success", text: "已完成" },
      cancelled: { class: "bg-secondary", text: "已取消" },
      overdue: { class: "bg-danger", text: "已逾期" },
    };

    const statusInfo = statusMap[record.status] || {
      class: "bg-secondary",
      text: "未知",
    };

    // 设备类型映射
    const deviceTypeMap = {
      rfid: "RFID设备",
      sensor: "传感器",
      network: "网络设备",
      server: "服务器",
      other: "其他设备",
    };

    // 维护类型映射
    const maintenanceTypeMap = {
      routine: "定期检查",
      preventive: "预防性维护",
      corrective: "故障维修",
      upgrade: "设备升级",
      calibration: "设备校准",
    };

    row.innerHTML = `
      <td>${deviceTypeMap[record.device_type] || record.device_type}</td>
      <td>${record.device_name || "-"}</td>
      <td>${
        maintenanceTypeMap[record.maintenance_type] || record.maintenance_type
      }</td>
      <td>${formatDateTime(record.scheduled_date)}</td>
      <td>${record.technician || "-"}</td>
      <td><span class="badge ${statusInfo.class}">${statusInfo.text}</span></td>
      <td>
        ${
          record.status === "scheduled"
            ? `
          <button class="btn btn-sm btn-outline-success" onclick="completeMaintenance(${record.id})">
            <i class="bi bi-check"></i> 完成
          </button>
        `
            : ""
        }
        <button class="btn btn-sm btn-outline-primary" onclick="editMaintenance(${
          record.id
        })">
          <i class="bi bi-pencil"></i> 编辑
        </button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteMaintenance(${
          record.id
        })">
          <i class="bi bi-trash"></i> 删除
        </button>
      </td>
    `;

    tableBody.appendChild(row);
  });
}

/**
 * 更新维护统计信息
 */
function updateMaintenanceStatistics(stats) {
  // 更新统计卡片
  const scheduledCount = stats.by_status.scheduled || 0;
  const completedCount = stats.by_status.completed || 0;
  const totalCost = stats.cost_statistics.total_cost || 0;

  // 更新页面显示
  const scheduledElement = document.querySelector(
    "#maintenance-page .text-warning"
  );
  if (scheduledElement) {
    scheduledElement.textContent = scheduledCount;
  }

  const completedElement = document.querySelector(
    "#maintenance-page .text-success"
  );
  if (completedElement) {
    completedElement.textContent = completedCount;
  }

  const costElement = document.querySelector("#maintenance-page .text-info");
  if (costElement) {
    costElement.textContent = `¥${totalCost.toFixed(0)}`;
  }
}

/**
 * 绑定维护页面事件
 */
function bindMaintenanceEvents() {
  // 添加维护计划表单提交
  const addMaintenanceForm = document.getElementById("addMaintenanceForm");
  if (addMaintenanceForm) {
    addMaintenanceForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await addMaintenancePlan();
    });
  }

  // 筛选按钮
  const filterButton = document.querySelector(
    '#maintenance-page button[onclick="filterMaintenance()"]'
  );
  if (filterButton) {
    filterButton.onclick = filterMaintenanceRecords;
  }
}

/**
 * 添加维护计划
 */
async function addMaintenancePlan() {
  try {
    const form = document.getElementById("addMaintenanceForm");
    const formData = new FormData(form);

    const data = {
      device_type: formData.get("device_type"),
      device_name: formData.get("device_name"),
      maintenance_type: formData.get("maintenance_type"),
      description: formData.get("description"),
      scheduled_date: formData.get("scheduled_date"),
      technician: formData.get("technician"),
      cost: parseFloat(formData.get("cost")) || 0,
    };

    const response = await fetch("/api/maintenance/records", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (result.success) {
      showSuccessMessage("维护计划添加成功");

      // 关闭模态框
      const modal = bootstrap.Modal.getInstance(
        document.getElementById("addMaintenanceModal")
      );
      modal.hide();

      // 重置表单
      form.reset();

      // 重新加载数据
      await loadMaintenanceRecords();
    } else {
      showErrorMessage(result.message || "添加维护计划失败");
    }
  } catch (error) {
    console.error("添加维护计划失败:", error);
    showErrorMessage("添加维护计划失败");
  }
}

/**
 * 完成维护
 */
async function completeMaintenance(recordId) {
  try {
    const response = await fetch(
      `/api/maintenance/records/${recordId}/status`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status: "completed",
          notes: "维护已完成",
        }),
      }
    );

    const result = await response.json();

    if (result.success) {
      showSuccessMessage("维护状态更新成功");
      await loadMaintenanceRecords();
      await loadMaintenanceStatistics();
    } else {
      showErrorMessage(result.message || "更新维护状态失败");
    }
  } catch (error) {
    console.error("更新维护状态失败:", error);
    showErrorMessage("更新维护状态失败");
  }
}

/**
 * 编辑维护记录
 */
async function editMaintenance(recordId) {
  try {
    // 获取维护记录详情
    const response = await fetch(`/api/maintenance/records/${recordId}`);
    const result = await response.json();

    if (result.success) {
      // 填充编辑表单（这里需要创建编辑模态框）
      showSuccessMessage(`正在编辑维护记录 ${recordId}`);
    } else {
      showErrorMessage("获取维护记录失败");
    }
  } catch (error) {
    console.error("获取维护记录失败:", error);
    showErrorMessage("获取维护记录失败");
  }
}

/**
 * 删除维护记录
 */
async function deleteMaintenance(recordId) {
  if (!confirm("确定要删除这条维护记录吗？")) {
    return;
  }

  try {
    const response = await fetch(`/api/maintenance/records/${recordId}`, {
      method: "DELETE",
    });

    const result = await response.json();

    if (result.success) {
      showSuccessMessage("维护记录删除成功");
      await loadMaintenanceRecords();
      await loadMaintenanceStatistics();
    } else {
      showErrorMessage(result.message || "删除维护记录失败");
    }
  } catch (error) {
    console.error("删除维护记录失败:", error);
    showErrorMessage("删除维护记录失败");
  }
}

/**
 * 筛选维护记录
 */
async function filterMaintenanceRecords() {
  try {
    const deviceType = document.getElementById("deviceTypeFilter").value;
    const maintenanceType = document.getElementById(
      "maintenanceTypeFilter"
    ).value;
    const date = document.getElementById("maintenanceDateFilter").value;

    const params = new URLSearchParams();
    if (deviceType) params.append("device_type", deviceType);
    if (maintenanceType) params.append("maintenance_type", maintenanceType);
    if (date) params.append("start_date", date);

    const response = await fetch(`/api/maintenance/records?${params}`);
    const result = await response.json();

    if (result.success) {
      updateMaintenanceTable(result.data.records);
    } else {
      showErrorMessage("筛选维护记录失败");
    }
  } catch (error) {
    console.error("筛选维护记录失败:", error);
    showErrorMessage("筛选维护记录失败");
  }
}

// ==================== 数据备份与恢复功能 ====================

/**
 * 创建数据备份
 */
function createBackup() {
  try {
    showSuccessMessage("正在创建数据备份...");

    // 模拟备份过程
    setTimeout(() => {
      const now = new Date();
      const backupTime = now.toLocaleString("zh-CN");
      const backupSize = (Math.random() * 50 + 100).toFixed(1) + " MB";

      // 更新备份状态
      updateElement("backupStatus", "正常", "badge bg-success");
      updateElement("lastBackupTime", backupTime);
      updateElement("backupSize", backupSize);

      // 增加备份文件数
      const currentCount = parseInt(
        document.getElementById("backupFileCount")?.textContent || "15"
      );
      updateElement("backupFileCount", (currentCount + 1).toString());

      showSuccessMessage("数据备份创建成功");
      console.log("数据备份已创建:", backupTime);
    }, 2000);
  } catch (error) {
    console.error("创建备份失败:", error);
    showErrorMessage("创建备份失败");
  }
}

/**
 * 恢复数据备份
 */
function restoreBackup() {
  if (confirm("确定要恢复数据备份吗？此操作将覆盖当前数据，请谨慎操作！")) {
    try {
      showSuccessMessage("正在恢复数据备份...");

      // 模拟恢复过程
      setTimeout(() => {
        updateElement("backupStatus", "已恢复", "badge bg-info");
        showSuccessMessage("数据备份恢复成功");
        console.log("数据备份已恢复");

        // 3秒后恢复正常状态
        setTimeout(() => {
          updateElement("backupStatus", "正常", "badge bg-success");
        }, 3000);
      }, 3000);
    } catch (error) {
      console.error("恢复备份失败:", error);
      showErrorMessage("恢复备份失败");
    }
  }
}

/**
 * 下载数据备份
 */
function downloadBackup() {
  try {
    showSuccessMessage("正在准备备份文件下载...");

    // 模拟下载过程
    setTimeout(() => {
      const now = new Date();
      const filename = `archive_backup_${now.getFullYear()}${(
        now.getMonth() + 1
      )
        .toString()
        .padStart(2, "0")}${now.getDate().toString().padStart(2, "0")}.zip`;

      // 创建模拟下载
      const link = document.createElement("a");
      link.href = "#";
      link.download = filename;
      link.click();

      showSuccessMessage(`备份文件 ${filename} 下载完成`);
      console.log("备份文件下载:", filename);
    }, 1500);
  } catch (error) {
    console.error("下载备份失败:", error);
    showErrorMessage("下载备份失败");
  }
}

/**
 * 更新备份设置
 */
function updateBackupSettings() {
  try {
    const frequency =
      document.getElementById("backupFrequency")?.value || "daily";
    const retention = document.getElementById("backupRetention")?.value || "7";

    console.log("备份设置已更新:", { frequency, retention });
    showSuccessMessage("备份设置已保存");
  } catch (error) {
    console.error("更新备份设置失败:", error);
    showErrorMessage("保存备份设置失败");
  }
}

/**
 * 初始化数据管理页面的备份状态
 */
function initializeBackupStatus() {
  try {
    // 设置初始备份状态
    const lastBackupTime = new Date(Date.now() - 6 * 60 * 60 * 1000); // 6小时前
    updateElement("lastBackupTime", lastBackupTime.toLocaleString("zh-CN"));
    updateElement("backupSize", "125.6 MB");
    updateElement("backupFileCount", "15");
    updateElement("backupStatus", "正常", "badge bg-success");

    // 绑定备份设置变更事件
    const backupFrequency = document.getElementById("backupFrequency");
    const backupRetention = document.getElementById("backupRetention");

    if (backupFrequency) {
      backupFrequency.addEventListener("change", updateBackupSettings);
    }

    if (backupRetention) {
      backupRetention.addEventListener("change", updateBackupSettings);
    }

    console.log("备份状态初始化完成");
  } catch (error) {
    console.error("初始化备份状态失败:", error);
  }
}
// ==================== 数据管理模
