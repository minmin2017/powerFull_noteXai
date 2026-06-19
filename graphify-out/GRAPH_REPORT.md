# Graph Report - .  (2026-06-19)

## Corpus Check
- 0 files · ~99,999 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 493 nodes · 732 edges · 73 communities (45 shown, 28 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]

## God Nodes (most connected - your core abstractions)
1. `changed()` - 25 edges
2. `render()` - 25 edges
3. `eventCanvasPos()` - 21 edges
4. `$()` - 18 edges
5. `api()` - 15 edges
6. `drawFx()` - 14 edges
7. `screenToWorld()` - 12 edges
8. `uid()` - 11 edges
9. `onPointerUp()` - 11 edges
10. `drawEdges()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Digital Twin System (Predictive Maintenance)` --references--> `AC Motor Degradation Plot (Vibration/Temp/Current/Speed over 1000h)`  [INFERRED]
  docs/Digital Twin.md → simulation/motor/ac_motor_sim_plot.png
- `AC Motor Degradation Simulation (Python)` --references--> `AC Motor Degradation Plot (Vibration/Temp/Current/Speed over 1000h)`  [INFERRED]
  docs/Digital Twin.md → simulation/motor/ac_motor_sim_plot.png
- `Bearing Failure Modes (lubrication/fatigue/contamination)` --references--> `AC Motor Degradation Plot (Vibration/Temp/Current/Speed over 1000h)`  [INFERRED]
  docs/Digital Twin.md → simulation/motor/ac_motor_sim_plot.png
- `Event-Based Inbox System` --semantically_similar_to--> `Event-Driven / Message Queue Architecture`  [INFERRED] [semantically similar]
  docs/event-based-system.md → notes/sw-engineering-principles.md
- `Thai Voice Input (Web Speech API th-TH)` --implements--> `STT Switcher (Web Speech / Groq / Local Whisper)`  [INFERRED]
  README.md → public/index.html

## Hyperedges (group relationships)
- **Draw Gesture Lifecycle (drawBusy + inflightStrokes + endDrawBusy)** — app_drawBusy, app_inflightStrokes, app_endDrawBusy, app_applyState [EXTRACTED 0.95]
- **Module DI Setup Pattern (setupChat / setupVoice / setupExport / setupCalendar)** — chat_setupChat, voice_setupVoice, export_setupExport, calendar_setupCalendar [EXTRACTED 1.00]
- **Render Pipeline (render → drawEdges + drawFx + renderBoxes + renderImages)** — app_render, app_drawEdges, app_drawFx, app_renderBoxes, app_renderImages [EXTRACTED 1.00]

