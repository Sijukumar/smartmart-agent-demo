# SmartMart Smart Assistant — DEMO Project

## Overview

A real-world e-commerce customer support agent ("Smart Assistant") built on the FC AgentRun DEMO platform. This agent uses RAG (Retrieval-Augmented Generation) with a vector database-backed knowledge base to help customers with product queries, order tracking, returns, shipping, and payments.

## Agent Details

| Property | Value |
|----------|-------|
| Name | Smart Assistant |
| Domain | E-commerce (General Marketplace) |
| Channel | Web Chat |
| Model | GPT-4o-mini (with GPT-4o fallback) |
| KB Documents | 5 |
| Vector Chunks | ~131 |
| Tools | 6 (order, product, return, shipping, escalation, promo) |

## Quick Start

See `deployment/deployment-guide.md` for step-by-step instructions.

## Project Structure

```
AgentInfra-Demo/
├── knowledge-base/        # 5 real-world KB documents
├── agent-source/          # Agent definition + configuration
├── vector-db/             # Vector DB and embedding config
└── deployment/            # Platform deployment config + guide
```

## Platform

Built on the FC AgentRun DEMO platform with: Agent Runtime, AI Gateway, Memory/KB (Vector DB), Observability (AgentLabs), Evaluation (AgentLoop), Multi-Agent Collaboration, and AI-powered SRE.
