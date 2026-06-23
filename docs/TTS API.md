# TTS API 文档

本文档描述 `OmniVoiceProject` 当前提供的 HTTP 与 WebSocket 接口，内容以仓库中的实际实现为准，适用于本地联调、服务接入和二次开发。

## 概览

### 服务地址

本地默认地址：

```text
http://localhost:8000
```

### 接口列表

| 接口 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/` | `GET` | 返回服务基础信息 |
| `/api/v1/tts/health` | `GET` | 健康检查，无需鉴权 |
| `/api/v1/tts/voices` | `GET` | 获取预设音色列表 |
| `/api/v1/tts/synthesize` | `POST` | HTTP 非流式语音合成 |
| `/api/v1/tts/stream` | `WebSocket` | WebSocket 流式语音合成 |

### 输出规格

| 项目 | 值 |
| ---- | ---- |
| 采样率 | `24000 Hz` |
| 声道 | 单声道 |
| 支持格式 | `wav`、`pcm`、`mp3` |
| 默认格式 | `wav` |

## 鉴权与公共约定

### API Key

除健康检查外，HTTP 和 WebSocket 接口都需要 API Key。

HTTP 请求头：

```http
Authorization: Bearer <API_KEY>
```

WebSocket 鉴权支持两种方式：

- 在握手头中传 `Authorization: Bearer <API_KEY>`
- 在连接查询参数中传 `?api_key=<API_KEY>`

本地开发默认 Key：

```text
dev-tts-api-key-change-me
```

### 公共请求头

| 请求头 | 是否必填 | 说明 |
| ------ | -------- | ---- |
| `Authorization` | 是 | Bearer Token |
| `Content-Type` | POST 时是 | `application/json` |
| `X-Request-Id` | 否 | 客户端请求 ID，未传时由服务端生成 |
| `X-Idempotency-Key` | 否 | 幂等键，仅对 HTTP 合成接口有效 |

### 统一响应结构

大多数业务结果会通过统一 envelope 返回：

```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_xxx",
  "timestamp": 1718442601000,
  "data": {}
}
```

字段说明：

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `code` | `int` | 业务状态码，`0` 表示成功 |
| `message` | `string` | 结果说明 |
| `request_id` | `string` | 请求追踪 ID |
| `timestamp` | `int` | 服务端时间戳，毫秒 |
| `data` | `object \| null` | 业务数据 |

### HTTP 状态码说明

| HTTP 状态码 | 说明 |
| ----------- | ---- |
| `200` | 请求成功，或业务失败但已返回 envelope |
| `400` | 请求体或参数格式错误 |
| `401` | 鉴权失败 |
| `429` | 触发限流 |
| `503` | 健康检查时模型尚未就绪 |

> 当前实现中，音色不存在、文本为空、文本超长等业务错误通常仍返回 `200`，请优先根据响应体中的 `code` 判断成功与否。

## 1. 服务首页

### 请求

```http
GET /
```

### 响应示例

```json
{
  "service": "OmniVoice TTS API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/v1/tts/health",
  "timestamp": 1718442601000
}
```

## 2. 健康检查

### 请求

```http
GET /api/v1/tts/health
```

### 成功响应

```json
{
  "status": "ok",
  "version": "1.0.0",
  "model_loaded": true,
  "gpu_available": true,
  "timestamp": 1718442601000
}
```

### 降级响应

```json
{
  "status": "degraded",
  "version": "1.0.0",
  "model_loaded": false,
  "gpu_available": true,
  "timestamp": 1718442601000,
  "load_error": "..."
}
```

当模型尚未加载完成时，接口可能返回 `503`。

## 3. 获取音色列表

### 请求

```http
GET /api/v1/tts/voices
```

### Query 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| ---- | ---- | ---- | ------ | ---- |
| `language` | `string` | 否 | - | 按语言过滤，例如 `zh`、`en` |
| `page` | `int` | 否 | `1` | 页码，从 1 开始 |
| `page_size` | `int` | 否 | `20` | 每页数量，最大 `100` |

### cURL 示例

```bash
curl "http://localhost:8000/api/v1/tts/voices?page=1&page_size=20" \
  -H "Authorization: Bearer dev-tts-api-key-change-me"
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_xxx",
  "timestamp": 1718442601000,
  "data": {
    "total": 5,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "voice_id": "Aiden",
        "display_name": "Aiden",
        "gender": "male",
        "language": "en",
        "description": "阳光开朗、音色清晰的美式男声",
        "sample_rate": 24000
      },
      {
        "voice_id": "Serena",
        "display_name": "Serena",
        "gender": "female",
        "language": "zh",
        "description": "温暖、柔和的年轻女声",
        "sample_rate": 24000
      }
    ]
  }
}
```

## 4. HTTP 非流式合成

### 请求

```http
POST /api/v1/tts/synthesize
Content-Type: application/json
Authorization: Bearer <API_KEY>
```

### 请求体

```json
{
  "text": "你好，这是我的声音。",
  "voice_id": "Vivian",
  "speed": 1.0,
  "volume": 1.0,
  "audio_format": "wav",
  "response_mode": "json",
  "enable_pinyin": false
}
```

### 字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| ---- | ---- | ---- | ------ | ---- |
| `text` | `string` | 是 | - | 待合成文本，最大 `5000` 字符 |
| `voice_id` | `string` | 是 | - | 预设音色 ID |
| `voice` | `string` | 否 | - | 历史兼容字段，等价于 `voice_id` |
| `speed` | `float` | 否 | `1.0` | 语速倍率 |
| `volume` | `float` | 否 | `1.0` | 音量倍率 |
| `audio_format` | `string` | 否 | `wav` | `wav` / `pcm` / `mp3` |
| `response_mode` | `string` | 否 | `json` | `json` 或 `binary` |
| `enable_pinyin` | `bool` | 否 | `false` | 是否返回拼音结果 |

### JSON 模式响应

当 `response_mode=json` 时，返回统一 envelope：

```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_xxx",
  "timestamp": 1718442601000,
  "data": {
    "task_id": "tts_xxx",
    "audio_data": "UklGRi...base64...",
    "audio_format": "wav",
    "sample_rate": 24000,
    "audio_duration": 3.2,
    "audio_pinyin": null
  }
}
```

### 二进制模式响应

当 `response_mode=binary` 时，接口直接返回音频数据，不再包裹 envelope。

示例响应头：

```http
Content-Type: audio/wav
X-Task-Id: tts_xxx
X-Audio-Duration: 3.2
X-Request-Id: req_xxx
```

### cURL 示例

返回 JSON：

```bash
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Authorization: Bearer dev-tts-api-key-change-me" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: demo-http-001" \
  -d '{
    "text": "你好，这是我的声音。",
    "voice_id": "Vivian",
    "speed": 1.0,
    "audio_format": "wav",
    "response_mode": "json"
  }'
