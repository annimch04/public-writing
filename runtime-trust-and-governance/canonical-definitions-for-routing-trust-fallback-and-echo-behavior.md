---
title: "Canonical Definitions for Routing, Trust, Fallback, and Echo Behavior"
status: "published"
source: "Say It Plain"
source_url: "https://sayitplain.posthaven.com/number-canonical-definitions-for-routing-trust-fallback-and-echo-behavior"
author: "Anni McHenry"
system: "Fieldlight"
canonical_category: "Runtime, Trust, and Governance"
related_categories:
  - "Fieldlight and Human-Owned AI"
related_projects:
  - name: "Fieldlight Mesh"
    url: "https://github.com/annimch04/fieldlight-mesh"
  - name: "Sanctum Zero"
    url: "https://github.com/annimch04/sanctum-zero"
---

# Canonical Definitions for Routing, Trust, Fallback, and Echo Behavior

This document defines canonical runtime terms for message routing, trust levels, fallback behavior, echo handling, logging, return status, and consent scope within Fieldlight-aligned mesh systems.

It is intentionally structured like a specification. The purpose is not prose polish; the purpose is shared vocabulary, routing clarity, and predictable system behavior.

## Message Types

```yaml
message_types:
  handshake:
    description: Initial contact and identity verification between nodes
    trust_required: peer
    ttl: 2
    fallback: proxy
    destination_format: mesh://node_id
    auth_required: true

  trace:
    description: Sends a signal with trace log intent
    trust_required: peer
    ttl: 4
    fallback: proxy
    destination_format: mesh://node_id
    auth_required: true

  query:
    description: Asks for data or status from another node
    trust_required: peer
    ttl: 3
    fallback: proxy
    destination_format: mesh://node_id
    auth_required: true

  response:
    description: Returns data or status in reply to a query
    trust_required: peer
    ttl: 2
    fallback: none
    destination_format: mesh://origin_node_id
    auth_required: true

  echo:
    description: Sends message to self or ghost node to test routing
    trust_required: ghost
    ttl: 2
    fallback: none
    destination_format: mesh://ghost_id
    auth_required: false

  ping:
    description: Lightweight message to check node reachability
    trust_required: proxy
    ttl: 1
    fallback: ghost
    destination_format: mesh://node_id
    auth_required: false
```

## Trust Levels

```yaml
trust_levels:
  peer:
    access: full
    permissions:
      - send
      - receive
      - originate
      - relay
      - respond

  proxy:
    access: limited
    permissions:
      - relay
      - ping

  ghost:
    access: echo-only
    permissions:
      - receive
      - reflect
```

## Authentication Requirements

```yaml
auth_requirements:
  true:
    methods:
      - gpg_signature
      - peer_id_match

  false:
    methods:
      - none
```

## Fallback Types

```yaml
fallback_types:
  proxy:
    description: Relay through trusted proxy
    allows_store_and_forward: true
    ghost_fallback: true

  ghost:
    description: Passive echo bounce (non-storing)
    allows_store_and_forward: false
    ghost_fallback: false
```

## Log Policies

```yaml
log_policies:
  local:
    store_echo: true
    store_trace: true
    store_query: true
    store_handshake: true

  ghost:
    store_anything: false
```

## Return Status Codes

| Code | Meaning |
| --- | --- |
| 200 | OK — message received |
| 202 | Echoed — ghost reflection received |
| 404 | No response — node unreachable |
| 410 | TTL exceeded — message dropped |
| 503 | Loop detected — message bounced repeatedly |

## Consent Scope Definitions

```yaml
consent_scope_definitions:
  temporal:
    description: Consent valid only during current message transmission or session

  authorship-aware:
    description: Receiver must acknowledge human author origin and preserve message fidelity

  non-reproducible:
    description: Message may not be duplicated, stored, or forwarded

  local-only:
    description: Action must remain within node execution layer; external routing forbidden

  review-required:
    description: Requires explicit human approval before execution or further routing

  open:
    description: Sender allows any action; no restrictions on handling
```
