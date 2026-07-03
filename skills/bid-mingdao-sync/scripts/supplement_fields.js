const https = require('https');
const fs = require('fs');

const path = 'C:/Users/wanglanzhou/WorkBuddy/2026-06-13-17-46-22/';

// 读取数据
const step1Data = JSON.parse(fs.readFileSync(path + 'step1_bid_type1_data.json', 'utf8'));
const step1Map = {};
step1Data.forEach(r => step1Map[r.bid_id] = r);

const syncResults = JSON.parse(fs.readFileSync(path + 'step3_sync_441_results.json', 'utf8'));
const bidToRecordMap = {};
for (const d of syncResults.details) {
  bidToRecordMap[d.bid_id] = d.record_id;
}

const step2Data = JSON.parse(fs.readFileSync(path + 'step2_relevance_analysis.json', 'utf8'));
const highRelevance = step2Data.high_relevance;

// MCP连接配置
const mcpUrl = 'https://lcode.bj-fanuc.com.cn/mcp?HAP-Appkey=86f46b54ee693fa7&HAP-Sign=YjIyNjYxYmVhZmVlNzc2OTFkZmJkOWU3Zjg1ZDQxMDhhYzA4ODFhZTFhNzc0M2E1OTQ5MjJhMDQxZDY2NGY5OQ==';
const urlObj = new URL(mcpUrl);

// 明道云字段ID映射
const FIELD_IDS = {
  url: '6a2d6c9bae5739e8ccd1ec25',           // 链接
  bid_process: '6a2d6c9bae5739e8ccd1ec1d',   // bid_process（单选）
  money: '6a2d6c9bae5739e8ccd1ec1f',         // money（数字）
  county: '6a2d6c9bae5739e8ccd1ec23',        // county（文本）
  relevance: '6a2e0b70de47daaa6cc6c3fc'       // 相关度（等级0-5）
};

// 相关度等级映射
function mapLevelToRelevance(level) {
  const mapping = { '高相关': 5, '中相关': 3, '低相关': 1 };
  return mapping[level] || 0;
}

function sendMcp(body) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(body);
    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Accept': 'application/json, text/event-stream',
        'MCP-Protocol-Version': '2024-11-05'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed);
        } catch (e) {
          resolve({ raw: data.substring(0, 500) });
        }
      });
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function updateRecord(recordId, fields) {
  const result = await sendMcp({
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: 'update_record',
      arguments: {
        worksheet_id: 'zlbx',
        row_id: recordId,
        fields: fields.map(f => ({ id: f.id, value: f.value })),
        ai_description: '补充缺失字段+相关度'
      }
    }
  });

  if (result.error) {
    return { success: false, recordId, error: result.error.message || result.error };
  }
  return { success: true, recordId };
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('============================================================');
  console.log('       补充缺失字段+相关度 - 明道云更新程序                   ');
  console.log('============================================================');
  console.log(`\n高相关记录数: ${highRelevance.length}`);

  // 准备更新数据
  const updates = [];
  for (const hr of highRelevance) {
    const recordId = bidToRecordMap[hr.bid_id];
    const full = step1Map[hr.bid_id];

    if (!recordId) {
      console.log(`警告: 未找到bid_id=${hr.bid_id}的record_id`);
      continue;
    }
    if (!full) {
      console.log(`警告: 未找到bid_id=${hr.bid_id}的完整数据`);
      continue;
    }

    const fields = [];

    // url字段
    if (full.url) {
      fields.push({ id: FIELD_IDS.url, value: full.url });
    }

    // bid_process字段（单选）
    if (full.bid_process) {
      fields.push({ id: FIELD_IDS.bid_process, value: [full.bid_process] });
    }

    // money字段
    if (full.money !== undefined && full.money !== null) {
      fields.push({ id: FIELD_IDS.money, value: full.money });
    }

    // county字段
    if (full.county) {
      fields.push({ id: FIELD_IDS.county, value: full.county });
    }

    // 相关度字段（等级0-5）
    const relevanceValue = mapLevelToRelevance(hr.level);
    fields.push({ id: FIELD_IDS.relevance, value: relevanceValue });

    if (fields.length > 0) {
      updates.push({
        bid_id: hr.bid_id,
        record_id: recordId,
        title: hr.title,
        level: hr.level,
        fields: fields
      });
    }
  }

  console.log(`准备更新 ${updates.length} 条记录`);

  // 统计字段覆盖
  let urlCount = 0, processCount = 0, moneyCount = 0, countyCount = 0, relevanceCount = 0;
  updates.forEach(u => {
    u.fields.forEach(f => {
      if (f.id === FIELD_IDS.url) urlCount++;
      if (f.id === FIELD_IDS.bid_process) processCount++;
      if (f.id === FIELD_IDS.money) moneyCount++;
      if (f.id === FIELD_IDS.county) countyCount++;
      if (f.id === FIELD_IDS.relevance) relevanceCount++;
    });
  });

  console.log('\n字段统计:');
  console.log(`  url: ${urlCount} 条`);
  console.log(`  bid_process: ${processCount} 条`);
  console.log(`  money: ${moneyCount} 条`);
  console.log(`  county: ${countyCount} 条`);
  console.log(`  relevance: ${relevanceCount} 条 (全部)`);

  // 显示示例
  console.log('\n示例更新数据:');
  if (updates.length > 0) {
    console.log(`  bid_id: ${updates[0].bid_id}`);
    console.log(`  record_id: ${updates[0].record_id}`);
    console.log(`  title: ${updates[0].title}`);
    console.log(`  level: ${updates[0].level}`);
    console.log(`  fields: ${JSON.stringify(updates[0].fields, null, 2)}`);
  }

  // 询问是否继续
  const args = process.argv.slice(2);
  if (args.includes('--dry-run')) {
    console.log('\n=== DRY RUN 模式，不执行更新 ===');
    fs.writeFileSync(path + 'supplement_with_relevance_data.json', JSON.stringify(updates, null, 2));
    console.log('已保存更新数据到 supplement_with_relevance_data.json');
    return;
  }

  // 执行更新
  let successCount = 0;
  let failCount = 0;
  const failures = [];

  console.log('\n开始更新...');

  for (let i = 0; i < updates.length; i++) {
    const update = updates[i];
    const result = await updateRecord(update.record_id, update.fields);

    if (result.success) {
      successCount++;
    } else {
      failCount++;
      failures.push({
        bid_id: update.bid_id,
        record_id: update.record_id,
        error: result.error
      });
    }

    // 每10条输出进度
    if ((i + 1) % 10 === 0 || i === updates.length - 1) {
      console.log(`进度: ${i + 1}/${updates.length} (成功: ${successCount}, 失败: ${failCount})`);
    }

    // 延迟避免限流
    if (i < updates.length - 1) {
      await delay(300);
    }
  }

  console.log(`\n更新完成!`);
  console.log(`成功: ${successCount}`);
  console.log(`失败: ${failCount}`);

  // 保存结果
  fs.writeFileSync(path + 'supplement_with_relevance_results.json', JSON.stringify({
    total: updates.length,
    success: successCount,
    failed: failCount,
    failures
  }, null, 2));

  if (failures.length > 0) {
    console.log('\n失败记录:');
    failures.forEach(f => console.log(`  ${f.bid_id}: ${f.error}`));
  }
}

main().catch(console.error);
