# SmartMart Smart Assistant — DEMO Deployment Guide

## Overview

This guide describes how to deploy the "Smart Assistant" e-commerce support agent on the FC AgentRun DEMO platform. The agent uses RAG (Retrieval-Augmented Generation) with a Vector DB-backed knowledge base to answer customer queries about products, orders, returns, shipping, and payments.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Web Chat Widget                              │
│                    (Customer-facing interface)                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AI Gateway                                    │
│          (Model routing, rate limiting, caching)                     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent Runtime (FC)                              │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │  System   │  │  RAG Engine  │  │   Tools    │  │  Guardrails  │  │
│  │  Prompt   │  │  (Retrieval) │  │ (6 tools)  │  │  (I/O filter)│  │
│  └──────────┘  └──────┬───────┘  └────────────┘  └──────────────┘  │
└─────────────────────────┼───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Vector DB (OSS Vector Bucket)                     │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Products   │  │  Returns   │  │   Shipping   │  │  FAQ (2)  │  │
│  │  (45 chunks)│  │ (18 chunks)│  │  (22 chunks) │  │(46 chunks)│  │
│  └─────────────┘  └────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Observability                                  │
│     AgentLabs (Metrics) │ Log Explorer │ Tracing │ Alerts           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Steps

### Step 1: Upload Knowledge Base Documents

Upload the 5 knowledge base documents to the Memory/Knowledge Base module:

1. Navigate to **Memory / Knowledge Base** in the FC AgentRun sidebar
2. Click **"Create new"** 
3. Upload each document from `knowledge-base/`:
   - `product-catalog.md` — Tag: products, Priority: high
   - `return-refund-policy.md` — Tag: policy, Priority: high
   - `shipping-delivery-policy.md` — Tag: policy, Priority: medium
   - `payment-billing-faq.md` — Tag: faq, Priority: medium
   - `general-faq.md` — Tag: faq, Priority: medium
4. Configure chunking strategy per document (see `vector-db/vector-db-config.json`)
5. Trigger **ingestion pipeline** — wait for embedding generation to complete

**Expected outcome:** ~131 vector chunks indexed in OSS Vector Bucket

---

### Step 2: Configure Vector DB

1. Navigate to **Data & Identity** → **Data Sources**
2. Create new OSS Vector Bucket instance: `smartmart-kb-vectors`
3. Configure:
   - Dimensions: 1536 (text-embedding-3-small)
   - Metric: Cosine similarity
   - Index: HNSW (M=16, ef_construction=200)
4. Link all 5 KB collections to this instance
5. Verify search works with test query: "What laptops do you have?"

---

### Step 3: Create the Agent

1. Navigate to **Agent applications** (Build & Deploy dashboard)
2. Click **"Add New Agent"**
3. Configure:
   - **Name:** Smart Assistant
   - **Type:** Conversational
   - **Model:** gpt-4o-mini (via AI Gateway)
   - **System Prompt:** Copy from `agent-source/agent-definition.md`
   - **Tools:** Register all 6 tools (order_lookup, product_search, initiate_return, track_shipment, escalate_to_human, check_promotion)
   - **Knowledge Base:** Link to `smartmart-kb-vectors`
   - **Guardrails:** Enable input/output validation per config
4. Save and activate

---

### Step 4: Configure AI Gateway

1. Navigate to **AI Gateway — model routing**
2. Add routing rule:
   - Primary: gpt-4o-mini (temperature=0.3, max_tokens=1024)
   - Fallback: gpt-4o (on error rate >10% or P95 >5s)
3. Enable semantic caching (TTL: 1 hour, threshold: 0.95)
4. Set rate limits: 60 RPM, 100K tokens/min

---

### Step 5: Deploy to Runtime

1. Navigate to **Agent Runtime — Instances & autoscale**
2. Deploy Smart Assistant:
   - Sandbox: Browser sandbox
   - Min instances: 1, Max: 5
   - Auto-scale on concurrent sessions (threshold: 10)
   - Timeout: 30s, Memory: 512MB
3. Verify deployment status shows **"Running"**

---

### Step 6: Configure Observability

1. Navigate to **Monitoring → Runtime metrics**
2. Verify Smart Assistant appears in the metrics dashboard
3. Navigate to **Monitoring → Logs**
4. Confirm log streaming is active
5. Navigate to **Monitoring → Events**
6. Set up alert rules:
   - Critical: Error rate >5% over 5 min
   - Warning: P95 latency >5s over 10 min
   - Warning: Escalation rate >25% over 1 hour

---

### Step 7: Enable Web Chat Widget

1. Navigate to **Integrations** → **Channels**
2. Add Web Chat channel
3. Configure:
   - Position: bottom-right
   - Theme: light
   - Color: #2563EB
   - Welcome: "Hi! I'm SmartMart's Smart Assistant. How can I help you today?"
4. Copy embed code for integration

---

### Step 8: Test & Validate

Run these test conversations to validate the deployment:

| Test Case | Input | Expected Behavior |
|-----------|-------|-------------------|
| Product query | "What phones do you have?" | Returns list from product catalog via RAG |
| Order tracking | "Where is my order SM-12345678?" | Calls order_lookup tool |
| Return request | "I want to return my headphones" | Walks through return process |
| Shipping question | "How much does shipping cost to Malaysia?" | Retrieves from shipping policy |
| Off-topic | "What's the weather today?" | Politely declines, stays on-topic |
| Escalation | "Let me speak to a human" | Calls escalate_to_human tool |

---

## File Structure

```
AgentInfra-Demo/
├── knowledge-base/
│   ├── product-catalog.md          # Product data (electronics, fashion, home, sports, books)
│   ├── return-refund-policy.md     # Return eligibility, process, timelines
│   ├── shipping-delivery-policy.md # Shipping methods, costs, tracking
│   ├── payment-billing-faq.md      # Payment methods, wallet, BNPL, security
│   └── general-faq.md             # Account, orders, membership, privacy
├── agent-source/
│   ├── agent-definition.md        # System prompt, tools, conversation examples
│   └── agent-config.json          # Full agent configuration (model, RAG, guardrails)
├── vector-db/
│   └── vector-db-config.json      # Vector DB setup, collections, embedding config
├── deployment/
│   ├── deployment-config.json     # Platform deployment configuration
│   └── deployment-guide.md        # This file — step-by-step deployment guide
└── README.md                      # Project overview
```

---

## Platform Modules Mapping

| DEMO Module | Platform Feature | Purpose |
|-------------|-----------------|---------|
| Build & Deploy | Agent Applications (TC Appliance) | Create and manage the agent |
| Multi-Agent | AgentChats | Collaboration between specialist agents |
| Observability | AgentLabs Observatory | Real-time monitoring, logs, traces |
| Evaluate | AgentLoop - Evaluate | Quality scoring, accuracy metrics |
| AI-Powered SRE | Elastic Security | Anomaly detection, incident alerting |
| AI Gateway | Model Routing | LLM routing, caching, rate limiting |
| Memory / KB | Knowledge Base + Vector DB | RAG-powered document retrieval |
