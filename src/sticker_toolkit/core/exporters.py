"""平台輸出的 Core facade；不含任何互動或 UI。"""

from exporters.line import export_line
from exporters.wechat import WechatExportResult, export_wechat

__all__ = ["WechatExportResult", "export_line", "export_wechat"]
