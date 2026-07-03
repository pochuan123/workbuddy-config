---
name: oa-week-summary
description: This skill should be used when the user wants to extract their week
  summary content from the OA system (泛微OA). It handles login, navigation to the
  week summary section, and extracting the pure text content of the week's
  summary. Perfect for recurring tasks like "查看本周周总结" or "提取X月X日的周总结".
agent_created: true
disable: true
---

# OA 周总结提取

## Overview

本skill用于从泛微OA系统（http://eoa.bj-fanuc.com.cn）提取用户的周工作总结内容。自动处理登录、导航、内容提取全流程。

## 系统信息

- **OA系统URL**: http://eoa.bj-fanuc.com.cn
- **系统类型**: 泛微OA (Domino-based workflow)
- **周总结模块**: Application/PersonalSummary/WeekWordSummary_personal_wanglanzhou.nsf

## 凭证配置

| 字段 | 说明 |
|------|------|
| 用户名 | wanglanzhou |
| 密码 | @zhaoyan0711 |

**注意**: 如凭证变更，需更新脚本中的配置。

## 工作流程

### Step 1: 登录OA系统

使用Playwright CLI登录OA系统：

```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // 设置导航超时
  page.setDefaultTimeout(30000);
  
  // 登录
  await page.goto('http://eoa.bj-fanuc.com.cn');
  await page.fill('input[name=\"username\"]', 'wanglanzhou');
  await page.fill('input[name=\"password\"]', '@zhaoyan0711');
  await page.click('button[type=\"submit\"]');
  
  // 等待登录完成
  await page.waitForURL('**/eoa**', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(2000);
  
  console.log('LOGIN_SUCCESS');
  await browser.close();
})();
"
```

### Step 2: 定位周总结入口

在首页点击"周总结"按钮：

```javascript
// 查找并点击周总结按钮
const weekSummaryBtn = await page.locator('text=周总结').first();
await weekSummaryBtn.click();
await page.waitForTimeout(2000);
```

### Step 3: 获取周总结列表

周总结列表通过AJAX动态加载，需等待内容加载完成：

```javascript
// 等待列表加载
await page.waitForSelector('a[href*=\"AppDoneView\"]', { timeout: 15000 });

// 列出所有周总结链接
const links = await page.locator('a[href*=\"AppDoneView\"]').all();
for (const link of links) {
  const text = await link.textContent();
  const href = await link.getAttribute('href');
  console.log(text + ' | ' + href);
}
```

### Step 4: 打开指定日期的周总结

根据日期找到对应的"查看"链接并点击：

```javascript
// 点击对应日期的查看链接
const viewLink = await page.locator('a:has-text(\"查看\")').first();
await viewLink.click();
await page.waitForTimeout(3000);
```

### Step 5: 提取本周总结内容

在周总结详情页提取"本周总结"字段的纯文本：

```javascript
// 获取页面内容
const content = await page.content();

// 提取"本周总结："后面的内容
const match = content.match(/本周总结[：:]\s*([\s\S]*?)(?=本周计划|下周计划|二、|三、|$)/i);
if (match) {
  // 清理HTML标签，获取纯文本
  let summary = match[1]
    .replace(/<[^>]*>/g, '')  // 移除HTML标签
    .replace(/&nbsp;/g, ' ')   // 替换空格
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')     // 合并空格
    .trim();
  
  console.log(summary);
}
```

## 完整脚本模板

将以下脚本保存为 `.js` 文件执行：

```javascript
// oa-week-summary-extract.js
const { chromium } = require('playwright');

const CONFIG = {
  url: 'http://eoa.bj-fanuc.com.cn',
  username: 'wanglanzhou',
  password: '@zhaoyan0711'
};

async function extractWeekSummary(targetDate) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  try {
    // 1. 登录
    console.log('正在登录OA系统...');
    await page.goto(CONFIG.url);
    await page.fill('input[name="username"]', CONFIG.username);
    await page.fill('input[name="password"]', CONFIG.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    console.log('登录成功');

    // 2. 点击周总结
    console.log('正在定位周总结入口...');
    const weekBtn = await page.locator('text=周总结').first();
    await weekBtn.click();
    await page.waitForTimeout(3000);

    // 3. 等待列表加载并获取链接
    console.log('正在加载周总结列表...');
    await page.waitForSelector('a[href*="AppDoneView"]', { timeout: 15000 });

    // 4. 点击第一条查看链接（通常是最新的）
    const viewLink = await page.locator('a:has-text("查看")').first();
    await viewLink.click();
    await page.waitForTimeout(3000);

    // 5. 提取内容
    const content = await page.content();
    const match = content.match(/本周总结[：:]\s*([\s\S]*?)(?=本周计划|下周计划|二、|三、|$)/i);
    
    if (match) {
      const summary = match[1]
        .replace(/<[^>]*>/g, '')
        .replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
      console.log('=== 本周总结 ===');
      console.log(summary);
      return summary;
    }

    return null;
  } finally {
    await browser.close();
  }
}

// 执行
extractWeekSummary().then(console.log).catch(console.error);
```

## 注意事项

1. **动态加载**: 周总结列表使用AJAX动态加载，必须等待内容加载完成后再操作
2. **超时处理**: 网络较慢时可适当增加timeout
3. **会话保持**: 如需多次操作，可在脚本中复用browser实例
4. **内容格式**: 提取的内容为纯文本，图片链接已过滤

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 找不到周总结按钮 | 检查首页布局，可能需要先点击"工作"或"个人"菜单 |
| 列表加载超时 | 增加waitForTimeout时间或检查网络连接 |
| 内容为空 | 页面可能尚未完全加载，增加等待时间 |
| 登录失败 | 检查凭证是否正确，或系统是否需要验证码 |
