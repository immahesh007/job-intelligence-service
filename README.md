# job-intelligence-service

## Overview

`job-intelligence-service` is a FastAPI-based backend microservice responsible for ATS-based job aggregation and job intelligence operations.

This service has no frontend responsibilities and acts as:

* a scheduled job ingestion engine
* a centralized jobs database service
* a job query engine for the main platform

---

# Core Responsibilities

## 1. ATS-Based Job Aggregation

The service periodically fetches jobs from multiple ATS providers including:

* Greenhouse
* Lever
* Ashby

Jobs are fetched on a scheduled basis using background workers.

---

## 2. Job Normalization

All fetched jobs are transformed into a common internal schema before persistence.

The normalization layer ensures:

* consistent querying
* unified search
* easier filtering and ranking
* provider-independent job representation

---

## 3. Jobs Database Management

The service stores:

* job metadata
* normalized descriptions
* extracted skills
* embeddings (future)
* source/provider metadata

using PostgreSQL.

---

## 4. Job Query Engine

The service exposes internal APIs for:

* job search
* filtering
* semantic matching
* recommendations
* trending jobs

These APIs are consumed by the main platform service.

---

# Initial Scope

## Included

* FastAPI backend
* PostgreSQL integration
* ATS ingestion workers
* scheduled sync jobs
* normalization pipeline
* internal search APIs
* common jobs schema

---

## Excluded

* frontend
* resume builder
* authentication UI
* PDF generation
* direct user interaction

---

# Recommended Stack

* FastAPI
* PostgreSQL
* SQLAlchemy
* pgvector (future)
* Redis
* Celery / Celery Beat

---

# Suggested Architecture

ATS APIs
↓
Ingestion Workers
↓
Normalization Layer
↓
PostgreSQL
↓
Search & Match APIs
↓
Main Platform Service

---

# Future Scope

Future enhancements may include:

* semantic embeddings
* AI-based job matching
* recommendation engine
* ranking engine
* LinkedIn/Naukri ingestion
* salary intelligence
* skill extraction pipelines
* analytics
