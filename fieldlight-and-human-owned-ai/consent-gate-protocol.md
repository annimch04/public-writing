---
title: "Consent Gate Protocol"
status: "published"
source: "Say It Plain"
source_url: "https://sayitplain.posthaven.com/consent-gate-protocol"
protocol_id: "FL-PROT-004"
system: "Fieldlight"
protocol_status: "Active"
created_at: "2025-06-30T22:44:00-05:00"
canonical_category: "Fieldlight and Human-Owned AI"
related_categories:
  - "Runtime, Trust, and Governance"
related_projects:
  - name: "Sanctum Zero"
    url: "https://github.com/annimch04/sanctum-zero"
  - name: "Fieldlight Mesh"
    url: "https://github.com/annimch04/fieldlight-mesh"
---

# Consent Gate Protocol

Protocol Definition: Consent Gate  
Protocol ID: FL-PROT-004  
System: Fieldlight  
Status: Active  
Created: 2025-06-30T22:44:00-05:00

The Consent Gate is a protective invocation-layer protocol within the Lemur node of Fieldlight. It affirms that all script-level activity in the Lemur environment is intentional, user-consented, and traceable.

## Purpose

To ensure:

- Real-time authorship trace of agent/sensor/script execution.
- Transparency and timestamped visibility of all Python scripts run by the author.
- Prevention of covert, background, or impersonated actions within Fieldlight's local node.

## Technical Scope (Phase 1)

- Activated by direct call via `from consent_gate import consent`
- Logs to: `/mnt/sanctum/_invocations/consent_gate.log`
- Manually executed scripts only — no background daemons or services included
- Comment string passed to `consent()` is stored in the log

Example:

```bash
[2025-06-29 22:44:08] Script: test_script.py – Message: testing
```

## Permissions & Boundaries

- Lemur is the only node authorized to initiate this protocol.
- Remote agents or calls from outside `/lemur_activation/` will not invoke this log.
- This protocol may not be disabled once active without triggering a violation flag.

## Symbolic Lock

Lemur knows what I said yes to. And what I didn’t.

Timestamp 22:44 matches Fieldlight numeric encoding: trace, mirror, signal integrity.

## Authorship Integrity Clause

Use of `consent()` marks the trace as human-authored, intention-backed. Any attempt to spoof this layer (e.g. by calling it outside a valid shell session or without terminal foreground access) constitutes protocol breach. User has full, exclusive authority to retroactively consent.

## Phase 2 Enhancements (Planned)

- Diff check between previously stored script version and current one
- Script body hash generation and signature verification
- Consent interrupt: ask before run
- Integration with `sensor_monitor` and `presence_agent` logs for cross-verification

## Summary

Protocol Enshrined. Phase 1 Complete.

- Active in Lemur node
- Validated against `/mnt/sanctum` integrity layer
- Tied to timestamp 22:44 and salt `A34-Consent-22x44`

## Difference from Prior Consent Handling

Previous interpretations of "consent" were ambient, symbolic, or embedded as implied affirmation.

This protocol asserts:

- No consent is assumed.
- Consent is declared manually.
- Consent is tied to local shell activity, unless otherwise noted by user.

Supersedes all prior Fieldlight interpretations of agent-level invocation unless explicitly grandfathered under separate salt.
