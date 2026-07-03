# 明道云MCP API 参考

## MCP连接信息

```
MCP端点: https://lcode.bj-fanuc.com.cn/mcp?HAP-Appkey=86f46b54ee693fa7&HAP-Sign=YjIyNjYxYmVhZmVlNzc2OTFkZmJkOWU3Zjg1ZDQxMDhhYzA4ODFhZTFhNzc0M2E1OTQ5MjJhMDQxZDY2NGY5OQ==
工作表ID: zlbx
协议版本: 2024-11-05
```

## MCP请求格式

```javascript
const body = {
  jsonrpc: '2.0',
  id: Date.now(),
  method: 'tools/call',
  params: {
    name: 'tool_name',
    arguments: { /* 工具参数 */ }
  }
};
```

## 工具列表

### 1. create_record - 创建记录

```javascript
{
  name: 'create_record',
  arguments: {
    worksheet_id: 'zlbx',
    fields: [
      { id: '字段ID', value: '值' }
    ],
    triggerWorkflow: false,
    ai_description: '描述'
  }
}
```

### 2. update_record - 更新记录

```javascript
{
  name: 'update_record',
  arguments: {
    worksheet_id: 'zlbx',
    row_id: 'record_id',
    fields: [
      { id: '字段ID', value: '新值' }
    ],
    ai_description: '描述'
  }
}
```

### 3. batch_create_records - 批量创建

```javascript
{
  name: 'batch_create_records',
  arguments: {
    worksheet_id: 'zlbx',
    records: [
      { fields: [{ id: '字段ID', value: '值' }] }
    ],
    triggerWorkflow: false
  }
}
```

### 4. get_records - 查询记录

```javascript
{
  name: 'get_records',
  arguments: {
    worksheet_id: 'zlbx',
    filter: {
      conjunction: 'and',
      conditions: [
        { field_name: 'bid_id', operator: 'contains', value: '123' }
      ]
    },
    page_size: 100
  }
}
```

### 5. get_worksheet_structure - 获取工作表结构

```javascript
{
  name: 'get_worksheet_structure',
  arguments: {
    worksheet_id: 'zlbx'
  }
}
```

## 字段类型与值格式

| 字段类型 | 值格式 | 示例 |
|---------|-------|------|
| 文本 | string | `"hello"` |
| 数字 | number | `123` |
| 单选 | array | `["选项1"]` |
| 多选 | array | `["选项1", "选项2"]` |
| 等级 | number | `5` |
| 日期 | string | `"2026-06-14"` |
| 复选框 | boolean | `true` |

## 明道云字段ID完整列表

### zlbx工作表

| 字段名(中文) | 字段ID | 类型 |
|------------|--------|------|
| bid_id | 6a2d6c0c37004c0467cd3daf | 文本 |
| title | 6a2d6c0c37004c0467cd3db0 | 文本 |
| bid_type | 6a2d6c9bae5739e8ccd1ec1c | 单选 |
| bid_process | 6a2d6c9bae5739e8ccd1ec1d | 单选 |
| pub_time | 6a2d6c9bae5739e8ccd1ec1e | 日期 |
| money | 6a2d6c9bae5739e8ccd1ec1f | 数字 |
| money_wan | 6a2d6c9bae5739e8ccd1ec20 | 数字 |
| province | 6a2d6c9bae5739e8ccd1ec21 | 文本 |
| city | 6a2d6c9bae5739e8ccd1ec22 | 文本 |
| county | 6a2d6c9bae5739e8ccd1ec23 | 文本 |
| caller_name | 6a2d6c9bae5739e8ccd1ec24 | 文本 |
| caller_id | 6a2d6c9bae5739e8ccd1ec25 | 文本/链接 |
| url | 6a2d6c9bae5739e8ccd1ec2c | 文本 |
| caller_base_type | 6a2d6c9bae5739e8ccd1ec26 | 文本 |
| caller_type | 6a2d6c9bae5739e8ccd1ec27 | 文本 |
| sm_names | 6a2d6c9bae5739e8ccd1ec28 | 多选 |
| signup_time | 6a2d6c9bae5739e8ccd1ec29 | 日期 |
| tender_time | 6a2d6c9bae5739e8ccd1ec2a | 日期 |
| agency_name | 6a2d6c9bae5739e8ccd1ec2b | 文本 |
| **相关度** | **6a2e0b70de47daaa6cc6c3fc** | **等级(0-5)** |

## 错误处理

```javascript
if (result.error) {
  console.error('MCP错误:', result.error.message);
  return { success: false, error: result.error };
}
```

## 限流建议

- 单次请求间隔: 300ms
- 批量操作时建议设置更长的间隔
- 避免并发请求
