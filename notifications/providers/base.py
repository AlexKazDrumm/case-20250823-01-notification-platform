from dataclasses import dataclass

class ProviderError(Exception):
    pass

class ProviderConfigError(ProviderError):
    pass

@dataclass
class SendResult:
    ok: bool
    message_id: str | None = None
    error: str | None = None
