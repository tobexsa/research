# ProgressReporter — 通用实验进度显示

**日期**: 2026-06-26
**状态**: 已批准

## 目标

为 `layer1_runner.py` 添加通用实时进度显示，支持 TUI 进度条和纯文本日志两种模式，无新依赖，完全向后兼容。

## 架构

新增 `src/mvp_agentic_rag/progress.py`，包含一个 `ProgressReporter` 类。修改 `layer1_runner.py` 集成使用。修改 `tests/test_runner.py` 覆盖新功能。

### 文件变更

| 文件 | 变更类型 |
|------|----------|
| `src/mvp_agentic_rag/progress.py` | **新增** — ProgressReporter 类 |
| `src/mvp_agentic_rag/layer1_runner.py` | 修改 — ~10 行，集成 reporter |
| `tests/test_runner.py` | 修改 — ~30 行，覆盖四种模式和 every 参数 |

## 配置

两个新增配置项，都有合理默认值，缺失时不改现有行为：

```yaml
progress_every: 1        # 已存在，行为不变：每 N 个 completed 输出一次
progress_display: auto   # 新增：auto | plain | tui | none，默认 auto
```

## ProgressReporter 接口

```python
class ProgressReporter:
    def __init__(self, total, output_dir, every=1, display="auto", out=None):
        """
        total:     总任务数 (samples × methods)
        output_dir: 输出目录路径
        every:     每 N 个 completed 输出一次进度
        display:   "auto" | "plain" | "tui" | "none"
        out:       输出目标文件对象，默认 sys.stdout
        """

    def update(self, completed, skipped):
        """更新进度并渲染到输出"""

    def finish(self):
        """结束进度显示（tui 模式换行并输出最终统计）"""

    def close(self):
        """同 finish，用于 with 语句"""
```

## display 模式行为

### auto（默认）
- `out.isatty()` 为 True → 使用 tui 模式
- `out.isatty()` 为 False（如重定向到 .log 文件）→ 使用 plain 模式

### plain
与现有行为完全一致，输出格式：
```
progress: completed=10 skipped=5 total=900 output_dir=runs/...
```
频率由 `progress_every` 控制。`finish()` 输出最终汇总行（同样的 `progress:` 格式）。

### tui
单行动态进度条，用 `\r` 覆盖，每次 `update()` 后调用 `file.flush()` 确保实时显示。`\n` 仅在 `finish()` 时输出：
```
[############--------] 611/900 67.9% completed=196 skipped=415 elapsed=01:23:10 eta=00:39:20 rate=2.1/min
```
- 条形宽度 20 个字符
- `elapsed` 从首次 `update()` 开始计时
- `eta` 基于 `completed / elapsed` 速率估算，`completed == 0` 时显示 `--:--:--`
- `rate` = completed / elapsed_minutes

### none
`update()` 不输出任何内容。`finish()` 无操作。不影响 trajectories 和 metrics 文件写入。
## 与现有代码的集成

### layer1_runner.py 改动

现有代码（第 51-56 行）：
```python
if progress_every > 0 and completed % progress_every == 0:
    progress_writer(
        f"progress: completed={completed} skipped={skipped} total={total} "
        f"output_dir={output_dir}"
    )
```

替换为：
```python
reporter.update(completed, skipped)
```

在循环结束后添加：
```python
reporter.finish()
```

`progress_writer` 参数保留：
- 如果调用者显式传入 `progress_writer`（如旧测试），走旧路径，不创建 ProgressReporter
- 否则创建 ProgressReporter

### 向后兼容

- 所有现有 config 文件不需要修改（`progress_display` 缺失时默认 `auto`）
- `progress_every` 语义不变
- `progress_writer` 参数继续生效
- 现有测试不受影响（测试用 `progress_writer=messages.append`，走旧路径）

## 测试

在 `test_runner.py` 中新增：

- `test_progress_reporter_plain_writes_lines` — plain 模式输出 `progress:` 行
- `test_progress_reporter_tui_writes_carriage_return_bar` — tui 模式输出 `\r` 和 `[###...]`
- `test_progress_reporter_none_suppresses_output` — none 模式不写任何东西
- `test_progress_reporter_auto_detects_tty` — auto 模式根据 isatty 切换
- `test_progress_reporter_respects_every` — every=3 每 3 次输出一次

## 无新依赖

完全使用标准库：`sys`, `time`, `shutil`。不使用 `rich`, `tqdm`, `progress` 等第三方包。
