"""
Statistical Health Checks for Data Quality.

This module provides utility functions for calculating variance, Z-scores,
and detecting anomalies in time-series data. It is used by the
validation node in the agent workflow to ensure data integrity.
"""

import math
import statistics
from typing import Any, Dict, List, Optional, Tuple


def calculate_mean(data: List[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    if not data:
        return 0.0
    return statistics.mean(data)


def calculate_variance(data: List[float]) -> float:
    """
    Calculate the variance of a list of numbers.
    
    Args:
        data: List of numerical values
        
    Returns:
        Variance value (0.0 if data is empty or single value)
    """
    if not data or len(data) < 2:
        return 0.0
    return statistics.variance(data)


def calculate_std_dev(data: List[float]) -> float:
    """Calculate standard deviation."""
    if not data or len(data) < 2:
        return 0.0
    return statistics.stdev(data)


def calculate_z_scores(data: List[float]) -> List[float]:
    """
    Calculate Z-scores for a list of numbers.
    
    Z = (X - Mean) / StdDev
    
    Args:
        data: List of numerical values
        
    Returns:
        List of Z-scores corresponding to the input data
    """
    if not data or len(data) < 2:
        return [0.0] * len(data)
        
    mean = calculate_mean(data)
    std_dev = calculate_std_dev(data)
    
    if std_dev == 0:
        return [0.0] * len(data)
        
    return [(x - mean) / std_dev for x in data]


def detect_anomalies(
    data: List[float], 
    z_threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Detect anomalies in data using Z-score method.
    
    Args:
        data: List of numerical values to check
        z_threshold: Z-score threshold for identifying anomalies (default 3.0)
        
    Returns:
        Dictionary containing anomaly statistics and indices
    """
    if not data:
        return {
            "has_anomalies": False,
            "anomaly_count": 0,
            "anomaly_indices": [],
            "max_z_score": 0.0
        }
        
    z_scores = calculate_z_scores(data)
    anomalies = []
    max_z = 0.0
    
    for i, z in enumerate(z_scores):
        abs_z = abs(z)
        if abs_z > max_z:
            max_z = abs_z
            
        if abs_z > z_threshold:
            anomalies.append({
                "index": i,
                "value": data[i],
                "z_score": z
            })
            
    return {
        "has_anomalies": len(anomalies) > 0,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "max_z_score": max_z,
        "mean": calculate_mean(data),
        "std_dev": calculate_std_dev(data),
        "variance": calculate_variance(data)
    }


def validate_price_continuity(
    prices: List[float], 
    max_drop_pct: float = 0.5
) -> Dict[str, Any]:
    """
    Check for unrealistic sudden price drops (flash crashes) or spikes.
    
    Args:
        prices: List of price values ordered by time
        max_drop_pct: Maximum allowed percentage change between consecutive points (0.5 = 50%)
        
    Returns:
        Validation results
    """
    if not prices or len(prices) < 2:
        return {"valid": True, "issues": []}
        
    issues = []
    
    for i in range(1, len(prices)):
        prev = prices[i-1]
        curr = prices[i]
        
        if prev == 0:
            continue
            
        pct_change = (curr - prev) / prev
        
        if abs(pct_change) > max_drop_pct:
            issues.append({
                "index": i,
                "prev_price": prev,
                "curr_price": curr,
                "pct_change": pct_change
            })
            
    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues
    }
