# 流式合成文本切分规则（split_streaming_text）

本文档整理项目中“流式合成”的文本分段（切分）规则与关键代码片段，便于理解 WebSocket 流式合成时为什么会被切成多段。

对应实现位置：
- `split_streaming_text` / `_split_oversized`：[/home/gjh/workspace/May/omnivoice/main.py](file:///home/gjh/workspace/May/omnivoice/main.py)
- 默认阈值配置：[/home/gjh/workspace/May/omnivoice/config.py](file:///home/gjh/workspace/May/omnivoice/config.py)

## 1. 配置项（阈值）

分段控制使用“字符数”阈值（不是 token 数，也不是音频时长）。

代码片段（来自 [config.py](file:///home/gjh/workspace/May/omnivoice/config.py#L12-L14)）：

```python
STREAM_SEGMENT_MAX_CHARS = 100
STREAM_SEGMENT_MIN_CHARS = 20
```

- `STREAM_SEGMENT_MAX_CHARS`：单段尽量不超过的最大字符数（默认 100）
- `STREAM_SEGMENT_MIN_CHARS`：合并时尽量避免过短片段的最小字符数（默认 20）

## 2. 总体流程（规则概览）

`split_streaming_text(text)` 的处理流程可以概括为三步：

1. **按“句末标点”切成句子列表（sentences）**
2. **合并过短句子 + 控制最大长度（max_chars）**
3. **若单段仍超长：在“次级标点”（逗号/分号等）二次切分**

其中第 1 步是“切”；第 2 步是“拼”；第 3 步是“补救”。

## 3. 第一步：句末标点断句

实现方式是逐字符扫描，把字符累加到 `buf`，遇到句末标点就把 `buf` 组成一个 sentence。

代码片段（来自 [main.py](file:///home/gjh/workspace/May/omnivoice/main.py#L140-L178)）：

```python
def split_streaming_text(
    text: str,
    max_chars: int = STREAM_SEGMENT_MAX_CHARS,
    min_chars: int = STREAM_SEGMENT_MIN_CHARS,
) -> list[str]:
    """
    流式合成分段：先按句末标点切句，再合并过短片段，超长句在逗号处二次切分。
    """
    text = text.strip()
    if not text:
        return []

    sentences: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        buf.append(ch)
        if ch in {'。', '！', '？', '!', '?'}:
            sentences.append("".join(buf).strip())
            buf = []
        elif ch == '…':
            while i + 1 < len(text) and text[i + 1] == '…':
                i += 1
                buf.append(text[i])
            sentences.append("".join(buf).strip())
            buf = []
        elif ch == '.' and not (
            i > 0 and i < len(text) - 1
            and text[i - 1].isdigit() and text[i + 1].isdigit()
        ):
            sentences.append("".join(buf).strip())
            buf = []
        i += 1
    if buf:
        tail = "".join(buf).strip()
        if tail:
            sentences.append(tail)
```

### 3.1 句末标点集合

- 直接断句：`。` `！` `？` `!` `?`
- 省略号：遇到 `…` 会把后续连续 `…` 一起并入，然后断句（例如 `……` 当作一次句末）
- 英文句点 `.`：**只有当它不是数字小数点时才断句**
  - `3.14`：不会在 `.` 处断句（因为 `.` 前后都是数字）
  - `Hello.`：会断句（`.` 前后不是“都是数字”）

## 4. 第二步：合并过短片段 + 控制 max_chars

此阶段会把第一步得到的 `sentences`，按规则合并到若干段中（`merged`），核心目标是：
- 段不要太短（优先满足 `min_chars`）
- 段不要太长（尽量不超过 `max_chars`）

代码片段（来自 [main.py](file:///home/gjh/workspace/May/omnivoice/main.py#L179-L194)）：

```python
    merged: list[str] = []
    current = ""
    for sent in sentences:
        if not sent:
            continue
        if not current:
            current = sent
        elif len(current) < min_chars or len(current) + len(sent) <= max_chars:
            current += sent
        else:
            merged.extend(_split_oversized(current, max_chars))
            current = sent
    if current:
        merged.extend(_split_oversized(current, max_chars))

    return merged if merged else [text]
```

### 4.1 合并条件（关键逻辑）

会把 `sent` 拼接到 `current` 的条件是：

- `len(current) < min_chars`  
  当前段太短，优先继续拼，避免“碎片化”。

或

- `len(current) + len(sent) <= max_chars`  
拼起来不超过最大长度，就继续拼。

否则：
- 先把 `current` 输出（输出前会做一次“单段超长二次切分”，见下一节）
- 再用 `sent` 开启新段

## 5. 第三步：单段超长时的二次切分（次级标点）

若某个段（通常是单句特别长、或合并后的段）超过 `max_chars`，会调用 `_split_oversized(segment, max_chars)` 做“次级标点”切分。

代码片段（来自 [main.py](file:///home/gjh/workspace/May/omnivoice/main.py#L197-L228)）：

```python
def _split_oversized(segment: str, max_chars: int) -> list[str]:
    """单句超长时，在逗号/分号处二次切分。"""
    if len(segment) <= max_chars:
        return [segment]

    secondary = {'，', '；', '、', ',', ';', '：', ':'}
    parts: list[str] = []
    buf: list[str] = []
    for ch in segment:
        buf.append(ch)
        if ch in secondary and len("".join(buf)) >= 10:
            parts.append("".join(buf).strip())
            buf = []
    if buf:
        parts.append("".join(buf).strip())

    if len(parts) <= 1:
        return [segment]

    result: list[str] = []
    current = ""
    for part in parts:
        if not current:
            current = part
        elif len(current) + len(part) <= max_chars:
            current += part
        else:
            result.append(current)
            current = part
    if current:
        result.append(current)
    return result
```

### 5.1 次级标点集合

可作为二次切分点的标点：

- 中文：`，` `；` `、` `：`
- 英文：`,` `;` `:`

### 5.2 “>= 10 字符”限制

二次切分不是遇到标点就切，而是要求：

- 当前累计缓冲 `buf` 的长度至少达到 10（`len("".join(buf)) >= 10`）

因此像 `你好，` 这类很短片段不会立刻被切开，避免产生过碎的 parts。

## 6. 规则与流式合成的关系（在哪里被调用）

WebSocket 流式合成时会先切分，再逐段 `generate` 并回传：

- 调用切分：`segments = split_streaming_text(text)`
- 每段生成一次音频并发送 `state=start/streaming/end`

你可以在 [main.py](file:///home/gjh/workspace/May/omnivoice/main.py) 的 WebSocket 处理逻辑里搜索 `split_streaming_text(text)` 找到调用点。

