/**
 * API调用封装模块
 * 提供与后端API交互的统一接口
 */

// 避免重复声明
if (typeof ApiClient === "undefined") {
  class ApiClient {
    constructor() {
      this.baseUrl = "http://127.0.0.1:5000/api";
      this.timeout = 10000; // 10秒超时
    }

    /**
     * 通用API请求方法
     * @param {string} endpoint - API端点
     * @param {object} options - 请求选项
     * @returns {Promise} API响应
     */
    async request(endpoint, options = {}) {
      const url = `${this.baseUrl}${endpoint}`;
      const config = {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        timeout: this.timeout,
        ...options,
      };

      try {
        const response = await fetch(url, config);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
      } catch (error) {
        console.error(`API请求失败 [${endpoint}]:`, error);
        // 只记录错误，不显示用户提示
        throw error;
      }
    }

    /**
     * GET请求
     * @param {string} endpoint - API端点
     * @param {object} params - 查询参数
     * @returns {Promise} API响应
     */
    async get(endpoint, params = {}) {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `${endpoint}?${queryString}` : endpoint;
      return this.request(url);
    }

    /**
     * POST请求
     * @param {string} endpoint - API端点
     * @param {object} data - 请求数据
     * @returns {Promise} API响应
     */
    async post(endpoint, data = {}) {
      return this.request(endpoint, {
        method: "POST",
        body: JSON.stringify(data),
      });
    }

    /**
     * PUT请求
     * @param {string} endpoint - API端点
     * @param {object} data - 请求数据
     * @returns {Promise} API响应
     */
    async put(endpoint, data = {}) {
      return this.request(endpoint, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    }

    /**
     * DELETE请求
     * @param {string} endpoint - API端点
     * @returns {Promise} API响应
     */
    async delete(endpoint) {
      return this.request(endpoint, {
        method: "DELETE",
      });
    }

    /**
     * 错误处理
     * @param {Error} error - 错误对象
     */
    handleError(error) {
      let message = "网络请求失败";

      if (error.name === "TypeError" && error.message.includes("fetch")) {
        message = "无法连接到服务器";
      } else if (error.message.includes("HTTP 404")) {
        message = "请求的资源不存在";
      } else if (error.message.includes("HTTP 500")) {
        message = "服务器内部错误";
      } else if (error.message.includes("timeout")) {
        message = "请求超时";
      } else if (error.message) {
        message = error.message;
      }

      // 只记录错误，不显示用户提示（除非是明确的用户操作）
      console.error("API请求错误:", message);
    }

    /**
     * 显示错误消息
     * @param {string} message - 错误消息
     */
    showError(message) {
      // 只在控制台记录错误，避免频繁的用户提示
      console.error("API错误:", message);

      // 只有在明确的用户操作失败时才显示错误提示
      if (
        message.includes("保存") ||
        message.includes("删除") ||
        message.includes("添加") ||
        message.includes("更新")
      ) {
        const alertDiv = document.createElement("div");
        alertDiv.className =
          "alert alert-danger alert-dismissible fade show position-fixed";
        alertDiv.style.cssText =
          "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
        alertDiv.innerHTML = `
              <i class="bi bi-exclamation-triangle-fill"></i>
              <strong>操作失败：</strong> ${message}
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          `;

        document.body.appendChild(alertDiv);

        // 3秒后自动移除
        setTimeout(() => {
          if (alertDiv.parentNode) {
            alertDiv.remove();
          }
        }, 3000);
      }
    }

    /**
     * 显示成功消息
     * @param {string} message - 成功消息
     */
    showSuccess(message) {
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

    // ==================== 系统API ====================

    /**
     * 获取系统健康状态
     */
    async getSystemHealth() {
      return this.get("/health");
    }

    /**
     * 获取系统信息
     */
    async getSystemInfo() {
      return this.get("/system/info");
    }

    /**
     * 获取系统性能数据
     */
    async getSystemPerformance() {
      return this.get("/system/performance");
    }

    /**
     * 获取系统性能历史数据
     */
    async getSystemPerformanceHistory() {
      return this.get("/system/performance/history");
    }

    // ==================== 环境监测API ====================

    /**
     * 获取实时环境数据
     */
    async getEnvironmentData() {
      return this.get("/environment/data");
    }

    /**
     * 获取环境历史数据
     * @param {object} params - 查询参数 {start_time, end_time, sensor_id}
     */
    async getEnvironmentHistory(params = {}) {
      return this.get("/environment/history", params);
    }

    /**
     * 设置环境告警阈值
     * @param {object} thresholds - 阈值配置
     */
    async setEnvironmentThresholds(thresholds) {
      return this.post("/environment/thresholds", thresholds);
    }

    // ==================== RFID设备API ====================

    /**
     * 获取RFID设备列表
     */
    async getRfidDevices() {
      return this.get("/rfid/devices");
    }

    /**
     * 添加RFID设备
     * @param {object} device - 设备信息
     */
    async addRfidDevice(device) {
      return this.post("/rfid/devices", device);
    }

    /**
     * 更新RFID设备配置
     * @param {number} deviceId - 设备ID
     * @param {object} config - 设备配置
     */
    async updateRfidDevice(deviceId, config) {
      return this.put(`/rfid/devices/${deviceId}`, config);
    }

    /**
     * 获取RFID标签列表
     */
    async getRfidTags() {
      return this.get("/rfid/tags");
    }

    /**
     * 添加RFID标签
     * @param {object} tag - 标签信息
     */
    async addRfidTag(tag) {
      return this.post("/rfid/tags", tag);
    }

    // ==================== 档案追踪API ====================

    /**
     * 获取档案列表
     * @param {object} params - 查询参数
     */
    async getArchives(params = {}) {
      return this.get("/tracking/archives", params);
    }

    /**
     * 获取档案位置信息
     * @param {number} archiveId - 档案ID
     */
    async getArchiveLocation(archiveId) {
      return this.get(`/tracking/location/${archiveId}`);
    }

    /**
     * 获取档案移动历史
     * @param {number} archiveId - 档案ID
     */
    async getArchiveHistory(archiveId) {
      return this.get(`/tracking/history/${archiveId}`);
    }

    // ==================== 盘点系统API ====================

    /**
     * 开始盘点任务
     * @param {object} task - 盘点任务信息
     */
    async startInventoryTask(task) {
      return this.post("/inventory/start", task);
    }

    /**
     * 获取盘点状态
     * @param {number} taskId - 任务ID
     */
    async getInventoryStatus(taskId) {
      return this.get(`/inventory/status?task_id=${taskId}`);
    }

    /**
     * 获取盘点报告
     * @param {number} taskId - 任务ID
     */
    async getInventoryReport(taskId) {
      return this.get(`/inventory/report?task_id=${taskId}`);
    }

    // ==================== 告警管理API ====================

    /**
     * 获取告警列表
     * @param {object} params - 查询参数
     */
    async getAlerts(params = {}) {
      return this.get("/alerts", params);
    }

    /**
     * 处理告警
     * @param {number} alertId - 告警ID
     * @param {object} handleInfo - 处理信息
     */
    async handleAlert(alertId, handleInfo) {
      return this.put(`/alerts/${alertId}/handle`, handleInfo);
    }

    /**
     * 设置告警规则
     * @param {object} rules - 告警规则
     */
    async setAlertRules(rules) {
      return this.post("/alerts/rules", rules);
    }

    // ==================== 统计报表API ====================

    /**
     * 获取环境趋势报表
     * @param {object} params - 查询参数
     */
    async getEnvironmentReport(params = {}) {
      return this.get("/reports/environment", params);
    }

    /**
     * 获取档案流动报表
     * @param {object} params - 查询参数
     */
    async getArchiveFlowReport(params = {}) {
      return this.get("/reports/archive-flow", params);
    }

    // ==================== 设备维护API ====================

    /**
     * 获取维护记录
     * @param {object} params - 查询参数
     */
    async getMaintenanceRecords(params = {}) {
      return this.get("/maintenance/records", params);
    }

    /**
     * 添加维护记录
     * @param {object} record - 维护记录
     */
    async addMaintenanceRecord(record) {
      return this.post("/maintenance/records", record);
    }

    // ==================== 系统配置API ====================

    /**
     * 获取系统配置
     * @param {string} category - 配置分类
     */
    async getSystemConfig(category = "") {
      return this.get("/settings/config", category ? { category } : {});
    }

    /**
     * 更新系统配置
     * @param {object} config - 配置信息
     */
    async updateSystemConfig(config) {
      return this.post("/settings/config", config);
    }
  }
}

// 创建全局API客户端实例
if (typeof window.api === "undefined") {
  window.api = new ApiClient();
}
