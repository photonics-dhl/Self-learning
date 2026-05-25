---
name: diagram-generator
description: |
  Advanced diagram generation skill supporting DrawIO, Mermaid, and Excalidraw formats for creating professional technical diagrams.

  **Trigger when**: User says "生成图表", "DrawIO", "excalidraw", "专业技术图", "architecture diagram", "系统架构图", "wireframe"

  **Also trigger when**: User wants:
  - Professional architecture diagrams
  - UML diagrams with more detail than Mermaid
  - Interactive diagrams (Excalidraw)
  - Technical drawings with precise shapes
  - Network diagrams
  - UI wireframes

  **DO NOT trigger for**: Simple flowcharts (use mermaid), photo-realistic images (use image-generation).

  Make sure to use this skill when the user needs more sophisticated diagrams than Mermaid can provide, or when they specifically request DrawIO/Excalidraw format.
---

# Diagram Generator Skill

## Overview

This skill generates professional technical diagrams in multiple formats: DrawIO (XML-based), Mermaid, and Excalidraw (hand-drawn style). Choose the format based on use case needs.

## Diagram Generator MCP Tools

The following MCP tools are available:
- `generate_diagram` - Generate diagram from structured JSON spec
- `get_config` - Get current diagram configuration
- `set_output_path` - Set default output path
- `validate_diagram_spec` - Validate diagram specification

## Supported Formats

| Format | Best For | File Extension |
|--------|----------|----------------|
| DrawIO | Technical diagrams, architecture | `.drawio` |
| Mermaid | Flowcharts, simple diagrams | `.mmd` or embedded |
| Excalidraw | Hand-drawn style, collaborative | `.excalidraw` |

## Diagram Specification Structure

```json
{
  "format": "drawio",
  "elements": [
    {
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "label": "Process",
      "style": "fillColor=#f3f3f3;strokeColor=#363636"
    },
    {
      "type": "arrow",
      "from": "node1",
      "to": "node2",
      "style": "endArrow=classic"
    }
  ],
  "theme": {
    "background": "#ffffff",
    "primary": "#0070c0"
  }
}
```

## Element Types

### Basic Shapes
- `rectangle` - Rounded rectangle
- `ellipse` - Circle/oval
- `diamond` - Decision rhombus
- `parallelogram` - Data/process
- `cylinder` - Database
- `hexagon` - Preparation

### Connectors
- `arrow` - Directed arrow
- `line` - Simple line
- `dashed_arrow` - Dashed connector

### Text
- `text` - Standalone text label

## Usage Guidelines

### When to Use Each Format

| Diagram Type | Format | Example |
|-------------|--------|---------|
| Architecture | DrawIO | Microservices, network topology |
| Simple flowchart | Mermaid | Quick process visualization |
| Brainstorming | Excalidraw | Collaborative sketching |
| Technical spec | DrawIO | Detailed component diagrams |
| Presentation | Excalidraw | Hand-drawn aesthetic |

### Recommended Parameters

```
format: "drawio"              # or "mermaid", "excalidraw"
output_path: "Obsidian-Vault/6️⃣ 工具/visualizations/"
```

## Example Diagrams

### Optical System Architecture (DrawIO)

```json
{
  "format": "drawio",
  "elements": [
    {
      "type": "rectangle",
      "id": "laser",
      "x": 50,
      "y": 100,
      "width": 80,
      "height": 60,
      "label": "Ti:Sapphire\nLaser",
      "style": "fillColor=#e1e1e1;strokeColor=#000000"
    },
    {
      "type": "rectangle",
      "id": "pca",
      "x": 200,
      "y": 100,
      "width": 80,
      "height": 60,
      "label": "PCA\nEmitter",
      "style": "fillColor=#f3f3f3;strokeColor=#000000"
    },
    {
      "type": "arrow",
      "from": "laser",
      "to": "pca",
      "label": "Pump",
      "style": "endArrow=classic;strokeColor=#ff0000"
    }
  ]
}
```

### Research Workflow (Excalidraw)

```json
{
  "format": "excalidraw",
  "elements": [
    {
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 150,
      "height": 80,
      "label": "Literature Review"
    }
  ]
}
```

## Best Practices

1. **Use DrawIO for technical precision** - Coordinates, styles, exact shapes
2. **Use Excalidraw for collaborative brainstorming** - Hand-drawn aesthetic
3. **Validate specs** - Use `validate_diagram_spec` before generation
4. **Set output path** - Configure once, reuse for consistency
5. **Combine with Mermaid** - For complex diagrams, use Mermaid for parts

## Integration with Project

1. Generate diagram with `generate_diagram`
2. Save to: `Obsidian-Vault/6️⃣ 工具/visualizations/`
3. Filename: `{type}_{topic}_{date}.{format}`
4. Insert in Obsidian:
   - DrawIO/Mermaid: ` ```mermaid ` or link to .drawio
   - Excalidraw: `![[visualizations/diagram.excalidraw]]`
5. Run sync script if needed

## Error Handling

If diagram generation fails:
1. Validate spec with `validate_diagram_spec`
2. Check element types are supported
3. Verify coordinates are valid numbers
4. Simplify - reduce number of elements
5. Try different format

## Notes

- DrawIO files can be edited in draw.io app or VS Code extension
- Excalidraw supports collaboration
- For simple diagrams, Mermaid skill may be faster
- diagram-generator MCP can also output Mermaid format
