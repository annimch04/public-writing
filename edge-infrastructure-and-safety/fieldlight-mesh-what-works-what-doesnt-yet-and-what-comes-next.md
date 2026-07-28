---
title: "Fieldlight Mesh: What Works, What Doesn't Yet, and What Comes Next"
subtitle: "An implementation review of the local-first network beneath Fieldlight's intelligence infrastructure."
status: "Published"
published: "2026-07-28"
source: "Fieldlight Mesh implementation review"
canonical_category: "Edge Infrastructure and Safety"
related_categories:
  - "Fieldlight and Human-Owned AI"
  - "Runtime, Trust, and Governance"
related_projects:
  - "Fieldlight Mesh"
  - "Fieldlight Institute / Intelligence Infrastructure"
source_repository: "https://github.com/annimch04/fieldlight-mesh"
---

# Fieldlight Mesh: What Works, What Doesn't Yet, and What Comes Next

## An implementation review of the local-first network beneath Fieldlight's intelligence infrastructure.

Fieldlight Mesh began with a constitutional requirement.

If intelligence is going to move between people, machines, vehicles, local models, and hosted systems, the network should not quietly make the most powerful remote system the authority over everything else.

Authority should begin with the human.

Identity should begin locally.

Memory should remain under local custody.

External capability should receive a bounded grant, perform a specific task, and return a result with a record of what happened.

That is the architecture.

The implementation is now real enough to evaluate.

Fieldlight Mesh is no longer only a collection of route schemas, symbolic roles, and infrastructure plans. The repository contains a runnable Python package, a TCP message layer, local node state, peer discovery, a peer-facing macOS application, cryptographically signed public objects, a mobile-edge event runtime, and a preflight audit layer for delegated tools.

It also has real limitations.

It is not yet a production mesh.

It does not yet provide encrypted transport.

It has not yet closed its most important cross-machine acceptance test.

Some of its strongest ideas exist as working local primitives but not yet as one continuous, enforced system.

This is the current line between what Fieldlight Mesh proves and what it still has to earn.

---

## The Short Version

As of July 2026:

| Layer | Current status |
|---|---|
| Local node state and identity | Runnable |
| SIL message framing, routing, response, inbox, and audit | Runnable locally |
| Same-host discovery → registry → send → `pong` | Validated |
| Two-node loopback message exchange | Tested |
| Ed25519-signed public objects | Runnable and tested |
| Town Square bundle export, import, verification, and trusted-peer sync | Runnable and tested |
| Peer-facing macOS app | Built as an Apple Silicon alpha |
| Supra Mobile Edge local event store and API | Runnable and tested |
| Kestrel Gate preflight, decision record, and mesh export | Runnable and tested |
| Trusted Bridge authority model | Schema, examples, and Phase 1 scaffolding |
| Encrypted transport | Not implemented |
| General signed message envelopes | Not implemented |
| Reliable cross-machine acceptance | Not yet closed |
| Multi-hop relay and store-and-forward | Not implemented |
| Public Town Square service | Not implemented |
| Notarized public Mac distribution | Not implemented |
| Full vehicle field deployment | Not yet validated |

The important distinction is this:

Fieldlight Mesh has working components.

It does not yet have a complete operational network.

---

## What Fieldlight Mesh Is Actually Building

Fieldlight Mesh is a local-first communication and delegation layer for Fieldlight nodes.

A node may be:

- a person-controlled computer;
- a peer's computer;
- a mobile or vehicle-based edge node;
- a neighborhood relay;
- a regional anchor;
- or a trusted bridge to hosted capability.

The network is designed around governed handoffs.

A message should not carry content alone. Depending on the action, it may also need to carry identity, consent, authority, provenance, expiration, revocation, routing policy, and an audit requirement.

This is why Fieldlight Mesh cannot be evaluated only by asking whether two computers can exchange bytes.

They can.

The larger question is whether capability can move without authority silently moving with it.

That is the system Fieldlight is trying to implement.

---

## What Works Now

### 1. A Node Can Establish Local State Without Making the Repository Its Memory

The current runtime initializes node state outside the source checkout.

A node receives:

