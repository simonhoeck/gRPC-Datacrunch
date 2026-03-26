# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains MongoDB-exported JSON data from a **semiconductor die bonding machine** (Flip Chip Bonder, z.B. Fineplacer fc-4800). The data represents the full lifecycle of component placement in a pick-and-place manufacturing process. The goal is data analysis ("Datacrunch") of these process reports.

## Data Location & MongoDB Connection

All data lives in `grpc/` as MongoDB JSON exports and is also stored in a live MongoDB instance on `ATRAPC0114:27017`. Connection test: `grpc/Test-MongoConnection.ps1`.

## Domain: Die Bonding Process Flow

Each production run is identified by a `production_id` (UUID). Each component placed within that run has a `component_id` (= `report.id.id`). The 7 report types represent sequential steps:

| Service | File | What it captures |
|---|---|---|
| `preproduction` | `preproduction_reports.json` | Machine setup: machine name, serial number, side (LEFT/RIGHT/BOTH), component types and tool references (ppTool, flipTool, esTool), PPID |
| `creation` | `creation_reports.json` | Die pick event: source wafer position (row/col, binCode, SEMI E142 coordinates), lot info |
| `pickup` | `pickup_reports.json` | Pickup traces: time-series sensor data during physical pickup |
| `transfer` | `transfer_reports.json` | Transfer step: camera inspection (measured XY/theta offset at two fiducial points), transfer position (XYZ + theta in meters/radians) |
| `alignment` | `alignment_reports.json` | Alignment step: UC adjust measurements, bonding position adjustments with fiducial quality scores |
| `bonding` | `bonding_reports.json` | Bond event: target substrate position, full bond profile with 5 phases (afterAlignment, touchdownStart, touchdownDetected, forceRampStart, afterBondProfile) — each with W/Z/ToolTip axis positions in meters |
| `pbi` | `pbi_reports.json` | Post Bond Inspection: measured final XY offset and rotation (theta) of placed component |

## Record Linkage

Every record has the same top-level structure:
```json
{
  "_id": {"$oid": "..."},
  "received_at": {"$date": "..."},
  "service": "<service name>",
  "production_id": "<UUID>",
  "component_id": "<UUID>",
  "report": { ... }
}
```

To correlate all reports for one component placement: join on `component_id`. To get all components in a production run: join on `production_id`.

## Coordinate Systems

- **Source (wafer)**: `row`/`col` (machine coordinates) and `row_e142`/`col_e142` (SEMI E142 standard), plus `binCode` for die quality
- **Target (substrate)**: `row`/`col` with `notch` orientation (LEFT/RIGHT/FRONT), also with E142 coordinates
- **Machine axes**: W (rotation/theta), Z (vertical), ToolTip — values in meters, typically ~3.2mm for Z
- **Inspection offsets**: XY in meters (µm range, ~60µm typical), theta in radians or degrees depending on report type

## Notable Data Patterns

- `alignment_reports.json` and `pickup_reports.json` are large files (>500 KB); use streaming/pagination when processing
- Optional fields are represented as empty objects `{}` rather than `null`
- The first record in most files is synthetic test data (production_id `<22180c83-007d-10ca-23c6-c37503e77fa1>`) with dummy values like `"someSubstrateId"`; real production data starts from the second record onward
- SEMI E142 XML substrate map format is relevant for interpreting row/col coordinates
