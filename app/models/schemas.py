from typing import Any, Literal

from pydantic import BaseModel, field_validator, model_validator


class ApiResponse(BaseModel):
    code: int
    message: str
    request_id: str
    timestamp: int
    data: Any | None = None


class VoiceItem(BaseModel):
    voice_id: str
    display_name: str
    gender: str
    language: str
    description: str
    sample_rate: int


class VoiceListData(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[VoiceItem]


class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str | None = None
    voice: str | None = None
    speed: float = 1.0
    volume: float = 1.0
    audio_format: Literal["wav", "pcm", "mp3"] = "wav"
    response_mode: Literal["json", "binary"] = "json"
    enable_pinyin: bool = False

    @model_validator(mode="after")
    def resolve_voice_id(self) -> "SynthesizeRequest":
        if not self.voice_id and not self.voice:
            raise ValueError("voice_id is required")
        if not self.voice_id:
            self.voice_id = self.voice
        return self

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("text is empty")
        return value


class SynthesizeData(BaseModel):
    task_id: str
    audio_data: str | None = None
    audio_format: str
    sample_rate: int
    audio_duration: float
    audio_pinyin: str | None = None


class StreamPayload(BaseModel):
    text: str
    voice_id: str | None = None
    voice: str | None = None
    speed: float = 1.0
    volume: float = 1.0
    audio_format: Literal["wav", "pcm", "mp3"] = "wav"
    enable_pinyin: bool = False

    @model_validator(mode="after")
    def resolve_voice_id(self) -> "StreamPayload":
        if not self.voice_id and not self.voice:
            raise ValueError("voice_id is required")
        if not self.voice_id:
            self.voice_id = self.voice
        return self

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("text is empty")
        return value


class StreamClientMessage(BaseModel):
    action: Literal["synthesize", "cancel", "pong"]
    request_id: str | None = None
    task_id: str | None = None
    payload: StreamPayload | None = None