- a stable `mesh://` identity;
- local configuration;
- route definitions;
- a trusted-peer registry;
- an inbox;
- routing and audit logs;
- local identity material;
- Town Square storage;
- and additional stores for mobile-edge and Kestrel Gate events.

Initialization fails rather than silently overwriting an existing identity.

That is a small behavior with constitutional importance.

The system treats identity as something that should be deliberately established, not regenerated whenever software is reinstalled.

Lemur remains the canonical source-authority node. Astra can run and publish. Supra can observe and queue mobile context. Those roles are related, but they are not interchangeable.

### 2. The SIL Runtime Can Send, Receive, Route, Store, and Acknowledge Messages

The current network layer uses one TCP connection per request with a four-byte length prefix and a UTF-8 YAML payload.

The receiver:

1. reads the framed message;
2. validates the destination and route;
3. checks the applicable trust rule;
4. dispatches the message;
5. stores durable content before acknowledging it;
6. and returns a structured response.

The runtime handles partial reads, rejects empty or truncated frames, deduplicates repeated messages, and detects conflicting reuse of a message identifier.

A tested two-node loopback exchange proves that a trusted sender can deliver a message, receive a `202 message_received` response, and find that message in the receiving node's inbox.

This is not the whole mesh.

It is a real transport and custody primitive.

### 3. Local Discovery Can Produce a Usable Route

Fieldlight supports LAN presence through `_fieldlight._tcp` mDNS advertisements.

A local advertisement can publish:

- the node's mesh URI;
- the SIL port;
- an optional host hint;
- and an optional libp2p peer identifier.

The discovery command can write those observations into a local peer registry. The send command can then resolve a message's destination from that registry instead of requiring the operator to enter an IP address manually.

One full same-host path has been validated:

**advertise → discover → registry → send → `pong`**

The repository also contains a Go libp2p discovery probe. Its observations can be merged into the registry alongside LAN information.

That bridge is useful, but still incomplete: the SIL runtime records libp2p multiaddresses; it does not yet dial them.

### 4. Public Objects Can Be Created Locally, Signed, Moved, and Verified

Fieldlight Mesh now supports Ed25519 local identities for signed objects.

Town Square uses that layer to create an append-only public wall without making a platform account the source of authorship.

A node can:

- create a signed post;
- derive its object identifier from the signed payload;
- verify the signature;
- export a bundle;
- import a bundle idempotently;
- reject tampered content;
- and synchronize the bundle to a trusted peer.

The implementation proves a specific principle:

Public speech can originate under local identity, move between nodes, and remain verifiable after it leaves the machine where it was written.

That is already more than a mockup.

### 5. A Peer Can Use a Mac Application Instead of Operating the Protocol by Hand

The Mesh repository includes a peer-facing macOS application over the same runtime used by the command line.

The app exposes:

- node setup;
- starting and stopping a local node;
- peer discovery;
- explicit peer trust;
- messaging;
- inbox inspection;
- local identity;
- and Town Square actions.

An Apple Silicon DMG build path exists. A peer does not need Git, Homebrew, Python, or a repository checkout to use that build.

The current package is an alpha. It is ad-hoc signed, not Apple-notarized, and not ready for anonymous public distribution.

Still, the existence of a peer surface matters. Sovereignty that requires every participant to become a specialist is not mainstream sovereignty.

### 6. The Supra Mobile Edge Runtime Preserves a Local Event Record

The Supra Mobile Edge Node has moved beyond a hardware diagram.

Its Phase 1 runtime includes:

- a SQLite event store;
- human-authored bookmarks;
- media-reference ingest with hashes;
- protected-custody flags;
- YAML and JSON export;
- review-gated sync manifests;
- a local HTTP API;
- and a lightweight iPad cockpit.

The current tests prove that a bookmark can be created, listed, translated into a Mesh message, and exposed through the local API.

They also prove that a protected media reference cannot enter a sync manifest without review.

The vehicle runtime therefore already encodes an important rule:

Capture does not equal permission to export.

### 7. Kestrel Gate Can Record a Delegated Action Before It Becomes Invisible

Kestrel Gate is the first runtime layer for preflight review of agent and script activity.

It can:

