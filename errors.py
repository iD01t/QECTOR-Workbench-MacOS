class QectorError(Exception):
    """Base exception class for all QECTOR Decoder Workbench errors."""
    pass

class QectorConfigError(QectorError):
    """Raised for configuration errors, missing paths, or invalid schemas."""
    pass

class QectorAuthError(QectorError):
    """Raised for Entra ID authentication and token management failures."""
    pass

class QectorDecoderError(QectorError):
    """Raised for syndrome parsing, matrix validation, or solver execution failures."""
    pass

class QectorHardwareError(QectorError):
    """Raised for CUDA / OpenCL device enumeration or driver execution errors."""
    pass

class QectorEgressBlockedError(QectorError):
    """Raised when an illegal outbound network connection is intercepted in air-gap mode."""
    pass

class QectorSecurityError(QectorError):
    """Raised for path traversal attempts, missing cryptographic signatures, or clock tamper detection."""
    pass
