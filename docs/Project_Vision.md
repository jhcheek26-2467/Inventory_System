# Inventory System

## Problem

Bars already have inventory management systems such as Partender.

The problem is not inventory tracking.

The problem is extracting useful business insights from inventory data.

Managers need to answer questions such as:

- What products move fastest?
- What products are overstocked?
- What should be reordered?
- Which locations have the most inventory?
- Where might inventory loss be occurring?

## Data Source

Partender inventory exports in Excel format.

## Tech Stack

- Python
- PostgreSQL
- Supabase
- Pandas
- SQLAlchemy

## Current Database

Tables:
- distributors
- categories
- products
- locations
- inventory_snapshots

## Current Goal

Build an ETL pipeline that imports inventory Excel reports into PostgreSQL.