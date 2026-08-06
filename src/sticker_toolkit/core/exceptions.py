"""Core 與 Service 使用的明確例外階層。"""


class StickerToolkitError(RuntimeError):
    """所有可由 UI 安全顯示的錯誤基底。"""


class InvalidSourceImageError(StickerToolkitError):
    """來源圖片不存在、無法解碼或沒有內容。"""


class UnsupportedFormatError(InvalidSourceImageError):
    """圖片格式不受支援。"""


class InvalidGridError(StickerToolkitError):
    """貼圖格線設定無效。"""


class ProcessingError(StickerToolkitError):
    """圖片處理失敗。"""


class ExportError(StickerToolkitError):
    """檔案輸出或封裝失敗。"""
