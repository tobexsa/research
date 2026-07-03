from pathlib import Path

_SRC_PACKAGE = Path(__file__).resolve().parents[1] / "src" / "mvp_agentic_rag"
__path__ = [str(_SRC_PACKAGE)]

__version__ = "0.1.0"
