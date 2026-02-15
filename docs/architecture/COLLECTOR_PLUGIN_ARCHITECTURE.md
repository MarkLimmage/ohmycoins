# Collector Plugin Architecture

**Date:** Feb 15, 2026
**Status:** APPROVED
**Sprint:** 2.28 (Collector Uplift)

## 1. Overview

The Collector system is being refactored from a purely configuration-based system into a **Plugin Architecture**. This allows for sophisticated data collection logic (e.g., sentiment analysis, pagination handling, specialized scraping) to be encapsulated in version-controlled Python modules, while allowing administrators to instantiate and configure these strategies via the UI.

## 2. Core Concepts

### 2.1 The Plugin Registry
The system will implement a `CollectorRegistry` singleton that scans a designated directory (`backend/app/collectors/strategies`) for valid plugin classes.

### 2.2 The Plugin Interface (`ICollector`)
All collectors must inherit from a strict base class:

```python
class BaseCollectorPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the plugin (e.g., 'news.coindesk')"""
        pass

    @property
    @abstractmethod
    def config_schema(self) -> Dict[str, Any]:
        """JSON Schema defining the configuration parameters required by this plugin"""
        pass

    @abstractmethod
    def collect(self, config: Dict[str, Any]) -> List[Signal]:
        """
        Main execution method.
        :param config: The configuration dict provided by the user.
        :return: A list of standardized Signal objects (News, Price, Social).
        """
        pass
        
    def test_connection(self, config: Dict[str, Any]) -> bool:
        """Optional method to validate credentials/connectivity before saving"""
        return True
```

### 2.3 The Collector Instance (Database)
The database stores *instances* of these plugins. A single plugin (e.g., `GenericRSS`) might have 50 instances (one for each feed).

**Table: `collector`**
*   `id`: UUID
*   `plugin_name`: String (FK to `BaseCollectorPlugin.name`)
*   `friendly_name`: String ("CryptoPanic News Feed")
*   `is_active`: Boolean
*   `interval_seconds`: Integer
*   `config_json`: JSONB (Stores the parameters defined in `config_schema`)

## 3. Data Flow

1.  **Startup**: `CollectorRegistry` loads all plugins from `backend/app/collectors/strategies/`.
2.  **Configuration**: Admin selects a plugin in the UI. Backend serves the `config_schema`. UI renders a dynamic form.
3.  **Execution**: `CollectorEngine` scheduler wakes up. It loads the `Collector` row, instantiates the correct `Plugin` class from the registry, and calls `.collect(row.config_json)`.
4.  **Ingestion**: The returned `Signal` objects are passed to the `DataIngestionService` for normalization and storage.

## 4. Reference Implementation Targets (Sprint 2.28)

We will port the following scrapers from the reference codebase into individual plugin modules:
*   `news.coindesk`: CoinDesk scraper with Article Body extraction.
*   `news.yahoo`: Yahoo Finance Crypto scraper.
*   `news.cryptopanic`: Aggregator interface.
*   `sentiment.vader`: A mixin or service for enriching text content.

## 5. Security Benefits

*   **No RCE**: Unlike storing Python code in the DB, this approach only stores configuration.
*   **Version Control**: All scraping logic is reviewed and committed to the repo.
*   **Type Safety**: Pydantic models validate the configuration before execution.