```

直接下载音频：

```bash
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Authorization: Bearer dev-tts-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is my voice.",
    "voice_id": "Aiden",
    "response_mode": "binary",
    "audio_format": "wav"
  }' \
  --output output.wav
```

### 幂等调用

HTTP 合成接口支持 `X-Idempotency-Key`。同一 API Key 下，重复提交相同幂等键时会复用缓存结果，适合重试场景。

```http
X-Idempotency-Key: 3d1c69f4-9a3b-4cc2-8864-0b5bb8f0f7e2
```

## 5. WebSocket 流式合成

### 连接地址

```text
ws://localhost:8000/api/v1/tts/stream
```

### 握手鉴权

推荐在握手头中传入：

```http
Authorization: Bearer <API_KEY>
```

也支持：

```text
ws://localhost:8000/api/v1/tts/stream?api_key=<API_KEY>
```

### 客户端请求消息

连接建立后，发送 JSON 文本帧：

```json
{
  "action": "synthesize",
  "request_id": "req-stream-001",
  "payload": {
    "text": "你好，这是我的声音。今天天气不错，我们一起出去玩吧。",
    "voice_id": "Vivian",
    "speed": 1.0,
    "volume": 1.0,
    "audio_format": "wav",
    "enable_pinyin": false
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `action` | `string` | 是 | `synthesize` / `cancel` / `pong` |
| `request_id` | `string` | 否 | 客户端自定义请求 ID |
| `task_id` | `string` | 否 | `cancel` 时使用 |
| `payload.text` | `string` | `synthesize` 时必填 | 待合成文本，最大 `20000` 字符 |
| `payload.voice_id` | `string` | `synthesize` 时必填 | 音色 ID |
| `payload.voice` | `string` | 否 | 兼容旧字段 |
| `payload.speed` | `float` | 否 | 语速倍率 |
| `payload.volume` | `float` | 否 | 音量倍率 |
| `payload.audio_format` | `string` | 否 | `wav` / `pcm` / `mp3` |
| `payload.enable_pinyin` | `bool` | 否 | 是否返回拼音 |

> 兼容模式下，也支持直接发送一个不带 `action` 的 payload 对象，服务端会按 `synthesize` 处理。

### 服务端事件

#### `begin`

任务开始时返回：

```json
{
  "event": "begin",
  "task_id": "tts_xxx",
  "request_id": "req-stream-001",
  "voice_id": "Vivian",
  "speed": 1.0,
  "total_segments": 3
}
```

#### `streaming`

每段音频生成后返回：

```json
{
  "event": "streaming",
  "task_id": "tts_xxx",
  "index": 1,
  "total_segments": 3,
  "text": "你好，这是我的声音。",
  "audio_data": "UklGRi...base64...",
  "audio_format": "wav",
  "sample_rate": 24000,
  "audio_duration": 1.8,
  "audio_pinyin": null
}
```

#### `end`

全部片段完成后返回：

```json
{
  "event": "end",
  "task_id": "tts_xxx",
  "total_segments": 3,
  "total_duration": 5.5
}
```

#### `error`

出现错误时返回：

```json
{
  "event": "error",
  "task_id": "tts_xxx",
  "code": 1005,
  "message": "synthesis failed",
  "request_id": "req-stream-001"
}
```

#### `heartbeat`

服务端空闲时会周期性发送：

```json
{
  "event": "heartbeat",
  "timestamp": 1718442601000
}
```

客户端可回复：

```json
{
  "action": "pong"
}
```

### 取消当前任务

```json
{
  "action": "cancel",
  "task_id": "tts_xxx"
}
```

取消后服务端会返回一个 `error` 事件，其业务码通常为 `1007`。

### Python 示例

```python
import asyncio
import json
import websockets


async def main():
    uri = "ws://localhost:8000/api/v1/tts/stream"
    headers = {"Authorization": "Bearer dev-tts-api-key-change-me"}

    async with websockets.connect(uri, additional_headers=headers) as ws:
        await ws.send(json.dumps({
            "action": "synthesize",
            "request_id": "demo-stream-001",
            "payload": {
                "text": "你好，这是我的声音。今天我们来测试流式接口。",
                "voice_id": "Vivian",
                "speed": 1.0,
                "audio_format": "wav"
            }
        }))

        async for message in ws:
            event = json.loads(message)
            if event["event"] == "streaming":
                print("segment:", event["index"], "duration:", event["audio_duration"])
            elif event["event"] == "end":
                print("done")
                break
            elif event["event"] == "error":
                raise RuntimeError(event["message"])


asyncio.run(main())
```

## 6. 长文本切分

服务端会对较长文本自动切分后逐段合成，尤其在 WebSocket 模式下会逐段返回 `streaming` 事件。

当前实现的处理原则：

- 优先按句末标点断句
- 过短片段会尽量合并
- 超长片段会按次级标点继续拆分
- 没有合适标点时会按固定窗口强制切分

因此同一段长文本在流式模式下可能拆成多个片段返回，客户端应按 `index` 顺序进行拼接或播放。

## 7. 限流与连接限制

默认限制来自环境变量配置：

| 配置项 | 默认值 | 说明 |
| ------ | ------ | ---- |
| `TTS_RATE_LIMIT_QPS` | `10` | 每个 API Key 每秒请求数 |
| `TTS_RATE_LIMIT_DAILY` | `100000` | 每个 API Key 每日请求数 |
| `TTS_WS_MAX_CONNECTIONS` | `5` | 每个 API Key 的最大 WebSocket 并发连接数 |

触发限流时：

- HTTP 接口返回 `429`
- WebSocket 超过并发连接限制时，服务端会以 `4429` 关闭连接

## 8. 业务状态码

| 业务码 | 含义 |
| ------ | ---- |
| `0` | 成功 |
| `1001` | `voice not found` |
| `1002` | `text is empty` |
| `1003` | `text length exceeded` |
| `1004` | `invalid parameter` |
| `1005` | `synthesis failed` |
| `1006` | `internal server error` |
| `1007` | `task cancelled` |
| `4010` | `unauthorized` |
| `4030` | `forbidden` |
| `4290` | `rate limit exceeded` |

常见 WebSocket Close Code：

| Close Code | 含义 |
| ---------- | ---- |
| `4401` | 认证失败 |
| `4429` | 连接数超限 |

## 9. 接入建议

- 优先依赖 `code` 字段而不是只看 HTTP 状态码
- 为每次请求传入 `X-Request-Id`，便于日志追踪
- 重试 HTTP 合成时建议配合 `X-Idempotency-Key`
- 长文本或低延迟播放场景优先使用 WebSocket
- 生产环境务必通过反向代理提供 `HTTPS` / `WSS`

## 10. 相关文档

- [项目首页](../README.md)
- [安装指南](./install.md)
- [Docker 部署指南](./docker.md)
