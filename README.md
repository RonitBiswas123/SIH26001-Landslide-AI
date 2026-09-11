# SIH26001 - AI-Based Landslide Risk Monitoring System

A real-data-first prototype for SIH26001.

## Project pipeline

Real GSI / ISRO / IMD / DEM data
-> validation
-> cleaning
-> feature engineering
-> ML model
-> GIS risk map
-> early warning dashboard

## Important

The final training dataset must use traceable real data. Do not claim model accuracy until it has been evaluated on an appropriate held-out dataset.

## Main data sources

- Geological Survey of India (GSI) Bhusanket
- ISRO / NRSC Landslide Atlas
- India Meteorological Department (IMD)
- DEM terrain data
- Satellite observations
- Road/infrastructure data
- Field/citizen reports

## Folder structure

data/raw/       Original downloaded data
data/processed/ Cleaned/derived data
ingestion/      Data ingestion and validation
model/          Training and prediction
app/            Streamlit dashboard
utils/          Shared utilities
notebooks/      Exploration notebooks
