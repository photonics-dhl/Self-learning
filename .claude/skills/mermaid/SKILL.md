---
name: mermaid
description: |
  Mermaid diagram generation skill for creating knowledge trees, flowcharts, sequence diagrams, and concept visualizations.

  **Trigger when**: User says "生成图表", "画个图", "mermaid", "知识树", "流程图", "生成mermaid", "画流程图", "knowledge graph", "flowchart"

  **Also trigger when**: User wants to visualize:
  - Concept relationships (knowledge trees)
  - Process flows (workflows, procedures)
  - System architecture
  - State machines
  - Entity relationships
  - Sequence/timeline diagrams

  **DO NOT trigger for**: Complex 3D visualizations (use image-generation), detailed technical drawings (use diagram-generator or image-generation).

  Make sure to use this skill whenever the user wants to visualize relationships, processes, or structures. Mermaid is free and fast - prefer it over image-generation for simple diagrams.
---

# Mermaid Diagram Generation Skill

## Overview

This skill generates Mermaid diagrams for visualizing knowledge structures, workflows, and relationships. Mermaid diagrams are rendered as SVGs and embedded directly in Markdown/ Obsidian.

## Mermaid MCP Tools

The following MCP tools are available:
- `generate_mermaid_diagram` - Generate Mermaid diagram as base64 PNG, SVG, or Mermaid code

## Diagram Types

| Type | Best For | Mermaid Keyword |
|------|----------|----------------|
| Flowchart | Processes, decision trees | `graph` |
| Sequence | Interactions, protocols | `sequenceDiagram` |
| Class | OOP structures | `classDiagram` |
| State | State machines | `stateDiagram` |
| ER | Database schemas | `erDiagram` |
| Gantt | Timelines | `gantt` |
| Pie | Distributions | `pie` |
| Mindmap | brainstorming | `mindmap` |

## Common Patterns

### Knowledge Tree (Recommended for Optics Research)

```mermaid
graph TD
    A[Optics] --> B[Geometric Optics]
    A --> C[Wave Optics]
    A --> D[Quantum Optics]
    B --> B1[Lens Theory]
    B --> B2[Mirror Systems]
    C --> C1[Interference]
    C --> C2[Diffraction]
    D --> D1[Photonics]
    D --> D2[Quantum Info]
```

### Flowchart for Process

```mermaid
graph LR
    A[Input] --> B[Process]
    B --> C{Decision}
    C -->|Yes| D[Output 1]
    C -->|No| E[Output 2]
```

### Sequence Diagram

```mermaid
sequenceDiagram
    A->>B: Request
    B->>C: Forward
    C-->>B: Response
    B-->>A: Result
```

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> State1
    State1 --> State2: Transition
    State2 --> [*]
```

## Usage Guidelines

### When to Use Mermaid vs Other Tools

| Use Case | Tool | Why |
|----------|------|-----|
| Knowledge tree | Mermaid | Free, fast, editable |
| Simple flowchart | Mermaid | Standard, integrated |
| Architecture diagram | diagram-generator | More control |
| Realistic illustration | image-generation | Photorealistic |
| Technical schematic | image-generation | Detailed rendering |

### Recommended Parameters

```
output_type: "svg"   # SVG for crisp rendering at any size
theme: "default"     # default/base/forest/dark/neutral
backgroundColor: "white"  # or transparent
```

## Example Prompts

**User**: "生成太赫兹知识体系的知识树"

```mermaid
graph TD
    A["THz Technology"] --> B["THz Sources"]
    A --> C["THz Detection"]
    A --> D["THz TDS"]
    A --> E["THz Imaging"]
    B --> B1["PCA"]
    B --> B2["Optical Rectification"]
    B --> B3["QCL"]
    C --> C1["PC Sampling"]
    C --> C2["EOS"]
    D --> D1["Reflection TDS"]
    D --> D2["Transmission TDS"]
```

**User**: "画一个光电导天线发射太赫兹的流程"

```mermaid
graph LR
    A["Femtosecond Laser"] --> B["PCA Antenna"]
    B --> C["Photo carriers"]
    C --> D["dJ/dt"]
    D --> E["THz Pulse"]
    style A fill:#f9f,stroke:#333
    style E fill:#9f9,stroke:#333
```

## Best Practices

1. **Use consistent naming** - `[Node]` for nodes, `"Label"` for labels
2. **Add styling** - Use `style` for emphasis on key nodes
3. **Keep it simple** - Break complex diagrams into smaller ones
4. **Use appropriate direction** - `TD` (top-down) for trees, `LR` (left-right) for flows
5. **Add colors sparingly** - for emphasis, not decoration

## Integration with Project

1. Generate Mermaid code
2. Save to Obsidian note with code block: ` ```mermaid `
3. Or use `generate_mermaid_diagram` MCP for rendered image
4. Save to: `Obsidian-Vault/6️⃣ 工具/visualizations/`
5. Insert reference: `![[visualizations/diagram.png]]`

## Error Handling

If Mermaid generation fails:
1. Check syntax - common issues with special characters
2. Simplify the graph structure
3. Remove non-ASCII characters from labels
4. Try SVG output instead of base64
5. Fall back to text description

## Notes

- Mermaid is free and doesn't consume API quota
- For Obsidian, install "Excalidraw" or "Mermaid" plugin for live preview
- Complex diagrams may render better as image-generation
- mindmap syntax is newer - test compatibility
