# Strategic Roadmap: Phase 2.5 - The Intelligence Layer

## Objective
Transition from raw data collection to model-ready "Feature Engineering" within the DB.

## Key Result
A unified `mv_training_set_v1` that allows the Lab Sandpit to fetch 100k rows of aligned training data in < 2 seconds.

## Context
This phase effectively creates a Feature Store directly inside the database, offloading heavy lifting from Python/Pandas to Postgres Materialized Views.
