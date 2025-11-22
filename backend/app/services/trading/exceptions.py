"""Trading service exceptions."""


class CoinspotAPIError(Exception):
    """Exception raised when Coinspot API returns an error."""
    pass


class CoinspotTradingError(Exception):
    """General trading error for Coinspot operations."""
    pass


class OrderExecutionError(Exception):
    """Exception raised when order execution fails."""
    pass


class SchedulerError(Exception):
    """Exception raised when scheduler encounters an error."""
    pass


class AlgorithmExecutionError(Exception):
    """Exception raised when algorithm execution fails."""
    pass


class SafetyViolationError(Exception):
    """Exception raised when a safety check is violated."""
    pass
