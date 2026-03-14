import json
from typing import Any, Dict

def mock_execute_code(code: str, execution_type: str = "general") -> Dict[str, Any]:
    """
    Mock execution of code, simulating a Dagger environment.
    
    Args:
        code: The Python code to execute.
        execution_type: type of execution (e.g., "data_loading", "modeling", "evaluation")

    Returns:
        Mocked execution result adhering to the contract.
    """
    
    # Simulate processing time or errors if needed
    
    if execution_type == "data_loading":
        return {
            "mime_type": "text/markdown",
            "content": "Data loaded successfully. Shape: (1000, 10). Columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume', ...]",
            "code_snippet": code
        }
        
    elif execution_type == "exploration":
        # Return a mock Plotly JSON
        mock_plot = {
            "data": [
                {
                    "x": ["2023-01-01", "2023-01-02", "2023-01-03"],
                    "y": [10, 15, 13],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Close Price"
                }
            ],
            "layout": {
                "title": "Price Exploration (Mock)",
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Price"}
            }
        }
        return {
            "mime_type": "application/vnd.plotly.v1+json",
            "content": mock_plot,
            "code_snippet": code
        }

    elif execution_type == "modeling":
        # Return a mock model artifact metadata
        return {
            "mime_type": "application/json+blueprint",
            "content": {
                "model_id": "xgb_mock_123",
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.80,
                "feature_importance": {"volume": 0.4, "rsi": 0.3, "sma": 0.3}
            },
            "code_snippet": code,
            "hyperparameters": {"n_estimators": 100, "learning_rate": 0.1}
        }

    elif execution_type == "evaluation":
        return {
            "mime_type": "application/json+tearsheet",
            "content": {
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.15,
                "total_return": 0.25,
                "win_rate": 0.55
            },
            "code_snippet": code
        }

    return {
        "mime_type": "text/plain",
        "content": "Code executed successfully (Mock).",
        "code_snippet": code
    }
