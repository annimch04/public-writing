---
title: "Fieldlight Mobile Edge Node"
subtitle: "Vehicle-Based Sovereign Compute Architecture"
status: "Current architecture note"
source: "Fieldlight working note"
created_at: "2026-06-30"
author: "Anni McHenry"
canonical_category: "Edge Infrastructure and Safety"
related_categories:
  - "Fieldlight and Human-Owned AI"
  - "Runtime, Trust, and Governance"
related_project: "Fieldlight Mesh"
related_project_url: "https://github.com/annimch04/fieldlight-mesh"
---

# Fieldlight Mobile Edge Node

## Vehicle-Based Sovereign Compute Architecture

## Vision

The Fieldlight Mobile Edge Node extends local-first computing beyond the home into the physical world.

Rather than treating a vehicle as transportation, Fieldlight treats it as a trusted edge node capable of sensing, remembering, indexing, and synchronizing lived experience while preserving complete user ownership.

The vehicle becomes part of the Fieldlight Mesh.

Not a smart car.

A sovereign computer that happens to move.

---

## Core Philosophy

The purpose of the Mobile Edge Node is not automation.

It is continuity.

It preserves context as life unfolds while ensuring computation remains under the owner's control.

Like every other Fieldlight node, custody remains local.

The system is designed around four principles:

- Local-first
- User-owned
- Explicit synchronization
- Human-directed meaning

The vehicle never becomes the authority.

It becomes another trusted witness.

---

## Architecture

```text
                    Home Node
          (GPU / Heavy AI / Storage)
                     |
             Fieldlight Mesh
                     |
----------------------------------
                     |
              Supra Edge Node
                     |
          Raspberry Pi 5 (Headless)
                     |
     +----------+--------+--------+--------+
     |          |        |        |        |
 Dashcams     GPS    OBD-II    Voice   Local Storage
                     |
                Local AI Services
                     |
             iPad Cockpit Interface
```

The Raspberry Pi functions as infrastructure.

The iPad functions as the human interface.

The user rarely interacts directly with the Pi.

---

## Node Responsibilities

### Continuous Environmental Capture

The node records:

- front 4K dashcam
- rear 4K dashcam
- GPS trajectory
- time
- vehicle telemetry
- optional cabin microphone
- optional cabin camera
- environmental metadata

---

### Local Memory

The node maintains encrypted local storage for:

- trips
- routes
- locations
- photographs
- saved driving events
- voice notes
- image embeddings
- semantic indexes
- research observations

Nothing leaves the node without policy allowing it.

---

### Human-Guided Memory

Fieldlight deliberately separates observation from meaning.

The cameras observe.

The human decides significance.

Example bookmarks:

- Save previous 30 minutes.
- Research.
- Beautiful.
- Strange interaction.
- Important conversation.
- Near miss.
- Follow up later.
- Institute idea.

Those bookmarks become high-value retrieval anchors.

---

## Compute

### Raspberry Pi 5

Responsibilities:

- sensor coordination
- storage
- indexing
- synchronization
- lightweight inference
- networking
- API hosting

The Raspberry Pi is the nervous system.

It is not the reasoning engine.

Heavy inference occurs elsewhere.

---

### Home Node

The home server performs:

- large language models
- multimodal reasoning
- semantic retrieval
- long-term indexing
- memory consolidation
- training experiments

The vehicle sends work to the home node whenever trusted connectivity exists.

---

## Human Interface

### iPad Cockpit

The iPad replaces a traditional dashboard computer.

Responsibilities:

- AI conversation
- navigation
- Fieldlight interface
- search
- drive review
- voice notes
- camera playback
- live node health
- synchronization status

The Pi remains invisible.

The iPad is the experience.

Example:

```text
FIELDLIGHT
Supra Node
--------------
Status
- Recording
- GPS
- Storage
- Sync Ready

Today's Drive
2h 14m
4 Saved Moments

Recent Notes
- Sonoma observation
- Architecture idea
- Sophie dialogue

Search
__________________
```

---

## Voice Capture

The iPad serves as the primary capture device.

Examples:

- "Field note."
- "Bookmark this."
- "Save previous ten minutes."

Every note automatically binds to:

- GPS
- timestamp
- dashcam footage
- vehicle telemetry
- weather
- nearby landmarks

The result is searchable embodied memory.

---

## AI Responsibilities

Local AI performs:

- scene detection
- object recognition
- semantic indexing
- trip summaries
- route clustering
- anomaly detection
- embedding generation
- retrieval preparation

Large reasoning remains on trusted infrastructure.

---

## Storage

Primary storage:

- Raspberry Pi OS
- SSD, 1-2TB

Future:

- encrypted rolling archive
- append-only event log
- vector database
- semantic memory graph

---

## Networking

Primary:

- Local Wi-Fi
- Tailscale mesh

Future:

- LTE/5G
- opportunistic synchronization
- offline-first operation

The node remains fully functional without internet connectivity.

---

## Power

Dedicated auxiliary LiFePO4 battery with DC-DC charging.

Benefits:

- does not drain starter battery
- continuous recording
- continuous indexing
- parking observation
- graceful shutdown

---

## Example Queries

- Show me every drive through Sonoma during golden hour.
- Retrieve the drive where I decided to move to California.
- Show every place I recorded a Field Note.
- Find every conversation about Sophie.
- Show all moments marked "Beautiful."
- Find every drive where I mentioned memory architecture.
- Show all interactions with other drivers that I manually bookmarked.

---

## Relationship to Fieldlight

The Mobile Edge Node is not a standalone product.

It is one sovereign node within a distributed architecture.

```text
Fieldlight Mesh
Home
|
Laptop
|
Phone
|
Vehicle
|
Wearables
|
Future Devices
```

Each node maintains local custody over its own memory.

Synchronization is explicit.

Ownership remains with the individual.

No cloud service owns continuity.

---

## Future Extensions

- Drone integration
- Body-worn cameras
- Environmental sensors
- Biometric streams
- Local weather capture
- Cabin occupancy awareness
- Spatial audio memory
- Personal research instrumentation

---

## Design Principle

Fieldlight does not ask, "How can AI watch the world?"

It asks:

> How can a person's world remain their own while becoming increasingly searchable, meaningful, and alive over time?

The Mobile Edge Node extends that principle into motion. It turns the car into a trusted participant in your memory architecture rather than a disconnected machine, preserving context locally while remaining part of a broader, human-owned ecosystem.
