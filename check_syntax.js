// 简单的语法检查
try {
  // 模拟浏览器环境
  global.window = global;

  // 加载api.js内容
  const fs = require("fs");
  const apiCode = fs.readFileSync("frontend/js/api.js", "utf8");

  // 尝试执行代码
  eval(apiCode);

  console.log("✓ api.js语法检查通过");

  // 检查ApiClient是否正确定义
  if (typeof window.ApiClient !== "undefined") {
    console.log("✓ window.ApiClient已定义");
  } else {
    console.log("✗ window.ApiClient未定义");
  }

  // 检查api实例是否创建
  if (typeof window.api !== "undefined") {
    console.log("✓ window.api实例已创建");
  } else {
    console.log("✗ window.api实例未创建");
  }
} catch (error) {
  console.log("✗ JavaScript错误:", error.message);
}
