/**
 * OA周总结提取脚本
 * 用于从泛微OA系统提取周工作总结内容
 * 
 * 使用方法: node oa-week-summary-extract.js [日期范围]
 * 示例: node oa-week-summary-extract.js "2026-05-25至2026-05-31"
 */

const { chromium } = require('playwright');

// 配置
const CONFIG = {
  // OA系统URL
  url: 'http://eoa.bj-fanuc.com.cn',
  // 登录凭证
  username: 'wanglanzhou',
  password: '@zhaoyan0711',
  // 超时设置(毫秒)
  timeout: {
    navigation: 30000,
    element: 15000,
    wait: 3000
  }
};

/**
 * 清理HTML文本，提取纯文本内容
 */
function cleanHtmlText(html) {
  return html
    .replace(/<[^>]*>/g, '')           // 移除HTML标签
    .replace(/&nbsp;/g, ' ')           // 替换不换行空格
    .replace(/&lt;/g, '<')              // 还原HTML实体
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/<br\s*\/?>/gi, '\n')     // 保留换行
    .replace(/\s+/g, ' ')              // 合并多余空格
    .replace(/^\s+|\s+$/g, '')         // 去除首尾空格
    .trim();
}

/**
 * 提取本周总结内容
 */
function extractWeekSummaryContent(html) {
  // 匹配"本周总结："后面的内容，直到"本周计划"或其他段落标记
  const patterns = [
    /本周总结[：:]\s*([\s\S]*?)(?=本周计划|下周计划|二、|三、|四、|$)/i,
    /本周工作总结[：:]\s*([\s\S]*?)(?=本周计划|下周计划|二、|三、|四、|$)/i,
    /工作内容[：:]\s*([\s\S]*?)(?=本周计划|下周计划|二、|三、|四、|$)/i
  ];

  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match && match[1].trim()) {
      return cleanHtmlText(match[1]);
    }
  }
  return null;
}

/**
 * 主函数
 */
async function extractWeekSummary(targetDateRange) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // 设置默认超时
  page.setDefaultTimeout(CONFIG.timeout.navigation);

  try {
    console.log('=== OA周总结提取工具 ===\n');
    
    // Step 1: 登录
    console.log('1. 正在登录OA系统...');
    await page.goto(CONFIG.url);
    await page.waitForTimeout(1000);
    
    // 填写登录表单
    await page.fill('input[name="username"]', CONFIG.username);
    await page.fill('input[name="password"]', CONFIG.password);
    await page.click('button[type="submit"]');
    
    // 等待登录完成
    await page.waitForTimeout(CONFIG.timeout.wait);
    console.log('   登录成功 ✓');

    // Step 2: 定位周总结入口
    console.log('2. 正在定位周总结入口...');
    const weekBtn = await page.locator('text=周总结').first();
    await weekBtn.click();
    await page.waitForTimeout(CONFIG.timeout.wait);
    console.log('   已进入周总结页面 ✓');

    // Step 3: 等待列表加载
    console.log('3. 正在加载周总结列表...');
    await page.waitForSelector('a[href*="AppDoneView"]', { 
      timeout: CONFIG.timeout.element 
    });
    console.log('   列表加载完成 ✓');

    // Step 4: 列出可用的周总结
    const links = await page.locator('a[href*="AppDoneView"]').all();
    console.log(`   发现 ${links.length} 条周总结记录`);

    // Step 5: 点击查看最新的周总结
    console.log('4. 正在打开周总结详情...');
    const viewLink = await page.locator('a:has-text("查看")').first();
    await viewLink.click();
    await page.waitForTimeout(CONFIG.timeout.wait);
    console.log('   已打开周总结详情 ✓');

    // Step 6: 提取内容
    console.log('5. 正在提取本周总结内容...\n');
    const content = await page.content();
    const summary = extractWeekSummaryContent(content);

    if (summary) {
      console.log('=== 本周总结内容 ===\n');
      console.log(summary);
      console.log('\n=== 内容提取完成 ===');
      
      // 返回结果供后续使用
      return summary;
    } else {
      console.log('未找到本周总结内容');
      return null;
    }

  } catch (error) {
    console.error('执行出错:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

// 执行
const targetDate = process.argv[2] || '';
extractWeekSummary(targetDate)
  .then(result => {
    if (result) {
      process.exit(0);
    } else {
      process.exit(1);
    }
  })
  .catch(() => process.exit(1));