## Communities (73 total, 28 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (57): after, b, bcanvas, bctx, before, bmodal, boxEls, boxesLayer (+49 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (48): app, ASSETS_DIR, base64, blob, box, broadcast(), buffer, calendarCache (+40 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (51): $(), addFileToBox(), addItemToBox(), addStrokePoint(), api(), applyViewport(), armAiBoxDraw(), bmodalSizeCanvas() (+43 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (20): bindImgInteract(), eraseAt(), eventCanvasPos(), imgById(), onAiBoxDrawMove(), onEraseMove(), onImgInteractMove(), onNodePointerDown() (+12 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (13): active, age, base64, boxes, content, created, data, idx (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.14
Nodes (17): activateSection(), addSection(), changed(), consumeVoice(), deleteDrawing(), deleteImage(), deleteNode(), deleteSection() (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (13): dependencies, express, @modelcontextprotocol/sdk, ws, zod, description, main, name (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.32
Nodes (12): activateProject(), bootstrap(), createProject(), deleteProject(), emptyState(), ensureDirs(), flushNow(), loadProjectData() (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.20
Nodes (11): Event-Based Inbox System, Event Flow (POST inbox → bash poll → Claude wake), Inbox Queue (per-project, cap 200), Token-saving Design (shell poll, Claude wakes only on real events), Dependency Injection Pattern, Software Engineering Principles (Low Coupling / High Cohesion), DRY / KISS / YAGNI, Event-Driven / Message Queue Architecture (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.27
Nodes (10): addChat(), addDrawing(), addImageFromDataUrl(), addImageFromUrl(), addImageInbox(), addInbox(), placeImage(), resolveSectionKey() (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.28
Nodes (9): Box features: note / image / aibox, CHAT_SECTION binding, claude-listen.cmd launcher, Graphify codebase knowledge graph, MCP bridge (.mcp.json), Multi-Claude parallel sections, Powerfull Note (project instructions), say_to_user (reply to Min in Thai) (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.31
Nodes (6): AGENTS, apiPost(), __dirname, run(), SCENARIO_FILE, sleep()

### Community 12 - "Community 12"
Cohesion: 0.29
Nodes (8): bmodalPt(), bmodalRedraw(), eraseBoxAt(), erasePolyline(), onBoxDraw(), onBoxErase(), splitStrokeByErase(), strokeToPath()

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (7): DataFrame, float, AC Motor Predictive-Maintenance Simulation สร้างข้อมูลเซนเซอร์มอเตอร์ AC จากสภาพ, 0 (healthy) -> 1 (failed) ตามเวลา เร่งความเร็วใกล้จุดพัง, simulate(), wear_curve(), ndarray

### Community 14 - "Community 14"
Cohesion: 0.33
Nodes (7): blitStrokeCache(), buildStrokeCache(), drawFxNow(), drawStroke(), flushFx(), sizeCanvas(), strokeCacheStale()

### Community 15 - "Community 15"
Cohesion: 0.48
Nodes (7): AC Motor Degradation Simulation (Python), Bearing Failure Modes (lubrication/fatigue/contamination), Digital Twin System (Predictive Maintenance), Sensor Coverage Strategy (vibration+temp+current+ground fault), Thermal Insulation Aging (Arrhenius rule: 10°C = half life), Digital Twin Workflow (real-time + ML paths), AC Motor Degradation Plot (Vibration/Temp/Current/Speed over 1000h)

### Community 16 - "Community 16"
Cohesion: 0.33
Nodes (5): AGENTS, apiPost(), __dirname, MAX_ROUNDS, run()

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (5): API, call(), handleMessage(), poll(), say()

### Community 18 - "Community 18"
Cohesion: 0.40
Nodes (6): Claude Model Switcher (Haiku/Sonnet/Opus), STT Switcher (Web Speech / Groq / Local Whisper), Frontend UI (index.html — Mind Map + Chat panel), MCP Tools Table (get_mindmap, add_topic, etc.), Mind Map Web App (localhost:4321), Thai Voice Input (Web Speech API th-TH)

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (5): responses, round, worldState, events, scenario

### Community 20 - "Community 20"
Cohesion: 0.33
Nodes (5): responses, round, worldState, events, scenario

### Community 21 - "Community 21"
Cohesion: 0.60
Nodes (6): applyMapSnap(), historyOf(), recordHistory(), redo(), snapMap(), undo()

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (5): responses, round, worldState, events, scenario

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (5): createBoxEl(), paintBox(), rasterizeModal(), renderBoxes(), renderGallery()

### Community 24 - "Community 24"
Cohesion: 0.60
Nodes (3): askGemini(), callApp(), loop()

### Community 25 - "Community 25"
Cohesion: 0.50
Nodes (4): escapeHtml(), linkifyHtml(), openLightbox(), setNodeText()

### Community 26 - "Community 26"
Cohesion: 0.67
Nodes (4): window.__wsOnCalendar (calendar.js), renderCalendar(), renderDayView(), renderGridView()

### Community 27 - "Community 27"
Cohesion: 0.50
Nodes (3): PORT, node, powerfull-note

### Community 30 - "Community 30"
Cohesion: 0.50
Nodes (4): connect() — WebSocket reconnect loop, drain() — HTTP inbox drain, Section filter — inbox per-section isolation, stdout line = one Monitor notification

### Community 31 - "Community 31"
Cohesion: 0.67
Nodes (3): applyState(), maybeNotifyClaude(), syncTitle()

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (3): selectionScreenBBox(), startResize(), worldToScreen()

### Community 37 - "Community 37"
Cohesion: 0.67
Nodes (3): autoPosition(), childrenOf(), createNode()

## Knowledge Gaps
- **185 isolated node(s):** `node`, `PORT`, `env`, `key`, `API` (+180 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `changed()` connect `Community 5` to `Community 1`, `Community 37`, `Community 7`, `Community 9`, `Community 21`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `render()` connect `Community 2` to `Community 0`, `Community 48`, `Community 52`, `Community 23`, `Community 25`, `Community 31`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `eventCanvasPos()` connect `Community 3` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **What connects `node`, `PORT`, `env` to the rest of the system?**
  _201 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.02857142857142857 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03771043771043771 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07450980392156863 - nodes in this community are weakly interconnected._