- record a proposed action;
- identify simple risk conditions;
- flag unknown actors, network access, package changes, protected paths, file mutation, public export, and extraction-like behavior;
- recommend `warn_and_ask`;
- record a human decision;
- and export the event as a Mesh-compatible message.

The classifier is intentionally simple.

The value is not that it can perfectly determine intent.

The value is that delegated action begins to leave a local, inspectable record before the system normalizes invisible authority.

### 8. The Current Code Passes Its Test Suite

At publication, the local Python suite passes:

**23 tests passed.**

The latest repository CI also passes on Ubuntu and macOS and builds the Go libp2p probe.

The tests cover:

- framing;
- trust failure behavior;
- no-clobber initialization;
- inbox deduplication and conflict detection;
- two-node message delivery;
- signed Town Square objects;
- tamper rejection;
- two-node Town Square bundle sync;
- mobile bookmarks;
- protected media review;
- the mobile local API;
- Kestrel risk flags;
- Kestrel decisions;
- and Mesh-compatible Kestrel export.

Passing tests do not make the Mesh production-ready.

They do make its current claims inspectable.

---

## What Does Not Work Yet

### 1. Transport Is Not Encrypted

The most important current limitation is also the clearest.

SIL messages are sent as plaintext YAML over TCP.

Town Square objects are signed, but signatures do not conceal their contents.

The current runtime should be used only on a trusted LAN or inside an encrypted overlay such as Tailscale.

It should not be exposed directly to the public internet.

### 2. General Mesh Messages Do Not Yet Have a Complete Cryptographic Identity Layer

Signed Town Square objects are real.

General transport identity is not complete.

The older GPG route check remains a development stub. The Ed25519 object layer has not yet become a signed envelope for every important message, grant, acknowledgement, and revocation.

Key rotation, continuity proofs, revocation records, and owner-signed agent delegation credentials also remain future work.

This is the difference between:

> this object verifies

and:

> this network relationship remains trustworthy over time.

Fieldlight has implemented the first.

It still has to implement the second.

### 3. The Cross-Machine Path Is Not Reliably Closed

The same-host runtime passes.

A remote receiver has also passed its own local end-to-end self-test.

But a documented sender-to-remote-peer test over Tailscale still times out before the SIL protocol is reached.

The evidence points to a raw TCP path or policy issue on the sender route rather than a failure in message framing or the remote handler.

That diagnosis is useful.

It is not the same as a successful cross-machine acceptance test.

Until two independent machines can exchange, store, acknowledge, and reply in both directions—with preserved evidence—the network's most important implementation claim remains open.

### 4. Discovery and Transport Still Sit Beside Each Other

LAN discovery works locally.

The libp2p probe works as an independent discovery track.

The registry can carry information from both.

But libp2p is not yet the Mesh transport, and the SIL runtime does not yet use libp2p multiaddresses as a live fallback.

Fieldlight can observe that a peer exists through more than one channel.

It cannot yet seamlessly choose and prove the best governed route between those channels.

### 5. The Runtime Is Not Yet a Multi-Hop Mesh

The current implementation is primarily direct node-to-node TCP.

It does not yet provide:

- automatic multi-hop routing;
- store-and-forward relays;
- offline queue reconciliation;
- relay selection;
- conflict resolution across replicated histories;
- revocation propagation;
- or regional handoff behavior.

The architecture describes household nodes, mobile nodes, neighborhood utilities, regional anchors, and trusted bridges.

The current runtime proves direct handoffs.

It does not yet prove the whole topology.

### 6. Town Square Is a Signed Primitive, Not Yet a Public Institution

Town Square can sign, verify, export, import, and synchronize posts.

It does not yet have:

- moderation records;
- tombstones;
- public identity endpoints;
- a public HTTP reader;
- automatic replication;
- or a mature social trust model.

Append-only storage is a strong beginning.

Public space requires more than a feed.

### 7. The Mac App Is Not Ready for Broad Distribution

The current app targets Apple Silicon.

It is not Developer ID signed, hardened, notarized, or stapled.

The repository contains a two-Mac acceptance runbook, but the durable public evidence does not yet show that the full install, enrollment, bidirectional message, inbox, and Town Square flow has been completed by two ordinary peer operators.

The app exists.

The distribution and field-validation layer remains unfinished.

