from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationFiles:
    dp_bin: bool
    xyt_config: bool
    offset: bool

    @property
    def ready(self) -> bool:
        return self.dp_bin and self.xyt_config and self.offset
