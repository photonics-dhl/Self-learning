<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>量子光学交互可视化</title>
    <style>
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 { color: #00d4ff; text-align: center; }
        h2 { color: #ff6b6b; border-bottom: 1px solid #333; padding-bottom: 10px; }

        .visualization-container {
            background: #16213e;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 15px 0;
            padding: 15px;
            background: #0f3460;
            border-radius: 10px;
        }

        .control-group {
            flex: 1;
            min-width: 200px;
        }

        .control-group label {
            display: block;
            margin-bottom: 8px;
            color: #00d4ff;
            font-weight: bold;
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #1a1a2e;
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #00d4ff;
            cursor: pointer;
            box-shadow: 0 0 10px #00d4ff;
        }

        .value-display {
            display: inline-block;
            margin-left: 10px;
            color: #ff6b6b;
            font-weight: bold;
        }

        canvas {
            background: #0a0a1a;
            border-radius: 10px;
            width: 100%;
            max-width: 600px;
            display: block;
            margin: 0 auto;
        }

        .formula {
            text-align: center;
            font-size: 1.2em;
            padding: 15px;
            background: #0f3460;
            border-radius: 10px;
            margin: 15px 0;
            color: #fff;
        }

        .description {
            color: #aaa;
            line-height: 1.6;
            margin: 10px 0;
        }

        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }

        .nav-btn {
            padding: 10px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }

        .nav-btn.active {
            background: #00d4ff;
            color: #1a1a2e;
        }

        .nav-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(0,212,255,0.5);
        }
    </style>
