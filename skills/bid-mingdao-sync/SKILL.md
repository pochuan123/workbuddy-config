---
name: bid-mingdao-sync
description: 明道云BID数据同步与字段补充技能。当需要向明道云同步标讯数据、更新记录字段、补充缺失字段时使用此技能。包括MCP连接配置、字段映射、更新脚本等完整工作流程。
agent_created: true
---

# BID数据同步明道云技能

## 概述

用于将标讯BID数据同步到明道云工作表，并执行字段更新和补充操作。

## MCP连接配置

```
MCP URL: https://lcode.bj-fanuc.com.cn/mcp?HAP-Appkey=86f46b54ee693fa7&HAP-Sign=YjIyNjYxYmVhZmVlNzc2OTFkZmJkOWU3Zjg1ZDQxMDhhYzA4ODFhZTFhNzc0M2E1OTQ5MjJhMDQxZDY2NGY5OQ==
工作表ID: zlbx
```

## 明道云字段ID映射

### 基础字段（首次导入时已有）
| 字段名 | 字段ID |
|--------|--------|
| bid_id | 6a2d6c0c37004c0467cd3daf |
| title | 6a2d6c0c37004c0467cd3db0 |
| bid_type | 6a2d6c9bae5739e8ccd1ec1c |
| pub_time | 6a2d6c9bae5739e8ccd1ec1e |
| money_wan | 6a2d6c9bae5739e8ccd1ec20 |
| province | 6a2d6c9bae5739e8ccd1ec21 |
| city | 6a2d6c9bae5739e8ccd1ec22 |
| caller_name | 6a2d6c9bae5739e8ccd1ec24 |
| sm_names | 6a2d6c9bae5739e8ccd1ec28 |

### 需要补充的字段（通过update_record更新）
| 字段名 | 字段ID | 类型 | 说明 |
|--------|--------|------|------|
| url | 6a2d6c9bae5739e8ccd1ec25 | 文本 | 标讯详情链接 |
| bid_process | 6a2d6c9bae5739e8ccd1ec1d | 单选 | 招标进程 |
| money | 6a2d6c9bae5739e8ccd1ec1f | 数字 | 招标金额（元） |
| county | 6a2d6c9bae5739e8ccd1ec23 | 文本 | 地区-区县 |
| **相关度** | **6a2e0b70de47daaa6cc6c3fc** | **等级(0-5)** | **首次判定的相关度等级** |

## 数据文件说明

- `step1_bid_type1_data.json` - 完整BID数据源（包含url、bid_process、money等所有字段）
- `step2_relevance_analysis.json` - 相关性分析结果，包含高/中/低相关等级
- `step3_sync_441_results.json` - bid_id到record_id的映射关系

## 字段补充工作流程

### 1. 加载数据
```javascript
const step1Data = JSON.parse(fs.readFileSync('step1_bid_type1_data.json', 'utf8'));
const step1Map = {};
step1Data.forEach(r => step1Map[r.bid_id] = r);

const syncResults = JSON.parse(fs.readFileSync('step3_sync_441_results.json', 'utf8'));
const bidToRecordMap = {};
for (const d of syncResults.details) {
  bidToRecordMap[d.bid_id] = d.record_id;
}

const step2Data = JSON.parse(fs.readFileSync('step2_relevance_analysis.json', 'utf8'));
```

### 2. 字段ID常量
```javascript
const FIELD_IDS = {
  url: '6a2d6c9bae5739e8ccd1ec25',
  bid_process: '6a2d6c9bae5739e8ccd1ec1d',
  money: '6a2d6c9bae5739e8ccd1ec1f',
  county: '6a2d6c9bae5739e8ccd1ec23',
  relevance: '6a2e0b70de47daaa6cc6c3fc'  // 相关度等级(0-5)
};
```

### 3. 更新单条记录
```javascript
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
        ai_description: '补充缺失字段'
      }
    }
  });
  return { success: !result.error, recordId };
}
```

### 4. 相关度等级映射
```javascript
// step2中的level字段映射到相关度数值
function mapLevelToRelevance(level) {
  const mapping = { '高相关': 5, '中相关': 3, '低相关': 1 };
  return mapping[level] || 0;
}
```

### 5. 完整更新逻辑
```javascript
for (const hr of highRelevance) {
  const recordId = bidToRecordMap[hr.bid_id];
  const full = step1Map[hr.bid_id];
  
  if (!recordId || !full) continue;
  
  const fields = [];
  
  // url字段
  if (full.url) fields.push({ id: FIELD_IDS.url, value: full.url });
  
  // bid_process字段（单选）
  if (full.bid_process) fields.push({ id: FIELD_IDS.bid_process, value: [full.bid_process] });
  
  // money字段
  if (full.money !== undefined) fields.push({ id: FIELD_IDS.money, value: full.money });
  
  // 相关度字段（等级0-5）
  fields.push({ id: FIELD_IDS.relevance, value: mapLevelToRelevance(hr.level) });
  
  await updateRecord(recordId, fields);
  await delay(300);  // 避免限流
}
```

## 相关度字段说明

- 字段类型：**等级**，只能输入0-5的整数
- 值映射：
  - 高相关 → 5
  - 中相关 → 3
  - 低相关 → 1
  - 无相关 → 0

## 使用场景

1. **首次同步**：使用batch_import_to_mingdao.js创建新记录
2. **补充缺失字段**：使用supplement_fields.js更新已有记录
3. **更新相关度**：将step2分析的相关度等级写入明道云
