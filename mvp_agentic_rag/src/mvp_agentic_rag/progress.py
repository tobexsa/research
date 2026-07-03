from __future__ import annotations

import shutil
import sys
import time


class ProgressReporter:
    """Universal progress display for experiment runs."""

    BAR_WIDTH = 20

    def __init__(
        self,
        total: int,
        output_dir: str,
        every: int = 1,
        display: str = "auto",
        out=None,
    ):
        if total <= 0:
            raise ValueError("total must be positive")
        if every <= 0:
            raise ValueError("every must be positive")
        if display not in ("auto", "plain", "tui", "none"):
            raise ValueError(f"unknown progress_display value: {display!r}")

        self._total = total
        self._output_dir = output_dir
        self._every = every
        self._display = display
        self._out = out or sys.stdout

        self._start_time: float | None = None
        self._prev_completed = 0
        self._prev_skipped = 0
        self._mode = self._resolve_mode()

    def update(self, completed: int, skipped: int) -> None:
        """Record a progress tick and render if the configured cadence fires."""
        if self._start_time is None:
            self._start_time = time.monotonic()

        self._prev_completed = completed
        self._prev_skipped = skipped

        if self._mode == "none":
            return

        done = completed + skipped
        should_emit = completed > 0 and completed % self._every == 0
        is_finished = done >= self._total
        if not should_emit and not is_finished:
            return

        if self._mode == "plain":
            self._write_plain(completed, skipped)
        elif self._mode == "tui":
            self._render_tui(completed, skipped)

    def write_line(self, text: str) -> None:
        """Write a normal line without changing progress state."""
        if self._mode == "tui":
            self._out.write("\n")
        self._out.write(text.rstrip("\n") + "\n")
        self._out.flush()

    def finish(self, completed: int | None = None, skipped: int | None = None) -> None:
        """Conclude progress display with the latest known counters."""
        if completed is not None:
            self._prev_completed = completed
        if skipped is not None:
            self._prev_skipped = skipped

        if self._start_time is None:
            self._start_time = time.monotonic()

        if self._mode == "tui":
            self._render_tui(self._prev_completed, self._prev_skipped, final=True)
            self._out.write("\n")
            self._out.flush()
        elif self._mode == "plain":
            self._write_plain(self._prev_completed, self._prev_skipped, suffix=" [done]")

    def close(self) -> None:
        """Alias for finish so callers can use close-style cleanup."""
        self.finish()

    def _resolve_mode(self) -> str:
        if self._display != "auto":
            return self._display
        try:
            if self._out.isatty():
                return "tui"
        except (OSError, AttributeError):
            pass
        return "plain"

    def _write_plain(self, completed: int, skipped: int, suffix: str = "") -> None:
        self._out.write(
            f"progress: completed={completed} skipped={skipped} "
            f"total={self._total} output_dir={self._output_dir}{suffix}\n"
        )
        self._out.flush()

    def _render_tui(self, completed: int, skipped: int, *, final: bool = False) -> None:
        elapsed = time.monotonic() - (self._start_time or time.monotonic())
        done = min(completed + skipped, self._total)
        fraction = done / self._total if self._total else 0.0
        pct = fraction * 100

        filled = int(self.BAR_WIDTH * fraction)
        bar = "#" * filled + "-" * (self.BAR_WIDTH - filled)
        elapsed_str = _format_duration(elapsed)

        if completed > 0 and elapsed > 0:
            rate_per_min = completed / (elapsed / 60.0)
            remaining_new = max(self._total - done, 0)
            eta_str = _format_duration(remaining_new / rate_per_min * 60.0)
            rate_str = f"{rate_per_min:.1f}/min"
        else:
            eta_str = "00:00:00" if final else "--:--:--"
            rate_str = "--.-/min"

        parts = [
            f"\r[{bar}] {done}/{self._total} {pct:.1f}%",
            f"completed={completed}",
            f"skipped={skipped}",
            f"elapsed={elapsed_str}",
            f"eta={eta_str}",
            f"rate={rate_str}",
        ]

        line = " ".join(parts)
        term_width = shutil.get_terminal_size().columns
        if term_width > 0:
            line = line[: term_width - 1]
            clear_width = min(len(line) + 8, term_width)
        else:
            clear_width = len(line) + 8
        self._out.write(line.ljust(clear_width))
        self._out.flush()


def _format_duration(seconds: float) -> str:
    """Return HH:MM:SS for a non-negative duration."""
    total = int(max(seconds, 0))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
