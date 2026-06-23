# TTS API 接口文档

| 属性     | 值              |
| ------ | -------------- |
| 文档版本   | 1.1.0          |
| API 版本 | v1             |
| 更新日期   | 2026-06-15     |
| 协议     | HTTPS / WSS    |
| 字符编码   | UTF-8          |

---

## 1. 接口概述

本服务基于 OmniVoice 提供企业级文本转语音（TTS）能力，支持预设音色与零样本声音克隆。

### 1.1 服务能力

| 能力       | 协议        | 说明                    |
| -------- | --------- | --------------------- |
| 获取音色列表   | HTTP GET  | 查询可用预设音色及元数据          |
| 非流式语音合成  | HTTP POST | 一次性返回完整音频（适合短文本）      |
| 流式语音合成   | WebSocket | 按句/段推送音频（适合长文本、低延迟场景） |
| 服务健康检查   | HTTP GET  | 用于负载均衡探活与运维监控         |

### 1.2 环境与 Base URL

| 环境   | Base URL 示例                        |
| ---- | ---------------------------------- |
| 生产   | `https://api.example.com`          |
| 预发布  | `https://api-staging.example.com`  |
| 本地开发 | `http://localhost:8000`          |

所有 HTTP 接口前缀：`/api/v1/tts`  
流式接口地址：`ws://{host}/api/v1/tts/stream`

### 1.3 音频输出规范

| 属性        | 默认值    | 说明                          |
| --------- | ------ | --------------------------- |
| 采样率       | 24000  | Hz，固定输出                     |
| 声道        | 1      | 单声道                         |
| 位深        | 16     | PCM 16-bit                  |
| 默认编码      | wav    | 支持 `wav` / `pcm` / `mp3`（可选） |
| 传输格式（HTTP） | base64 | 见 §3.3，亦支持直接返回二进制           |

---

## 2. 通用约定

### 2.1 认证

所有接口（HTTP 与 WebSocket）均需在请求头携带 API Key：

```http
Authorization: Bearer <API_KEY>
```

WebSocket 连接时，可在握手阶段通过 Query 或 Header 传递（二选一，推荐 Header）：

```http
Authorization: Bearer <API_KEY>
```

认证失败统一返回：

```json
{
  "code": 4010,
  "message": "unauthorized",
  "request_id": "req_20260615143001_a1b2c3"
}
```

HTTP 状态码：`401 Unauthorized`

### 2.2 公共请求头

| 请求头              | 必填 | 说明                                      |
| ---------------- | -- | --------------------------------------- |
| Authorization    | 是  | Bearer Token                            |
| Content-Type     | 是* | `application/json`（POST 请求必填）            |
| X-Request-Id     | 否  | 客户端请求 ID，用于链路追踪；未传时服务端自动生成            |
| X-Idempotency-Key | 否  | 幂等键（建议 UUID），24h 内相同键的重复 POST 返回同一结果 |

### 2.3 统一响应结构（HTTP）

成功与业务失败均使用 **HTTP 200**，通过 body 中 `code` 区分；仅协议层错误使用 4xx/5xx。

```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_20260615143001_a1b2c3",
  "timestamp": 1718442601000,
  "data": {}
}
```

| 字段         | 类型     | 说明                    |
| ---------- | ------ | --------------------- |
| code       | int    | 业务状态码，`0` 表示成功        |
| message    | string | 人类可读描述                |
| request_id | string | 请求唯一标识，排查问题时请提供此字段     |
| timestamp  | long   | 服务端响应时间戳（Unix 毫秒）     |
| data       | object | 业务数据；失败时可为 `null` 或省略 |

### 2.4 HTTP 状态码映射

| HTTP 状态码 | 场景                          |
| -------- | --------------------------- |
| 200      | 请求已处理（含业务失败，见 `code` 字段）   |
| 400      | 请求体 JSON 非法、缺少必填头           |
| 401      | 认证失败                        |
| 403      | 无权限（如租户未开通 TTS）             |
| 404      | 路径不存在                       |
| 413      | 请求体过大                       |
| 429      | 触发限流                        |
| 500      | 网关或服务不可恢复错误                 |
| 503      | 服务过载或维护中                    |