### 8. The Mobile Node Has Not Yet Earned Its Hardware Claims

The Supra runtime is implemented.

The full vehicle loop is not yet demonstrated in the field.

The Raspberry Pi, storage, router, dashcam, OBD-II, microphone, local interface, custody rules, and home sync still need to operate together during and after an actual drive.

Until then, the mobile runtime is a strong local implementation with a hardware acceptance test still ahead of it.

### 9. Kestrel Gate Records Decisions but Does Not Yet Enforce the Whole System

Kestrel Gate can classify and record a preflight request.

It is not yet an operating-system-wide policy engine.

It does not yet sit automatically in front of every agent, terminal, repository mutation, network call, sync, and publication action.

The Trusted Bridge protocol has a grant schema and examples. Runtime enforcement remains Phase 1 work.

The record exists.

The gate is not yet everywhere the architecture says it should be.

---

## What Comes Next

The next stage should not be measured by how many new concepts the repository can name.

It should be measured by how many existing claims can be closed with evidence.

### 1. Close the Two-Machine Acceptance Test

This is the highest-priority next step.

Use two independent machines on a controlled network.

Prove:

- raw TCP reachability in both directions;
- message delivery in both directions;
- storage before acknowledgement;
- peer trust behavior;
- signed Town Square bundle sync;
- restart persistence;
- and retained audit evidence.

Record the exact software versions, network conditions, commands, responses, inbox state, and failure modes.

One completed field test will clarify more than another month of architecture writing.

### 2. Replace Trusted-Network Assumptions With Protocol Security

The next protocol release should add:

- encrypted transport;
- signed message envelopes;
- verified node identity;
- key continuity;
- rotation;
- revocation;
- and replay protection.

The goal is not merely secrecy.

It is making the authority path cryptographically inspectable.

### 3. Turn Discovery Metadata Into a Real Transport Choice

The Mesh should converge its LAN, registry, Tailscale, and libp2p observations into an explicit routing decision.

A node should be able to answer:

- Which peer did I resolve?
- Through which channel?
- Why was that channel trusted?
- What fallback was available?
- What authority and audit state traveled with the handoff?

The libp2p bridge should become executable, not merely descriptive.

### 4. Run the First Ordinary-Peer Mac Trial

Package the app.

Install it on two Macs operated by two people.

Observe where the system still assumes developer knowledge.

The test is not complete when the message arrives.

It is complete when both participants understand what identity they created, whom they trusted, what moved, and where the record lives.

Then sign and notarize the distribution path.

### 5. Complete the Supra Drive Bookmark Loop

The first vehicle milestone should remain narrow:

1. create a human bookmark;
2. bind it to time, route, vehicle context, and a media reference;
3. preserve the record locally;
4. review the proposed sync;
5. send only approved metadata to a trusted home node;
6. retain the original under local custody.

That loop would prove the Mobile Edge Node as a witness rather than a surveillance endpoint.

### 6. Put Kestrel Gate and Trusted Bridge Grants in the Actual Execution Path

The next trusted-bridge milestone should use a real delegated task.

For example:

- inspect a repository;
- draft a change;
- run tests;
- commit;
- publish;
- return an audit record.

The local node should issue a signed grant. Kestrel Gate should evaluate it. The hosted system should receive only the permitted context and tools. The result and audit trace should return to the local record.

That would connect Fieldlight's governance language to the work people are already doing with AI systems now.

---

## The Standard for the Next Phase

Fieldlight Mesh should resist two temptations.

The first is pretending that working local components already constitute a finished network.

The second is dismissing working local components because the network is not finished.

Both erase useful truth.

The current implementation proves that local identity, durable custody, governed messages, signed public objects, mobile event records, and delegated-action audits can exist in one coherent technical direction.

The current implementation does not yet prove that the direction survives hostile networks, ordinary users, multiple hops, changing keys, broken routes, public scale, or long periods of time.

That is what comes next.

Not a larger promise.

A stronger chain of evidence.

Fieldlight Mesh will be real when intelligence can move through the network without forcing the human to surrender authorship, memory, consent, or authority in exchange for capability.

The repository is no longer at zero.

Now it has to cross the distance between a working node and dependable infrastructure.
