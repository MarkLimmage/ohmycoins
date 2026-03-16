from app.enrichment.statistical_health import (
    calculate_variance,
    calculate_z_scores,
    detect_anomalies,
    validate_price_continuity,
)


def test_calculate_variance():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    expected_variance = 2.5
    assert calculate_variance(data) == expected_variance

    assert calculate_variance([]) == 0.0
    assert calculate_variance([1.0]) == 0.0

def test_calculate_z_scores():
    data = [10, 20, 30]
    # Mean = 20, StdDev = 10
    # Z = (X - 20) / 10
    expected_z = [-1.0, 0.0, 1.0]
    z_scores = calculate_z_scores(data)
    assert z_scores == expected_z

    assert calculate_z_scores([]) == []
    assert calculate_z_scores([1.0]) == [0.0]

def test_detect_anomalies():
    # Normal data with one extreme outlier
    data = [10.0, 10.1, 9.9, 10.0, 100.0]
    # Mean approx 28, StdDev huge
    # 100 will have a high Z-score

    anomalies = detect_anomalies(data, z_threshold=1.5)
    assert anomalies["has_anomalies"] is True
    assert anomalies["anomaly_count"] == 1
    assert anomalies["anomalies"][0]["index"] == 4
    assert anomalies["anomalies"][0]["value"] == 100.0

def test_validate_price_continuity():
    # Price crash scenario (50% drop)
    prices = [100.0, 101.0, 50.0, 51.0]

    result = validate_price_continuity(prices, max_drop_pct=0.4)

    assert result["valid"] is False
    assert result["issue_count"] == 1
    assert result["issues"][0]["index"] == 2
    assert result["issues"][0]["prev_price"] == 101.0
    assert result["issues"][0]["curr_price"] == 50.0