### 2.5 限流

默认配额（可按租户调整）：

| 维度       | 默认值              |
| -------- | ---------------- |
| QPS      | 10 req/s / API Key |
| 日调用量     | 100,000 次        |
| 并发 WebSocket | 5 路 / API Key     |

触发限流时 HTTP 返回 `429`，响应头示例：

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1718442660
Retry-After: 1
```

```json
{
  "code": 4290,
  "message": "rate limit exceeded",
  "request_id": "req_20260615143001_a1b2c3"
}
```

---

## 3. 获取音色列表

### 3.1 接口地址

```http
GET /api/v1/tts/voices
```

### 3.2 请求参数（Query）

| 参数       | 类型     | 必填 | 默认值 | 说明                          |
| -------- | ------ | -- | --- | --------------------------- |
| language | string | 否  | -   | 按语言过滤，如 `zh`、`en`           |
| page     | int    | 否  | 1   | 页码，从 1 开始                   |
| page_size | int   | 否  | 20  | 每页条数，最大 100                 |

### 3.3 响应示例

```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_20260615143001_a1b2c3",
  "timestamp": 1718442601000,
  "data": {
    "total": 5,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "voice_id": "Vivian",
        "display_name": "Vivian",
        "gender": "female",
        "language": "zh",
        "description": "明亮、略带锋芒的年轻女声",
        "sample_rate": 24000
      },
      {
        "voice_id": "Serena",
        "display_name": "Serena",
        "gender": "female",
        "language": "zh",
        "description": "温暖、柔和的年轻女声",
        "sample_rate": 24000
      },
      {
        "voice_id": "Ryan",
        "display_name": "Ryan",
        "gender": "male",
        "language": "zh",
        "description": "节奏感强、富有动感的男声",
        "sample_rate": 24000
      },
      {
        "voice_id": "Aiden",
        "display_name": "Aiden",
        "gender": "male",
        "language": "en",
        "description": "阳光开朗、音色清晰的美式男声",
        "sample_rate": 24000
      },
      {
        "voice_id": "Sohee",
        "display_name": "Sohee",
        "gender": "female",
        "language": "zh",
        "description": "情感丰富、温暖的女声",
        "sample_rate": 24000
      }
    ]
  }
}
```

### 3.4 响应字段说明

| 字段           | 类型     | 说明        |
| ------------ | ------ | --------- |
| total        | int    | 符合条件的音色总数 |
| page         | int    | 当前页码      |
| page_size    | int    | 每页条数      |
| items        | array  | 音色列表      |
| voice_id     | string | 音色唯一标识，合成时传入 |
| display_name | string | 展示名称      |
| gender       | string | `male` / `female` |
| language     | string | 主语言，ISO 639-1 |
| description  | string | 音色描述      |
| sample_rate  | int    | 输出采样率（Hz） |

---

## 4. 非流式语音合成

### 4.1 接口地址

```http
POST /api/v1/tts/synthesize
```

### 4.2 请求体

```json
{
  "text": "你好，这是我的声音。",
  "voice_id": "Vivian",
  "speed": 1.0,
  "volume": 1.0,
  "audio_format": "wav",
  "response_mode": "json"
}
```

### 4.3 字段说明

| 字段            | 类型     | 必填 | 默认值   | 约束                    | 说明              |
| ------------- | ------ | -- | ----- | --------------------- | --------------- |
| text          | string | 是  | -     | 1 ~ 5000 字符           | 待合成文本           |
| voice_id      | string | 是  | -     | 须为音色列表中的 `voice_id` | 音色标识            |
| speed         | float  | 否  | 1.0   | 0.5 ~ 2.0             | 语速倍率            |
| volume        | float  | 否  | 1.0   | 0.0 ~ 2.0             | 音量倍率（后处理增益）     |
| audio_format  | string | 否  | wav   | wav / pcm / mp3       | 输出音频编码          |
| response_mode | string | 否  | json  | json / binary         | 见 §4.4           |
| enable_pinyin | bool   | 否  | false | -                     | 是否返回拼音辅助信息      |

> **兼容说明**：历史字段 `voice` 与 `voice_id` 等价，建议使用 `voice_id`。

### 4.4 响应模式

#### 模式 A：`response_mode=json`（默认）

`Content-Type: application/json`

```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_20260615143001_a1b2c3",
  "timestamp": 1718442601000,
  "data": {
    "task_id": "tts_20260615143001",
    "audio_data": "UklGRi...base64...",
    "audio_format": "wav",
    "sample_rate": 24000,
    "audio_duration": 3.2,
    "audio_pinyin": "nǐ hǎo ， zhè shì wǒ de shēng yīn 。"
  }
}
```

#### 模式 B：`response_mode=binary`

直接返回音频二进制，适合大段音频、减少 Base64 膨胀。

响应头：

```http
Content-Type: audio/wav
X-Task-Id: tts_20260615143001
X-Audio-Duration: 3.2
X-Request-Id: req_20260615143001_a1b2c3
```

### 4.5 响应字段说明（JSON 模式）

| 字段             | 类型     | 说明              |
| -------------- | ------ | --------------- |
| task_id        | string | 合成任务 ID         |
| audio_data     | string | Base64 编码音频     |
| audio_format   | string | 音频编码格式          |
| sample_rate    | int    | 采样率（Hz）         |
| audio_duration | float  | 音频时长（秒）         |
| audio_pinyin   | string | 拼音结果（`enable_pinyin=true` 时返回；是否带音调由环境变量 `TTS_PINYIN_WITH_TONE` 控制） |

### 4.6 错误响应示例

```json
{
  "code": 1001,
  "message": "voice not found",
  "request_id": "req_20260615143001_a1b2c3",
  "timestamp": 1718442601000,
  "data": null
}
```

### 4.7 超时建议

| 文本长度      | 建议客户端超时 |
| --------- | ------- |
| ≤ 200 字   | 30 s    |
| 200 ~ 2000 字 | 120 s   |
| > 2000 字  | 建议使用 WebSocket 流式接口 |

---

## 5. 流式语音合成（WebSocket）

### 5.1 连接地址

```text
ws://{host}/api/v1/tts/stream
```

### 5.2 连接与鉴权

1. 客户端发起 WebSocket 握手，携带 `Authorization` 头。
2. 服务端校验通过后保持连接；失败则关闭连接，Close Code `4401`。
3. 单连接同一时间仅处理一个合成任务；收到新 `synthesize` 请求时，可配置为拒绝或取消上一任务（默认拒绝，返回 `error` 事件）。

### 5.3 消息协议

- 传输格式：JSON 文本帧（`Text Message`）
- 字符编码：UTF-8
- 客户端 → 服务端：请求消息
- 服务端 → 客户端：事件消息（`begin` / `streaming` / `end` / `error`）

#### 客户端请求

连接建立后，发送合成请求：

```json
{
  "action": "synthesize",
  "request_id": "req_20260615143001_a1b2c3",
  "payload": {
    "text": "你好，这是我的声音。今天的天气非常不错，我们一起出去玩吧。",
    "voice_id": "Vivian",
    "speed": 1.0,
    "volume": 1.0,
    "audio_format": "wav",
    "enable_pinyin": false
  }
}
```

> 兼容说明：也支持直接发送 `payload`（即不带外层 `action/payload` 包装），服务端会按 `action=synthesize` 处理。

| 字段                    | 类型     | 必填 | 说明                          |
| --------------------- | ------ | -- | --------------------------- |
| action                | string | 是  | 固定为 `synthesize`            |
| request_id            | string | 否  | 客户端请求 ID                    |
| payload.text          | string | 是  | 待合成文本，1 ~ 20000 字符          |
| payload.voice_id      | string | 是  | 音色 ID                       |
| payload.speed         | float  | 否  | 0.5 ~ 2.0                   |
| payload.volume        | float  | 否  | 0.0 ~ 2.0                   |
| payload.audio_format  | string | 否  | 默认 `wav`                    |
| payload.enable_pinyin | bool   | 否  | 默认 `false`                  |

可选取消当前任务：

```json
{
  "action": "cancel",
  "task_id": "tts_20260615143001"
}
```

### 5.4 服务端事件

#### 5.4.1 `begin` — 任务开始

```json
{
  "event": "begin",
  "task_id": "tts_20260615143001",
  "request_id": "req_20260615143001_a1b2c3",
  "voice_id": "Vivian",
  "speed": 1.0,
  "total_segments": 3
}
```

| 字段             | 类型     | 说明        |
| -------------- | ------ | --------- |
| event          | string | 固定 `begin` |
| task_id        | string | 任务 ID     |
| request_id     | string | 关联的请求 ID  |
| voice_id       | string | 使用的音色     |
| speed          | float  | 语速        |
| total_segments | int    | 预计分段总数（可选，切分后可知） |

#### 5.4.2 `streaming` — 分段音频就绪

```json
{
  "event": "streaming",
  "task_id": "tts_20260615143001",
  "index": 1,
  "total_segments": 3,
  "text": "你好，这是我的声音。",
  "audio_data": "UklGRi...base64...",
  "audio_format": "wav",
  "sample_rate": 24000,
  "audio_duration": 1.8,
  "audio_pinyin": "nǐ hǎo ， zhè shì wǒ de shēng yīn 。"
}
```

| 字段             | 类型     | 说明              |
| -------------- | ------ | --------------- |
| event          | string | 固定 `streaming`  |
| task_id        | string | 任务 ID           |
| index          | int    | 当前分段序号（从 1 开始）  |
| total_segments | int    | 总分段数            |
| text           | string | 当前分段文本          |
| audio_data     | string | Base64 音频       |
| audio_format   | string | 音频格式            |
| sample_rate    | int    | 采样率             |
| audio_duration | float  | 当前分段时长（秒）       |
| audio_pinyin   | string | 拼音（`enable_pinyin=true` 时；是否带音调由环境变量 `TTS_PINYIN_WITH_TONE` 控制） |

> **性能优化（可选扩展）**：高吞吐场景可增加 `audio_transport=binary` 模式，音频走 Binary Frame，JSON 帧仅携带元数据。默认保持 Base64 以降低接入复杂度。

#### 5.4.3 `end` — 任务完成

```json
{
  "event": "end",
  "task_id": "tts_20260615143001",
  "total_segments": 3,
  "total_duration": 5.5
}
```

#### 5.4.4 `error` — 异常

```json
{
  "event": "error",
  "task_id": "tts_20260615143001",
  "code": 1001,
  "message": "voice not found",
  "request_id": "req_20260615143001_a1b2c3"
}
```

### 5.5 事件时序

```text
Client                          Server
  |---- WebSocket Connect -------->|
  |<------- (auth ok) ------------|
  |---- synthesize JSON ---------->|
  |<------- begin ----------------|
  |<------- streaming (x N) ------|
  |<------- end ------------------|
