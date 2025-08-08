// 测试导航修复的脚本

console.log("开始测试导航功能...");

// 模拟点击智能盘点
setTimeout(() => {
  console.log("模拟点击智能盘点...");
  const inventoryLink = document.querySelector('[data-page="inventory"]');
  if (inventoryLink) {
    inventoryLink.click();

    // 检查导航状态
    setTimeout(() => {
      const activeLinks = document.querySelectorAll(".nav-link.active");
      console.log("当前激活的导航项数量:", activeLinks.length);

      activeLinks.forEach((link) => {
        const page = link.getAttribute("data-page");
        console.log("激活的导航项:", page);
      });

      // 检查当前页面
      console.log("当前页面:", window.currentPage);

      // 检查页面显示状态
      const visiblePages = document.querySelectorAll(
        '.page-content[style*="block"]'
      );
      console.log("可见页面数量:", visiblePages.length);

      visiblePages.forEach((page) => {
        console.log("可见页面ID:", page.id);
      });
    }, 100);
  } else {
    console.log("未找到智能盘点导航链接");
  }
}, 1000);

// 模拟点击仪表盘
setTimeout(() => {
  console.log("模拟点击仪表盘...");
  const dashboardLink = document.querySelector('[data-page="dashboard"]');
  if (dashboardLink) {
    dashboardLink.click();

    // 检查导航状态
    setTimeout(() => {
      const activeLinks = document.querySelectorAll(".nav-link.active");
      console.log("当前激活的导航项数量:", activeLinks.length);

      activeLinks.forEach((link) => {
        const page = link.getAttribute("data-page");
        console.log("激活的导航项:", page);
      });
    }, 100);
  }
}, 2000);