</head>
<body>
    <h1>🔬 量子光学交互可视化</h1>

    <div class="nav-buttons">
        <button class="nav-btn active" onclick="showViz('fock')">Fock态</button>
        <button class="nav-btn" onclick="showViz('coherent')">相干态</button>
        <button class="nav-btn" onclick="showViz('squeezed')">压缩态</button>
        <button class="nav-btn" onclick="showViz('rabi')">Rabi振荡</button>
        <button class="nav-btn" onclick="showViz('statistics')">光子统计</button>
    </div>

    <!-- Fock态可视化 -->
    <div id="fock-viz" class="visualization-container">
        <h2>📊 Fock态光子数分布</h2>
        <p class="description">
            Fock态 |n⟩ 是光子数确定的态，每次测量得到确定的光子数。
            拖动滑块观察不同平均光子数下相干态的分布如何逼近Fock态。
        </p>

        <div class="controls">
            <div class="control-group">
                <label>相干态振幅 α |α⟩ = <span id="alpha-val" class="value-display">2.0</span></label>
                <input type="range" id="alpha-slider" min="0" max="5" step="0.1" value="2" oninput="updateFock()">
            </div>
            <div class="control-group">
                <label>显示范围 N = <span id="n-val" class="value-display">10</span></label>
                <input type="range" id="n-slider" min="5" max="30" step="1" value="10" oninput="updateFock()">
            </div>
        </div>

        <canvas id="fock-canvas" width="600" height="400"></canvas>

        <div class="formula">
            P(n) = |⟨n|α⟩|² = e<sup>-|α|²</sup> · |α|<sup>2n</sup> / n! &nbsp;&nbsp; (泊松分布)
        </div>
    </div>

    <!-- 相干态可视化 -->
    <div id="coherent-viz" class="visualization-container" style="display:none">
        <h2>🎯 相干态相空间表示 (Q函数)</h2>
        <p class="description">
            相干态 |α⟩ 是湮灭算符的本征态，在相空间中表现为高斯波包。
            拖动滑块观察Q函数的分布变化。
        </p>

        <div class="controls">
            <div class="control-group">
                <label>Re(α) = <span id="re-alpha-val" class="value-display">2.0</span></label>
                <input type="range" id="re-alpha-slider" min="-4" max="4" step="0.1" value="2" oninput="updateCoherent()">
            </div>
            <div class="control-group">
                <label>Im(α) = <span id="im-alpha-val" class="value-display">1.0</span></label>
                <input type="range" id="im-alpha-slider" min="-4" max="4" step="0.1" value="1" oninput="updateCoherent()">
            </div>
        </div>

        <canvas id="coherent-canvas" width="600" height="400"></canvas>

        <div class="formula">
            Q(α) = |⟨α|β⟩|² / π = (1/π) · exp(-|α-β|²)
        </div>
    </div>

    <!-- 压缩态可视化 -->
    <div id="squeezed-viz" class="visualization-container" style="display:none">
        <h2>📐 压缩态不确定椭圆</h2>
        <p class="description">
            压缩态将噪声从X方向"挤压"到P方向，保持ΔX·ΔP=1/4。
            拖动滑块观察不同压缩参数r下的椭圆变化。
        </p>

        <div class="controls">
            <div class="control-group">
                <label>压缩参数 r = <span id="r-val" class="value-display">1.0</span></label>
                <input type="range" id="r-slider" min="0" max="2.5" step="0.1" value="1" oninput="updateSqueezed()">
            </div>
            <div class="control-group">
                <label>旋转角 φ = <span id="phi-val" class="value-display">45</span>°</label>
                <input type="range" id="phi-slider" min="0" max="180" step="5" value="45" oninput="updateSqueezed()">
            </div>
        </div>

        <canvas id="squeezed-canvas" width="600" height="400"></canvas>

        <div class="formula">
            ΔX<sub>r</sub> = (1/2)·e<sup>-r</sup> &nbsp;&nbsp; ΔP<sub>r</sub> = (1/2)·e<sup>+r</sup>
        </div>
    </div>

    <!-- Rabi振荡可视化 -->
    <div id="rabi-viz" class="visualization-container" style="display:none">
        <h2>⚡ Rabi振荡</h2>
        <p class="description">
            二能级原子在光场中发生周期性跃迁，称为Rabi振荡。
            拖动滑块观察耦合强度g和失谐量δ对振荡的影响。
        </p>

        <div class="controls">
            <div class="control-group">
                <label>耦合强度 g = <span id="g-val" class="value-display">1.0</span></label>
                <input type="range" id="g-slider" min="0.1" max="3" step="0.1" value="1" oninput="updateRabi()">
            </div>
            <div class="control-group">
                <label>失谐量 δ = <span id="delta-val" class="value-display">0.0</span></label>
                <input type="range" id="delta-slider" min="-2" max="2" step="0.1" value="0" oninput="updateRabi()">
            </div>
        </div>

        <canvas id="rabi-canvas" width="600" height="400"></canvas>

        <div class="formula">
            Ω<sub>R</sub> = 2√(g² + δ²) &nbsp;&nbsp; 共振时(δ=0): Ω<sub>R</sub> = 2g
        </div>
    </div>

    <!-- 光子统计可视化 -->
    <div id="statistics-viz" class="visualization-container" style="display:none">
        <h2>📈 光子统计对比</h2>
        <p class="description">
            不同光源有不同的光子统计：相干光是泊松分布，热光是超泊松分布，Fock态无涨落。
        </p>

        <div class="controls">
            <div class="control-group">
                <label>平均光子数 ⟨n⟩ = <span id="mean-n-val" class="value-display">4</span></label>
                <input type="range" id="mean-n-slider" min="1" max="20" step="1" value="4" oninput="updateStatistics()">
            </div>
        </div>

        <canvas id="statistics-canvas" width="600" height="400"></canvas>

        <div class="formula">
            相干态: g²(0) = 1 &nbsp;|&nbsp; 热光: g²(0) = 2 &nbsp;|&nbsp; Fock态: g²(0) = 0
        </div>
    </div>

    <script>
        // 通用设置
        const colors = {
            primary: '#00d4ff',
            secondary: '#ff6b6b',
            accent: '#4ecdc4',
            purple: '#a855f7',
            orange: '#f97316'
        };

        // 数学函数
        function factorial(n) {
            if (n <= 1) return 1;
            let result = 1;
            for (let i = 2; i <= n; i++) result *= i;
            return result;
        }

        function poisson(n, lambda) {
            return Math.exp(-lambda) * Math.pow(lambda, n) / factorial(Math.round(n));
        }

        // 显示/隐藏可视化
        function showViz(name) {
            document.querySelectorAll('.visualization-container').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

            document.getElementById(name + '-viz').style.display = 'block';
            event.target.classList.add('active');

            // 初始化
            if (name === 'fock') updateFock();
            else if (name === 'coherent') updateCoherent();
            else if (name === 'squeezed') updateSqueezed();
            else if (name === 'rabi') updateRabi();
            else if (name === 'statistics') updateStatistics();
        }

        // ===== Fock态可视化 =====
        function updateFock() {
            const alpha = parseFloat(document.getElementById('alpha-slider').value);
            const N = parseInt(document.getElementById('n-slider').value);

            document.getElementById('alpha-val').textContent = alpha.toFixed(1);
            document.getElementById('n-val').textContent = N;

            const canvas = document.getElementById('fock-canvas');
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;

            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, w, h);

            // 绘制坐标轴
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(50, h - 50);
            ctx.lineTo(w - 20, h - 50);
            ctx.moveTo(50, h - 50);
            ctx.lineTo(50, 50);
            ctx.stroke();

            // 标签
            ctx.fillStyle = '#888';
            ctx.font = '12px Arial';
            ctx.fillText('n (光子数)', w/2, h - 15);
            ctx.save();
            ctx.translate(20, h/2);
            ctx.rotate(-Math.PI/2);
            ctx.fillText('P(n)', 0, 0);
            ctx.restore();

            // 绘制泊松分布
            const barWidth = (w - 100) / N;
            const maxP = poisson(alpha*alpha, alpha*alpha);

            for (let n = 0; n <= N; n++) {
                const p = poisson(n, alpha*alpha);
                const barHeight = (p / maxP) * (h - 120);

                // 渐变色
                const gradient = ctx.createLinearGradient(0, h-50-barHeight, 0, h-50);
                gradient.addColorStop(0, colors.primary);
                gradient.addColorStop(1, colors.secondary);

                ctx.fillStyle = gradient;
                ctx.fillRect(50 + n * barWidth + 2, h - 50 - barHeight, barWidth - 4, barHeight);

                // 数值标签
                if (p > 0.05) {
                    ctx.fillStyle = '#fff';
                    ctx.font = '10px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(n, 50 + n * barWidth + barWidth/2, h - 55 - barHeight);
                }
            }

            // 信息框
            ctx.fillStyle = 'rgba(0,212,255,0.2)';
            ctx.fillRect(w - 150, 20, 130, 60);
            ctx.fillStyle = colors.primary;
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(`⟨n⟩ = ${(alpha*alpha).toFixed(1)}`, w - 140, 42);
            ctx.fillText(`σ = ${alpha.toFixed(1)}`, w - 140, 60);
        }

        // ===== 相干态可视化 =====
        function updateCoherent() {
            const reAlpha = parseFloat(document.getElementById('re-alpha-slider').value);
            const imAlpha = parseFloat(document.getElementById('im-alpha-slider').value);

            document.getElementById('re-alpha-val').textContent = reAlpha.toFixed(1);
            document.getElementById('im-alpha-val').textContent = imAlpha.toFixed(1);

            const canvas = document.getElementById('coherent-canvas');
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;
            const cx = w/2, cy = h/2;
            const scale = 40;

            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, w, h);

            // 坐标轴
            ctx.strokeStyle = '#444';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(0, cy);
            ctx.lineTo(w, cy);
            ctx.moveTo(cx, 0);
            ctx.lineTo(cx, h);
            ctx.stroke();

            // 轴标签
            ctx.fillStyle = '#888';
            ctx.font = '14px Arial';
            ctx.fillText('Re(α)', w - 40, cy - 10);
            ctx.fillText('Im(α)', cx + 10, 20);

            // Q函数热力图
            const resolution = 100;
            const imageData = ctx.createImageData(w, h);

            for (let py = 0; py < h; py++) {
                for (let px = 0; px < w; px++) {
                    const x = (px - cx) / scale;
                    const y = (cy - py) / scale;

                    const dx = x - reAlpha;
                    const dy = y - imAlpha;
                    const r2 = dx*dx + dy*dy;
                    const Q = Math.exp(-r2) / Math.PI;

                    // 归一化并映射到颜色
                    const idx = (py * w + px) * 4;
                    const intensity = Math.min(255, Q * 500);

                    if (Q > 0.3) {
                        imageData.data[idx] = 255;     // R
                        imageData.data[idx+1] = 100;    // G
                        imageData.data[idx+2] = 50;     // B
                        imageData.data[idx+3] = intensity;
                    } else {
                        imageData.data[idx] = 0;
                        imageData.data[idx+1] = Math.floor(intensity * 0.8);
                        imageData.data[idx+2] = Math.floor(intensity);
                        imageData.data[idx+3] = 150;
                    }
                }
            }
            ctx.putImageData(imageData, 0, 0);

            // 标记相干态位置
            ctx.beginPath();
            ctx.arc(cx + reAlpha * scale, cy - imAlpha * scale, 8, 0, Math.PI * 2);
            ctx.fillStyle = colors.primary;
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.fillStyle = '#fff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(`|α⟩`, cx + reAlpha * scale + 15, cy - imAlpha * scale - 10);
        }

        // ===== 压缩态可视化 =====
        function updateSqueezed() {
            const r = parseFloat(document.getElementById('r-slider').value);
            const phiDeg = parseFloat(document.getElementById('phi-slider').value);
            const phi = phiDeg * Math.PI / 180;

            document.getElementById('r-val').textContent = r.toFixed(1);
            document.getElementById('phi-val').textContent = phiDeg;

            const canvas = document.getElementById('squeezed-canvas');
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;
            const cx = w/2, cy = h/2;
            const scale = 60;

            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, w, h);

            // 真空圆
            ctx.beginPath();
            ctx.arc(cx, cy, 0.5 * scale, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(100,100,100,0.2)';
            ctx.fill();
            ctx.strokeStyle = '#666';
            ctx.lineWidth = 1;
            ctx.stroke();

            // 压缩椭圆
            const a = 0.5 * Math.exp(r);
            const b = 0.5 * Math.exp(-r);

            ctx.beginPath();
            for (let t = 0; t <= Math.PI * 2; t += 0.01) {
                const xEllipse = a * Math.cos(t);
                const yEllipse = b * Math.sin(t);

                // 旋转
                const x = xEllipse * Math.cos(phi) - yEllipse * Math.sin(phi);
                const y = xEllipse * Math.sin(phi) + yEllipse * Math.cos(phi);

                const px = cx + x * scale;
                const py = cy - y * scale;

                if (t === 0) ctx.moveTo(px, py);
                else ctx.lineTo(px, py);
            }
            ctx.closePath();

            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, scale);
            gradient.addColorStop(0, colors.primary);
            gradient.addColorStop(1, colors.secondary);
            ctx.fillStyle = gradient;
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // X和P轴
            ctx.strokeStyle = colors.secondary;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(50, cy);
            ctx.lineTo(w - 50, cy);
            ctx.moveTo(cx, 50);
            ctx.lineTo(cx, h - 50);
            ctx.stroke();

            ctx.fillStyle = colors.secondary;
            ctx.font = 'bold 16px Arial';
            ctx.fillText('X', w - 35, cy - 10);
            ctx.fillText('P', cx + 10, 40);

            // 信息
            ctx.fillStyle = 'rgba(0,212,255,0.2)';
            ctx.fillRect(w - 140, h - 80, 120, 60);
            ctx.fillStyle = colors.primary;
            ctx.font = 'bold 12px Arial';
            ctx.fillText(`ΔX = ${(0.5*Math.exp(-r)).toFixed(3)}`, w - 130, h - 55);
            ctx.fillText(`ΔP = ${(0.5*Math.exp(r)).toFixed(3)}`, w - 130, h - 35);
        }

        // ===== Rabi振荡可视化 =====
        function updateRabi() {
            const g = parseFloat(document.getElementById('g-slider').value);
            const delta = parseFloat(document.getElementById('delta-slider').value);

            document.getElementById('g-val').textContent = g.toFixed(1);
            document.getElementById('delta-val').textContent = delta.toFixed(1);

            const canvas = document.getElementById('rabi-canvas');
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;

            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, w, h);

            const Omega = 2 * Math.sqrt(g*g + delta*delta);
            const T = 12 / Math.min(g, 0.5);

            // 绘制概率曲线
            ctx.beginPath();
            ctx.strokeStyle = colors.primary;
            ctx.lineWidth = 3;

            for (let t = 0; t <= T; t += 0.05) {
                let P2;
                if (Math.abs(delta) < 0.01) {
                    P2 = Math.sin(g * t) * Math.sin(g * t);
                } else {
                    const Omega_t = Omega * t / 2;
                    P2 = (4*g*g / (Omega*Omega)) * Math.sin(Omega_t) * Math.sin(Omega_t);
                }

                const x = 50 + (t / T) * (w - 100);
                const y = h - 50 - P2 * (h - 100);

                if (t === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // 基态概率
            ctx.strokeStyle = colors.secondary;
            ctx.lineWidth = 3;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();

            for (let t = 0; t <= T; t += 0.05) {
                let P1;
                if (Math.abs(delta) < 0.01) {
                    P1 = Math.cos(g * t) * Math.cos(g * t);
                } else {
                    const Omega_t = Omega * t / 2;
                    const cos2 = Math.cos(Omega_t);
                    P1 = 1 - (4*g*g / (Omega*Omega)) * Math.sin(Omega_t) * Math.sin(Omega_t);
                }

                const x = 50 + (t / T) * (w - 100);
                const y = h - 50 - P1 * (h - 100);

                if (t === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
            ctx.setLineDash([]);

            // 轴
            ctx.strokeStyle = '#444';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(50, h - 50);
            ctx.lineTo(w - 20, h - 50);
            ctx.moveTo(50, h - 50);
            ctx.lineTo(50, 50);
            ctx.stroke();

            // 标签
            ctx.fillStyle = '#888';
            ctx.font = '12px Arial';
            ctx.fillText('时间 t', w/2, h - 10);
            ctx.save();
            ctx.translate(15, h/2);
            ctx.rotate(-Math.PI/2);
            ctx.fillText('P', 0, 0);
            ctx.restore();

            // 图例
            ctx.fillStyle = colors.primary;
            ctx.fillRect(w - 120, 30, 15, 15);
            ctx.fillStyle = '#fff';
            ctx.font = '12px Arial';
            ctx.fillText('P₂ (激发态)', w - 100, 42);

            ctx.fillStyle = colors.secondary;
            ctx.fillRect(w - 120, 55, 15, 15);
            ctx.fillStyle = '#fff';
            ctx.fillText('P₁ (基态)', w - 100, 67);

            // Rabi频率
            ctx.fillStyle = 'rgba(0,212,255,0.2)';
            ctx.fillRect(50, 20, 140, 35);
            ctx.fillStyle = colors.primary;
            ctx.font = 'bold 12px Arial';
            ctx.fillText(`Ω_R = ${Omega.toFixed(2)}`, 60, 40);
        }

        // ===== 光子统计可视化 =====
        function updateStatistics() {
            const meanN = parseInt(document.getElementById('mean-n-slider').value);
            document.getElementById('mean-n-val').textContent = meanN;

            const canvas = document.getElementById('statistics-canvas');
            const ctx = canvas.getContext('2d');
            const w = canvas.width, h = canvas.height;

            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(0, 0, w, h);

            const N = Math.min(30, meanN * 2 + 5);

            // 绘制泊松分布
            const barWidth = (w - 100) / N;
            const maxP = poisson(meanN, meanN);

            // 相干态（泊松）
            for (let n = 0; n <= N; n++) {
                const p = poisson(n, meanN);
                const barHeight = (p / maxP) * (h - 120);

                ctx.fillStyle = colors.primary;
                const x = 50 + n * barWidth + 2;
                ctx.fillRect(x, h - 50 - barHeight, barWidth/3 - 2, barHeight);
            }

            // Fock态（确定性）
            const fockHeight = (h - 120);
            ctx.fillStyle = colors.secondary;
            ctx.fillRect(50 + meanN * barWidth + barWidth/3, h - 50 - fockHeight, barWidth/3 - 2, fockHeight);
            ctx.fillStyle = '#fff';
            ctx.font = '10px Arial';
            ctx.fillText('|n⟩', 50 + meanN * barWidth + barWidth/3 + 5, h - 55 - fockHeight);

            // 热光分布
            ctx.globalAlpha = 0.3;
            for (let n = 0; n <= N; n++) {
                const p_thermal = 1 / (meanN + 1) * Math.pow(meanN / (meanN + 1), n);
                const barHeight = (p_thermal / maxP) * (h - 120);

                ctx.fillStyle = colors.accent;
                ctx.fillRect(50 + n * barWidth + 2*barWidth/3, h - 50 - barHeight, barWidth/3 - 2, barHeight);
            }
            ctx.globalAlpha = 1;

            // 轴
            ctx.strokeStyle = '#444';
            ctx.beginPath();
            ctx.moveTo(50, h - 50);
            ctx.lineTo(w - 20, h - 50);
            ctx.stroke();

            ctx.fillStyle = '#888';
            ctx.font = '12px Arial';
            ctx.fillText('n', w/2, h - 10);

            // 图例
            ctx.fillStyle = colors.primary;
            ctx.fillRect(w - 150, 25, 15, 15);
            ctx.fillStyle = '#fff';
            ctx.font = '11px Arial';
            ctx.fillText('相干态 (泊松)', w - 130, 37);

            ctx.fillStyle = colors.accent;
            ctx.fillRect(w - 150, 45, 15, 15);
            ctx.fillStyle = '#fff';
            ctx.fillText('热光 (超泊松)', w - 130, 57);

            ctx.fillStyle = colors.secondary;
            ctx.fillRect(w - 150, 65, 15, 15);
            ctx.fillStyle = '#fff';
            ctx.fillText('Fock态 (确定)', w - 130, 77);
        }

        // 初始化
        updateFock();
    </script>
</body>
</html>