```

出错时：`begin` 可能省略，直接返回 `error` 后关闭或保持连接（可配置，默认保持连接）。

### 5.6 心跳（推荐）

服务端每 30s 发送：

```json
{
  "event": "heartbeat",
  "timestamp": 1718442601000
}
```

客户端可回复 `{ "action": "pong" }`。连续 3 次未收到心跳视为连接失效。

---

## 6. 长文本切分规则

当输入文本较长时，服务端按标点自动切分后逐段合成，流式接口通过多次 `streaming` 事件返回。

**示例**

原始文本：

```text
你好，这是我的声音。今天的天气非常不错，我们一起出去玩吧。
```

切分结果：

```text
1. 你好，这是我的声音。
2. 今天的天气非常不错，
3. 我们一起出去玩吧。
```

### 6.1 默认切分符

```text
。 ！ ？ ； ， 换行符(\n)
```

### 6.2 推荐正则（实现参考）

```python
import re
segments = re.split(r'(?<=[。！？；，\n])', text)
segments = [s.strip() for s in segments if s.strip()]
```

### 6.3 切分约束

| 规则        | 说明                          |
| --------- | --------------------------- |
| 单段最大长度    | 500 字符（超出则按次级标点继续切分）       |
| 最小段长度     | 1 字符                        |
| 无标点超长文本   | 按固定窗口 200 字强制切分（可配置）        |
| 首尾空白      | 自动 trim                     |

---

## 7. 健康检查

```http
GET /api/v1/tts/health
```

无需认证（或由网关层单独控制）。

**正常**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "model_loaded": true,
  "gpu_available": true,
  "timestamp": 1718442601000
}
```

