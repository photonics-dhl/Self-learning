# 量子光学可视化系统使用指南

## 概述

这个可视化系统允许你通过Obsidian笔记中的链接或右键菜单，触发Python生成的可视化图像，帮助理解量子光学的核心概念。

## 快速开始
v
### 1. 启动可视化服务器V

```bash
cd "z:/321/DHL/Self_Learning"
python .claude/hooks/viz_server.py --port 8765
```

服务器将在 `http://localhost:8765` 启动。

### 2. 命令行生成可视化

```bash
# 列出所有可用概念
python .claude/hooks/viz_engine.py --list

# 生成单个可视化
python .claude/hooks/viz_engine.py --concept fock_state
python .claude/hooks/viz_engine.py --concept rabi_oscillation
python .claude/hooks/viz_engine.py --concept bell_state

# 带参数生成
python .claude/hooks/viz_engine.py --concept fock_state --params "alpha_values=0,1,2,3"
```

### 3. Obsidian中使用

#### 方式1：内嵌链接

在Obsidian笔记中添加链接：

```
[[runviz:fock_state]]
[[runviz:coherent_state]]
[[runviz:rabi_oscillation]]
[[runviz:squeezed_state]]
[[runviz:vacuum_fluctuation]]
[[runviz:jaynes_cummings]]
[[runviz:bell_state]]
[[runviz:spdc]]
[[runviz:bloch_sphere]]
[[runviz:photon_statistics]]
[[runviz:antibunching]]
```

#### 方式2：Templater脚本触发

创建Templater模板 `viz_trigger.md`:
```markdown
<%*
const concept = tp.system.prompt("输入可视化概念:");
if (concept) {
  const result = await tp.system.run_command(`python .claude/hooks/viz_engine.py --concept ${concept}`);
  tR += `![[${concept}.png]]`;
}
%>
```

#### 方式3：QuickAdd插件

1. 安装 QuickAdd 插件
2. 创建宏：
   ```javascript
   module.exports = {
     addToMacros: (macros) => {
       macros.visualizeConcept = async (params, app) => {
         const concept = await app.plugins.plugins.quickadd.api.inputPrompt('概念:');
         if (concept) {
           const { exec } = require('child_process');
           exec(`python .claude/hooks/viz_engine.py --concept ${concept}`);
         }
       };
     }
   }
   ```

### 4. 右键菜单触发（推荐）

由于Obsidian不原生支持自定义右键菜单，推荐使用以下方案：

#### 方案A：使用Obsidian的Templater插件

1. 安装 Templater 插件
2. 创建模板文件 `viz_trigger.md`:
```markdown
<%*
const selected = app.workspace.activeLeaf.view.sourceMode.cmEditor.selection;
const concept = selected || await tp.system.prompt("输入可视化概念:");
if (concept && concept.trim()) {
  const cmd = `python "${app.vault.adapter.basePath}/.claude/hooks/viz_engine.py" --concept ${concept.trim()}`;
  const { exec } = require('child_process');
  exec(cmd, (err, stdout, stderr) => {
    if (err) console.error(stderr);
    else console.log(stdout);
  });
  await tp.file.include(`![[${concept.trim()}.png]]`);
}
%>
```

3. 设置快捷键（如 `Ctrl+Shift+V`）触发模板

#### 方案B：使用Obsidian的Custom Frames

创建本地HTML页面调用服务器API：

```html
<!DOCTYPE html>
<html>
<head>
  <title>量子光学可视化</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .concept-btn { padding: 10px; margin: 5px; cursor: pointer; }
    #result { margin-top: 20px; }
  </style>
</head>
<body>
  <h1>量子光学可视化</h1>
  <div id="buttons"></div>
  <div id="result"></div>

  <script>
    const concepts = ['fock_state','coherent_state','squeezed_state',
                      'vacuum_fluctuation','rabi_oscillation','jaynes_cummings',
                      'bell_state','spdc','bloch_sphere','photon_statistics','antibunching'];

    concepts.forEach(c => {
      const btn = document.createElement('button');
      btn.className = 'concept-btn';
      btn.textContent = c.replace('_', ' ');
      btn.onclick = () => fetch(`/viz/${c}`).then(r => r.json()).then(d => {
        document.getElementById('result').innerHTML =
          `<img src="${d.output_url}" width="600"/>`;
      });
      document.getElementById('buttons').appendChild(btn);
    });
  </script>
</body>
</html>
```

## 可视化概念列表

| 概念ID | 说明 | 适用场景 |
|--------|------|----------|
| `fock_state` | Fock态光子数分布 | 理解光子数确定态 vs 相干态 |
| `coherent_state` | 相干态相空间Q函数 | 可视化复振幅 |
| `squeezed_state` | 压缩态不确定椭圆 | 理解噪声压缩 |
| `vacuum_fluctuation` | 真空涨落示意 | 理解零点能 |
| `rabi_oscillation` | Rabi振荡动画 | 光与原子相互作用 |
| `jaynes_cummings` | JC模型能级图 | 真空Rabi劈裂 |
| `bell_state` | Bell纠缠态 | EPR佯谬 |
| `spdc` | SPDC下转换 | 纠缠光子对产生 |
| `bloch_sphere` | Bloch球 | 量子态几何表示 |
| `photon_statistics` | 光子统计对比 | 聚束/反聚束 |
| `antibunching` | Antibunching效应 | HBT实验 |

## 输出位置

可视化图片保存在：
```
Obsidian-Vault/6️⃣ 工具/visualizations/
├── fock_state.png
├── coherent_state.png
├── squeezed_state.png
├── ...
```

## 技术架构

```
Obsidian笔记                    Python可视化引擎
     │                                │
     │  [[runviz:concept]]            │
     │  或右键触发                    │
     ▼                                ▼
┌─────────────────┐        ┌─────────────────────┐
│  Templater/     │ ────▶  │  viz_engine.py      │
│  QuickAdd       │        │  (matplotlib)       │
└─────────────────┘        └─────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────────┐
                         │ visualizations/     │
                         │ (PNG输出)            │
                         └─────────────────────┘
```

## 故障排除

### 服务器无法启动
```bash
# 检查端口占用
netstat -an | grep 8765

# 使用其他端口
python viz_server.py --port 8766
```

### 可视化文件未生成
```bash
# 直接运行测试
python .claude/hooks/viz_engine.py --concept fock_state --output ./test.png

# 检查错误输出
python .claude/hooks/viz_engine.py --concept fock_state -d .
```

### Obsidian无法显示图片
- 确保图片路径正确
- 确认Obsidian已启用本地图片嵌入
- 使用绝对路径：`![[z:/321/DHL/Self_Learning/Obsidian-Vault/6️⃣ 工具/visualizations/fock_state.png]]`

## 扩展开发

要添加新的可视化，在 `viz_engine.py` 中添加函数：

```python
def viz_your_concept(output_path: str = None, **params):
    """
    你的概念说明（会显示在--list中）
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    # 你的绘图代码
    # ...
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path

# 在VISUALIZATION_FUNCTIONS字典中注册
VISUALIZATION_FUNCTIONS['your_concept'] = viz_your_concept
```

---

*最后更新：2026-04-16*
