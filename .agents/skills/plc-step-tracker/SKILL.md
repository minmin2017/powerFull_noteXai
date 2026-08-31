---
name: plc-step-tracker
description: >-
  AI Mouse & Action Tracker for recording software steps (PLC, engineering apps, CAD, Windows apps) 
  and generating interactive Step-by-Step SOP guides with highlighted click screenshots, 
  UI element recognition, and synchronized audio transcription. Use when user wants to 
  record, track, or generate tutorial/guide steps from desktop actions or oCam recordings.
---

# PLC & Software Action Step Tracker Skill

A lightweight, powerful tool to record desktop mouse interactions (Left click, Right click, Double click, Drag & Drop), automatically identify active Windows UI controls & window titles, capture highlighted screenshots, and generate interactive HTML SOP Guides and Markdown documents.

## Project Location
- **Directory:** `C:\Users\wicha\Desktop\plc_step_tracker`
- **Tracker Script:** `C:\Users\wicha\Desktop\plc_step_tracker\tracker.py`
- **Launcher:** `C:\Users\wicha\Desktop\plc_step_tracker\start.cmd`

## How to Launch
To launch the background tracker:
```bash
python C:\Users\wicha\Desktop\plc_step_tracker\tracker.py
```

## Key Capabilities & Workflow
1. **F2 Hotkey & oCam Integration**: Pressing `F2` prompts a confirmation dialog to start/stop tracking in sync with screen recording.
2. **Visual Confirmation Indicator**: Displays a floating badge `🟢 AI Tracking Active` at the bottom-right of the screen.
3. **Mouse Action Detection**:
   - **Left Click**: Annotated with cyan/blue circle
   - **Right Click**: Annotated with orange circle
   - **Double Click**: Annotated with double-ring purple circle
   - **Drag & Drop**: Annotated with directional arrow overlay
4. **UI Automation**: Automatically extracts window titles and control element names using Windows UI Automation.
5. **Interactive Report Output**: Outputs interactive HTML guide with one-click PDF printing, Markdown export, and step timeline.