HTTP `200`

**异常**

```json
{
  "status": "degraded",
  "version": "1.0.0",
  "model_loaded": false,
  "gpu_available": false,
  "timestamp": 1718442601000
}
```

HTTP `503`

---

## 8. 状态码定义

### 8.1 业务状态码（`code`）

| 状态码  | HTTP | 描述       | 处理建议              |
| ---- | ---- | -------- | ----------------- |
| 0    | 200  | 成功       | -                 |
| 1001 | 200  | 音色不存在    | 调用 voices 接口核对   |
| 1002 | 200  | 文本为空     | 检查 `text` 参数      |
| 1003 | 200  | 文本长度超限   | 缩短文本或改用流式接口       |
| 1004 | 200  | 语速/音量参数非法 | 检查参数范围            |
| 1005 | 200  | 合成失败     | 可重试，建议带幂等键        |
| 1006 | 200  | 服务内部异常   | 联系技术支持，提供 `request_id` |
| 1007 | 200  | 任务已取消    | 流式 cancel 后返回      |
| 4010 | 401  | 认证失败     | 检查 API Key        |
| 4030 | 403  | 无权限      | 联系管理员开通           |
| 4290 | 429  | 触发限流     | 按 `Retry-After` 退避 |

### 8.2 WebSocket Close Code

| Code | 说明        |
| ---- | --------- |
| 1000 | 正常关闭      |
| 4401 | 认证失败      |
| 4403 | 无权限       |
| 4429 | 连接数超限     |
| 4500 | 服务内部错误    |

---

## 9. 安全与合规

| 项      | 要求                              |
| ------ | ------------------------------- |
| 传输加密   | 生产环境强制 HTTPS / WSS              |
| 密钥管理   | API Key 定期轮换，禁止写入客户端明文           |
| 日志     | 不记录完整 API Key；文本日志按合规要求脱敏        |
| 内容安全   | 可接入敏感词过滤（返回 `1008 content blocked`） |
| 多租户隔离  | 按 API Key 绑定租户，音色与配额独立          |

---

## 10. 版本与兼容性

| 项        | 值                 |
| -------- | ----------------- |
| 当前 API 版本 | v1                |
| 路径前缀     | `/api/v1/tts`     |
| 升级策略     | 新版本走路径 `/api/v2/tts`，v1 至少保留 12 个月 |

### 10.1 协议扩展（向后兼容）

WebSocket 事件可扩展，客户端应忽略未知 `event` 类型：

```text
begin | streaming | end | error | heartbeat | progress | warning | cancel
```

新增字段均为可选；不得删除或修改已有必填字段语义。

### 10.2 变更记录

| 版本    | 日期         | 说明                                      |
| ----- | ---------- | --------------------------------------- |
| 1.0.0 | 2026-06-15 | 初版：voices、synthesize、stream           |
| 1.1.0 | 2026-06-15 | 补充认证、限流、健康检查、统一响应信封、二进制响应、分页与字段规范化 |

---

## 11. 接入示例

### 11.1 cURL — 非流式合成

```bash
curl -X POST "https://api.example.com/api/v1/tts/synthesize" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: demo-001" \
  -d '{
    "text": "你好，这是我的声音。",
    "voice_id": "Vivian",
    "speed": 1.0,
    "response_mode": "json"
  }'
```

### 11.2 Python — WebSocket 流式

```python
import asyncio
import json
import websockets

async def stream_tts():
    uri = "wss://api.example.com/api/v1/tts/stream"
    headers = {"Authorization": "Bearer YOUR_API_KEY"}
    async with websockets.connect(uri, additional_headers=headers) as ws:
        await ws.send(json.dumps({
            "action": "synthesize",
            "payload": {
                "text": "你好，这是我的声音。",
                "voice_id": "Vivian",
                "speed": 1.0,
            },
        }))
        async for message in ws:
            event = json.loads(message)
            if event["event"] == "streaming":
                # 处理 event["audio_data"]
                pass
            elif event["event"] == "end":
                break
            elif event["event"] == "error":
                raise RuntimeError(event["message"])

asyncio.run(stream_tts())
```

---
