#!/usr/bin/env python3
"""
量子光学可视化引擎 (Quantum Optics Visualization Engine)
===========================================

功能：从Obsidian笔记中提取可视化指令，生成Python/matplotlib可视化

使用方法：
    python viz_engine.py --concept fock_state --output viz_output/
    python viz_engine.py --concept rabi_oscillation --params "alpha=0.5,g=1.0"

可视化概念列表：
    - fock_state: Fock态光子数分布
    - coherent_state: 相干态相空间表示
    - squeezed_state: 压缩态不确定椭圆
    - vacuum_fluctuation: 真空涨落示意
    - rabi_oscillation: Rabi振荡动画
    - jaynes_cummings: Jaynes-Cummings能级图
    - bell_state: Bell纠缠态示意
    - spdc: SPDC参量下转换
    - bloch_sphere: Bloch球
    - photon_statistics: 光子统计对比
    - antibunching: Antibunching效应
"""

import argparse
import os
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Arrow, FancyArrowPatch
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
import warnings

warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# Windows控制台编码处理
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 输出目录
DEFAULT_OUTPUT = "Obsidian-Vault/6️⃣ 工具/visualizations"
os.makedirs(DEFAULT_OUTPUT, exist_ok=True)

def get_output_path(concept: str, output_dir: str = DEFAULT_OUTPUT) -> str:
    """生成输出文件路径"""
    return os.path.join(output_dir, f"{concept}.png")


def viz_fock_state(output_path: str = None, **params):
    """
    Fock态光子数分布可视化

    参数：
        n_max: 最大光子数 (默认: 20)
        alpha_values: 相干态振幅列表 (默认: [0, 1, 2, 3])
    """
    n_max = params.get('n_max', 20)
    alpha_values = params.get('alpha_values', [0, 1, 2, 3])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Fock态与相干态的光子数分布', fontsize=16, fontweight='bold')

    # 左上：纯Fock态
    ax1 = axes[0, 0]
    n_vals = np.arange(0, 11)
    for n in n_vals:
        ax1.bar(n, 1, width=0.6, color='steelblue', alpha=0.8)
    ax1.set_xlabel('光子数 n')
    ax1.set_ylabel('概率')
    ax1.set_title('纯Fock态 |n⟩ (以|5⟩为例)')
    ax1.set_xticks(n_vals)
    ax1.set_ylim(0, 1.3)
    ax1.annotate('|5⟩', xy=(5, 1.1), ha='center', fontsize=12)

    # 右上：不同alpha的泊松分布
    ax2 = axes[0, 1]
    n_vals = np.arange(0, 20)
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    for i, alpha in enumerate(alpha_values):
        # 泊松分布 P(n) = e^{-α²} α^{2n} / n!
        probabilities = np.exp(-alpha**2) * (alpha**(2*n_vals)) / np.array([math.factorial(int(n)) for n in n_vals])
        ax2.bar(n_vals + i*0.2 - 0.3, probabilities, width=0.18,
                label=f'α={alpha} (n̄={alpha**2:.1f})', color=colors[i], alpha=0.8)

    ax2.set_xlabel('光子数 n')
    ax2.set_ylabel('概率 P(n)')
    ax2.set_title('相干态|α⟩的光子数分布(泊松分布)')
    ax2.legend(loc='upper right')
    ax2.set_xlim(-0.5, 15)

    # 左下：Fock态展开系数
    ax3 = axes[1, 0]
    alpha = 2.0
    n_vals = np.arange(0, 15)
    probabilities = np.exp(-alpha**2) * (alpha**(2*n_vals)) / np.array([math.factorial(int(n)) for n in n_vals])

    bars = ax3.bar(n_vals, probabilities, width=0.6, color='coral', alpha=0.8, edgecolor='darkred')
    ax3.axhline(y=0, color='black', linewidth=0.5)
    ax3.set_xlabel('光子数 n')
    ax3.set_ylabel('|⟨n|α⟩|²')
    ax3.set_title(f'相干态|α={alpha}⟩的Fock态展开系数')
    ax3.set_xticks(n_vals)

    # 添加数值标签
    for bar, prob in zip(bars, probabilities):
        if prob > 0.02:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{prob:.3f}', ha='center', va='bottom', fontsize=7)

    # 右下：统计性质对比
    ax4 = axes[1, 1]
    alphas = np.linspace(0.1, 4, 50)
    mean_n = alphas**2
    variance_n = alphas**2  # 泊松分布: 方差 = 均值

    ax4.fill_between(alphas, mean_n - np.sqrt(variance_n), mean_n + np.sqrt(variance_n),
                     alpha=0.3, color='blue', label='±σ 范围')
    ax4.plot(alphas, mean_n, 'b-', linewidth=2, label='均值 ⟨n⟩')
    ax4.set_xlabel('|α| (相干态振幅)')
    ax4.set_ylabel('光子数 n')
    ax4.set_title('相干态光子数涨落随振幅变化')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    output = output_path or get_output_path('fock_state')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Fock态可视化已保存: {output}")
    return output


def viz_coherent_state(output_path: str = None, **params):
    """
    相干态相空间可视化 (Q函数与Wigner函数)
    """
    alpha_max = params.get('alpha_max', 4)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('相干态|α⟩的相空间表示', fontsize=16, fontweight='bold')

    # 左：Q函数（Q函数是相干态的准概率分布）
    ax1 = axes[0]
    x = np.linspace(-alpha_max, alpha_max, 200)
    y = np.linspace(-alpha_max, alpha_max, 200)
    X, Y = np.meshgrid(x, y)
    alpha_complex = X + 1j*Y

    # Q函数: Q(α) = |⟨α|ψ⟩|² / π = e^{-|α|²}|ψ(α)|²/π
    # 对于相干态|β⟩, Q(α) = |⟨α|β⟩|²/π = e^{-|α-β|²}/π
    beta = 2 + 1j  # 相干态参数
    Q = np.exp(-np.abs(alpha_complex - beta)**2) / np.pi

    im1 = ax1.contourf(X, Y, Q, levels=50, cmap='RdYlBu_r')
    ax1.plot([0], [0], 'k+', markersize=15, label='原点')
    ax1.plot([beta.real], [beta.imag], 'r*', markersize=20, label=f'|α={beta}⟩')
    ax1.set_xlabel('Re(α)')
    ax1.set_ylabel('Im(α)')
    ax1.set_title('Q函数 (准概率分布)')
    ax1.set_aspect('equal')
    ax1.legend(loc='upper right')
    plt.colorbar(im1, ax=ax1, label='Q(α)')

    # 右：不同相干态的等高线
    ax2 = axes[1]
    alphas = [0, 1, 2, 3]
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(alphas)))

    for i, a in enumerate(alphas):
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = a * np.cos(theta)
        y_circle = a * np.sin(theta)
        ax2.plot(x_circle, y_circle, '-', color=colors[i], linewidth=2, label=f'|α|={a}')
        ax2.fill(x_circle, y_circle, color=colors[i], alpha=0.1)

    ax2.set_xlim(-4, 4)
    ax2.set_ylim(-4, 4)
    ax2.set_xlabel('Re(α)')
    ax2.set_ylabel('Im(α)')
    ax2.set_title('不同振幅相干态在相空间的圆')
    ax2.set_aspect('equal')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linewidth=0.5)
    ax2.axvline(x=0, color='k', linewidth=0.5)

    plt.tight_layout()

    output = output_path or get_output_path('coherent_state')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"相干态可视化已保存: {output}")
    return output


def viz_squeezed_state(output_path: str = None, **params):
    """
    压缩态不确定椭圆可视化
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.set_aspect('equal')

    # 绘制真空圆
    theta = np.linspace(0, 2*np.pi, 100)
    r = 0.5  # 真空不确定度半径
    x_vac = r * np.cos(theta)
    y_vac = r * np.sin(theta)
    ax.fill(x_vac, y_vac, alpha=0.2, color='gray', label='真空态不确定度圆')
    ax.plot(x_vac, y_vac, 'k-', linewidth=1)

    # 绘制不同压缩参数的椭圆
    squeeze_params = [0.5, 1.0, 1.5, 2.0]
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6']

    for i, r_squeeze in enumerate(squeeze_params):
        # 压缩后的不确定椭圆
        a = 0.5 * np.exp(r_squeeze)  # 长轴
        b = 0.5 * np.exp(-r_squeeze)  # 短轴
        theta_rot = np.linspace(0, 2*np.pi, 100)

        # 椭圆参数方程
        x_ellipse = a * np.cos(theta_rot)
        y_ellipse = b * np.sin(theta_rot)

        # 旋转45度
        angle = np.pi / 4
        x_rot = x_ellipse * np.cos(angle) - y_ellipse * np.sin(angle)
        y_rot = x_ellipse * np.sin(angle) + y_ellipse * np.cos(angle)

        ax.plot(x_rot, y_rot, '-', color=colors[i], linewidth=2,
               label=f'r={r_squeeze}')
        ax.fill(x_rot, y_rot, color=colors[i], alpha=0.05)

    # 标记X和P方向
    ax.annotate('', xy=(3.5, 0), xytext=(-3.5, 0),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.annotate('', xy=(0, 3.5), xytext=(0, -3.5),
               arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax.text(3.6, 0, 'X', color='red', fontsize=14, fontweight='bold')
    ax.text(0.15, 3.5, 'P', color='blue', fontsize=14, fontweight='bold')

    ax.set_xlim(-4, 4)
    ax.set_ylim(-4, 4)
    ax.set_xlabel('X quadrature')
    ax.set_ylabel('P quadrature')
    ax.set_title('压缩态的不确定椭圆\n(从圆压缩成椭圆，体积保持不变: ΔX·ΔP=1/4)', fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)

    plt.tight_layout()

    output = output_path or get_output_path('squeezed_state')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"压缩态可视化已保存: {output}")
    return output


def viz_vacuum_fluctuation(output_path: str = None, **params):
    """
    真空涨落可视化 - 虚粒子对产生湮灭示意
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')

    # 标题
    ax.text(5, 7.5, '真空涨落 (Vacuum Fluctuations)', fontsize=16,
           ha='center', fontweight='bold')

    # 中心区域 - 真空间
    circle = plt.Circle((5, 4), 2.5, fill=True, facecolor='lightyellow',
                        edgecolor='orange', linewidth=2, linestyle='--')
    ax.add_patch(circle)
    ax.text(5, 5.8, '真空间 |0⟩', fontsize=12, ha='center')

    # 虚粒子对动画序列
    time_steps = [
        ('t₀: 平静真空', 'gray', 0.3, '，虚对尚未产生'),
        ('t₁: 能量涨落\n触发虚对产生', 'red', 0.6, ' (ΔE·Δt ≥ ℏ/2)'),
        ('t₂: 虚对分离', 'purple', 0.8, '，虚光子交换'),
        ('t₃: 虚对湮灭', 'blue', 0.6, '，能量回归零点'),
        ('t₄: 真空恢复', 'gray', 0.3, '，等待下一次涨落'),
    ]

    y_positions = [3, 2.5, 2, 1.5, 1]

    for i, (text, color, alpha, note) in enumerate(time_steps):
        circle1 = plt.Circle((4.2, y_positions[i]), 0.15, color='red' if i in [1,2] else 'gray',
                             alpha=alpha if i in [1,2] else 0.5)
        circle2 = plt.Circle((5.8, y_positions[i]), 0.15, color='blue' if i in [1,2] else 'gray',
                             alpha=alpha if i in [1,2] else 0.5)

        if i in [1, 2]:
            # 画虚线表示虚对关联
            ax.plot([4.35, 5.65], [y_positions[i], y_positions[i]],
                   'g--', alpha=0.5, linewidth=1)

        ax.add_patch(circle1)
        ax.add_patch(circle2)

        ax.text(0.5, y_positions[i], text, fontsize=10, ha='left', va='center')
        ax.text(6.3, y_positions[i], note, fontsize=9, ha='left', va='center',
               style='italic', color='gray')

    # 底部说明
    explanation = """
    真空不是"空"的 —— 即使在绝对零度，系统也有零点能量 E₀ = ℏω/2

    海森堡不确定性原理允许虚粒子对在短时间内产生：
    ΔE · Δt ≥ ℏ/2  →  虚对寿命 Δt ~ ℏ/(2ΔE)

    这种涨落导致：
    • 真空中的电场涨落 ⟨0|E²|0⟩ ≠ 0
    • 卡西米尔效应（平行板间的吸引力）
    • 兰姆位移（Lamb shift）
    """
    ax.text(5, -0.5, explanation, fontsize=9, ha='center', va='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    output = output_path or get_output_path('vacuum_fluctuation')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"真空涨落可视化已保存: {output}")
    return output


def viz_rabi_oscillation(output_path: str = None, **params):
    """
    Rabi振荡可视化 - 原子在基态和激发态之间的概率振荡
    """
    g = params.get('g', 1.0)  # 耦合强度
    omega = params.get('omega', 0.0)  # 失谐量

    t = np.linspace(0, 10, 1000)

    # 计算Rabi振荡概率
    if omega == 0:  # 共振情况
        P1 = np.cos(g * t)**2  # 基态概率
        P2 = np.sin(g * t)**2  # 激发态概率
        title = '共振Rabi振荡 (δ=0, ΩR=2g)'
    else:  # 非共振情况
        Omega_eff = np.sqrt(4*g**2 + omega**2)
        P1 = (omega**2 + 4*g**2*np.cos(Omega_eff*t/2)**2) / Omega_eff**2
        P2 = (4*g**2*np.sin(Omega_eff*t/2)**2) / Omega_eff**2
        title = f'Rabi振荡 (δ={omega}, Ω={Omega_eff:.2f})'

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # 上图：概率随时间演化
    ax1.plot(t, P1, 'b-', linewidth=2, label='P₁(t) 基态 |1⟩')
    ax1.plot(t, P2, 'r-', linewidth=2, label='P₂(t) 激发态 |2⟩')
    ax1.fill_between(t, 0, P1, alpha=0.3, color='blue')
    ax1.fill_between(t, 0, P2, alpha=0.3, color='red')

    ax1.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax1.axhline(y=0, color='k', linewidth=0.5)
    ax1.axhline(y=1, color='k', linewidth=0.5)

    ax1.set_xlim(0, t[-1])
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_xlabel('时间 (单位: 1/g)', fontsize=12)
    ax1.set_ylabel('概率', fontsize=12)
    ax1.set_title(title, fontsize=14)
    ax1.legend(loc='center right')
    ax1.grid(True, alpha=0.3)

    # 添加注释
    ax1.annotate('完全转移\nP₂=1', xy=(np.pi/(2*g), 1), xytext=(np.pi/(2*g)+1, 0.7),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='red'))

    # 下图：光场与原子能级
    ax2.set_xlim(0, 12)
    ax2.set_ylim(-1, 4)

    # 原子能级
    ax2.axhline(y=0, color='blue', linewidth=3, label='基态 |1⟩ (E₁)')
    ax2.axhline(y=3, color='red', linewidth=3, label='激发态 |2⟩ (E₂=ℏω₀)')

    # 绘制光场（余弦波）
    t_light = np.linspace(0, 12, 200)
    E_field = 0.5 * np.cos(2*t_light) + 1.5
    ax2.plot(t_light, E_field, 'purple', alpha=0.5, linewidth=1, label='光场 E(t)')

    ax2.set_xlabel('时间', fontsize=12)
    ax2.set_ylabel('能量 / 场强', fontsize=12)
    ax2.set_title('二能级原子与光场相互作用', fontsize=14)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    # 标注
    ax2.annotate('吸收 (|1⟩+|γ⟩→|2⟩)', xy=(2.5, 1.5), xytext=(5, 1),
                fontsize=9, arrowprops=dict(arrowstyle='->', color='green'))
    ax2.annotate('发射 (|2⟩→|1⟩+|γ⟩)', xy=(7, 1.5), xytext=(8, 2.5),
                fontsize=9, arrowprops=dict(arrowstyle='->', color='green'))

    plt.tight_layout()

    output = output_path or get_output_path('rabi_oscillation')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Rabi振荡可视化已保存: {output}")
    return output


def viz_jaynes_cummings(output_path: str = None, **params):
    """
    Jaynes-Cummings模型能级图
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # 左图：裸原子能级 vs 腔场模
    ax1.set_xlim(-1, 8)
    ax1.set_ylim(-1, 12)

    # 原子能级
    ax1.axhline(y=0, color='blue', linewidth=4, label='原子基态 |1⟩')
    ax1.axhline(y=4, color='red', linewidth=4, label='原子激发态 |2⟩')

    # 光子数能级
    for n in range(1, 6):
        ax1.axhline(y=n*2 - 0.5, color='gray', linewidth=0.5, linestyle=':')
        ax1.text(-0.5, n*2 - 0.5, f'|{n}⟩', fontsize=10, va='center')

    ax1.set_xlabel('系统', fontsize=12)
    ax1.set_ylabel('能量 (ℏω 单位)', fontsize=12)
    ax1.set_title('分离的原子-光子系统', fontsize=14)
    ax1.legend(loc='upper right')
    ax1.set_yticks([])

    # 右图：JC模型能级劈裂
    ax2.set_xlim(-1, 8)
    ax2.set_ylim(-1, 12)

    # JC能级（未耦合）
    ax2.axhline(y=0, color='blue', linewidth=2, linestyle='--', alpha=0.5)
    ax2.axhline(y=4, color='red', linewidth=2, linestyle='--', alpha=0.5)

    # 相互作用导致的劈裂（真空Rabi劈裂）
    # |1,n⟩ 和 |2,n-1⟩ 之间的耦合
    n_show = [1, 2, 3, 4]
    colors = plt.cm.coolwarm(np.linspace(0, 1, len(n_show)))

    for i, n in enumerate(n_show):
        # 裸能级位置
        E_1n = (n-1) * 2  # |1,n⟩ 能量
        E_2n1 = 4 + (n-2) * 2  # |2,n-1⟩ 能量

        # 绘制未耦合能级（虚线）
        ax2.plot([1.5, 2.5], [E_1n, E_1n], 'b--', alpha=0.3, linewidth=1)
        ax2.plot([1.5, 2.5], [E_2n1, E_2n1], 'r--', alpha=0.3, linewidth=1)

        # 绘制耦合后的能级（实线）- 真空Rabi劈裂 2g√n
        if n >= 1:
            g_n = np.sqrt(n)  # g√n
            E_avg = (E_1n + E_2n1) / 2
            Delta = np.sqrt(4*g_n**2 + 0**2)  # 共振情况

            # 劈裂后的能级
            E_plus = E_avg + g_n
            E_minus = E_avg - g_n

            ax2.plot([3.5, 4.5], [E_minus, E_minus], '-', color=colors[i], linewidth=2)
            ax2.plot([3.5, 4.5], [E_plus, E_plus], '-', color=colors[i], linewidth=2)

            # 标注
            ax2.text(5, E_minus, f'|-,n={n}⟩', fontsize=9, va='center', color=colors[i])
            ax2.text(5, E_plus, f'|-,n={n}⟩', fontsize=9, va='center', color=colors[i])

            # 画箭头表示劈裂
            if i == 0:
                ax2.annotate('', xy=(4.7, E_plus), xytext=(4.7, E_minus),
                           arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
                ax2.text(4.9, (E_plus+E_minus)/2, 'ΩR', fontsize=10, color='purple')

    # 标注
    ax2.text(2, -0.5, '未耦合\n(原子+光子)', fontsize=10, ha='center', style='italic')
    ax2.text(4, -0.5, 'JC耦合\n(ℏg)', fontsize=10, ha='center', style='italic')

    ax2.axhline(y=0, color='blue', linewidth=3, label='|1,n⟩')
    ax2.axhline(y=4, color='red', linewidth=3, label='|2,n-1⟩')
    ax2.set_xlabel('')
    ax2.set_ylabel('能量', fontsize=12)
    ax2.set_title('Jaynes-Cummings模型：真空Rabi劈裂', fontsize=14)
    ax2.set_yticks([])

    plt.tight_layout()

    output = output_path or get_output_path('jaynes_cummings')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Jaynes-Cummings可视化已保存: {output}")
    return output


def viz_bell_state(output_path: str = None, **params):
    """
    Bell态与纠缠可视化
    """
    fig = plt.figure(figsize=(16, 12))

    # 上图：四个Bell态
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-2, 2)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('四个Bell态（最大纠缠态）', fontsize=14, fontweight='bold')

    states = [
        ('|Φ⁺⟩', '(|00⟩+|11⟩)/√2', 'blue'),
        ('|Φ⁻⟩', '(|00⟩-|11⟩)/√2', 'red'),
        ('|Ψ⁺⟩', '(|01⟩+|10⟩)/√2', 'green'),
        ('|Ψ⁻⟩', '(|01⟩-|10⟩)/√2', 'orange'),
    ]

    positions = [(-1, 1), (1, 1), (-1, -1), (1, -1)]

    for i, (name, formula, color) in enumerate(states):
        x, y = positions[i]
        ax1.text(x, y + 0.3, name, fontsize=18, ha='center', fontweight='bold', color=color)
        ax1.text(x, y - 0.3, formula, fontsize=11, ha='center')

        # Alice粒子
        circle_a = plt.Circle((x - 0.5, y), 0.25, fill=True, facecolor='lightblue',
                              edgecolor='blue', linewidth=2)
        ax1.add_patch(circle_a)
        ax1.text(x - 0.5, y - 0.6, 'A', fontsize=10, ha='center')

        # Bob粒子
        circle_b = plt.Circle((x + 0.5, y), 0.25, fill=True, facecolor='lightpink',
                              edgecolor='red', linewidth=2)
        ax1.add_patch(circle_b)
        ax1.text(x + 0.5, y - 0.6, 'B', fontsize=10, ha='center')

        # 纠缠线
        ax1.plot([x - 0.25, x + 0.25], [y, y], 'k-', linewidth=2)

    # 下左：EPR佯谬示意
    ax2 = fig.add_subplot(2, 2, 3)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 6)
    ax2.axis('off')
    ax2.set_title('EPR佯谬与"鬼魅超距作用"', fontsize=14, fontweight='bold')

    # 上海和纽约
    ax2.text(2, 5, '上海\nAlice', fontsize=12, ha='center', fontweight='bold')
    ax2.text(8, 5, '纽约\nBob', fontsize=12, ha='center', fontweight='bold')

    # 纠缠对
    ax2.add_patch(plt.Circle((2, 3.5), 0.3, color='purple', alpha=0.5))
    ax2.add_patch(plt.Circle((8, 3.5), 0.3, color='purple', alpha=0.5))
    ax2.plot([2.3, 7.7], [3.5, 3.5], 'purple', linewidth=2, linestyle='--')
    ax2.text(5, 3.8, '纠缠对', fontsize=10, ha='center', color='purple')

    # 测量
    ax2.annotate('', xy=(1.5, 2.5), xytext=(2.3, 3.2),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax2.text(1.2, 2.3, '测量: ↑\n结果: 随机', fontsize=9, ha='center')

    ax2.annotate('', xy=(8.5, 2.5), xytext=(7.7, 3.2),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax2.text(9, 2.3, '测量: →\n立刻知道\n上海结果!', fontsize=9, ha='center')

    # 说明文字
    explanation = """
    经典隐变量理论：测量结果在分离前就确定
    量子力学：测量结果在测量瞬间才"坍缩"
    实验（Aspect, 1982）：S=2.42 > 2，隐变量被否定！
    """
    ax2.text(5, 0.5, explanation, fontsize=9, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 下右：CHSH不等式
    ax3 = fig.add_subplot(2, 2, 4)
    ax3.set_xlim(-2, 2)
    ax3.set_ylim(-2, 2)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('CHSH不等式', fontsize=14, fontweight='bold')

    # 测量设置
    angles = {'a': 0, "a'": np.pi/4, 'b': np.pi/8, "b'": 3*np.pi/8}
    colors_angle = {'a': 'blue', "a'": 'green', 'b': 'red', "b'": 'orange'}

    for name, angle in angles.items():
        x = 1.5 * np.cos(angle)
        y = 1.5 * np.sin(angle)
        ax3.arrow(0, 0, x, y, head_width=0.1, head_length=0.05,
                 fc=colors_angle[name], ec=colors_angle[name], linewidth=2)
        ax3.text(x*1.2, y*1.2, name, fontsize=12, ha='center', va='center',
                color=colors_angle[name], fontweight='bold')

    ax3.text(0, -1.8, 'Alice测量方向: a, a\'\nBob测量方向: b, b\'', fontsize=10, ha='center')
    ax3.text(0, -2.5, 'CHSH: |S| ≤ 2 (隐变量)\n量子: |S| = 2√2 ≈ 2.83', fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()

    output = output_path or get_output_path('bell_state')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Bell态可视化已保存: {output}")
    return output


def viz_spdC(output_path: str = None, **params):
    """
    自发参量下转换(SPDC)可视化
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # 左图：SPDC过程示意
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('自发参量下转换 (SPDC)', fontsize=14, fontweight='bold')

    # 非线性晶体(BBO)
    crystal = FancyBboxPatch((4, 2.5), 2, 3, boxstyle="round,pad=0.1",
                             facecolor='lightyellow', edgecolor='orange', linewidth=3)
    ax1.add_patch(crystal)
    ax1.text(5, 4, 'BBO\n晶体', fontsize=12, ha='center', va='center')

    # 泵浦光
    ax1.annotate('', xy=(4, 4), xytext=(0, 4),
                arrowprops=dict(arrowstyle='->', color='blue', lw=3))
    ax1.text(1.5, 4.5, '泵浦光 ωₚ\n(高能量/蓝光)', fontsize=10, ha='center', color='blue')

    # 信号光和闲频光
    ax1.annotate('', xy=(9, 6), xytext=(6, 4),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax1.text(8, 6.5, '信号光 ωₛ', fontsize=10, ha='center', color='red')

    ax1.annotate('', xy=(9, 2), xytext=(6, 4),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax1.text(8, 1.5, '闲频光 ωᵢ', fontsize=10, ha='center', color='green')

    # 能量守恒标注
    conservation = """
    能量守恒: ℏωₚ = ℏωₛ + ℏωᵢ
    动量守恒(相位匹配): kₚ = kₛ + kᵢ
    """
    ax1.text(5, 0.5, conservation, fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 右图：类型I vs 类型II相位匹配
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('I型 vs II型相位匹配', fontsize=14, fontweight='bold')

    # I型
    ax2.text(2.5, 7, 'I型 SPDC', fontsize=12, ha='center', fontweight='bold')
    ax2.add_patch(plt.Circle((1.5, 5), 0.2, color='blue', alpha=0.8))
    ax2.add_patch(plt.Circle((3.5, 5), 0.2, color='blue', alpha=0.8))
    ax2.text(2.5, 4.5, 'o光 + o光 → e光', fontsize=9, ha='center')
    ax2.text(2.5, 4, '同偏振纠缠', fontsize=9, ha='center', style='italic')
    ax2.annotate('', xy=(1.5-0.5, 5-1), xytext=(1.5, 5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
    ax2.annotate('', xy=(3.5+0.5, 5-1), xytext=(3.5, 5),
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))

    # II型
    ax2.text(7.5, 7, 'II型 SPDC', fontsize=12, ha='center', fontweight='bold')
    ax2.add_patch(plt.Circle((6.5, 5.3), 0.2, color='blue', alpha=0.8))
    ax2.add_patch(plt.Circle((8.5, 4.7), 0.2, color='red', alpha=0.8))
    ax2.text(7.5, 4.5, 'o光 + e光 → e光+o光', fontsize=9, ha='center')
    ax2.text(7.5, 4, '正交偏振纠缠', fontsize=9, ha='center', style='italic')
    ax2.annotate('', xy=(6.5-0.5, 5.3-1), xytext=(6.5, 5.3),
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
    ax2.annotate('', xy=(8.5+0.5, 4.7-1), xytext=(8.5, 4.7),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

    # 纠缠标注
    ax2.text(5, 2, '纠缠光子对特性:', fontsize=11, ha='center', fontweight='bold')
    ax2.text(5, 1.3, '• 偏振纠缠\n• 能量-时间纠缠\n• 动量-空间纠缠', fontsize=9, ha='center')

    plt.tight_layout()

    output = output_path or get_output_path('spdc')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"SPDC可视化已保存: {output}")
    return output


def viz_bloch_sphere(output_path: str = None, **params):
    """
    Bloch球可视化 - 纯量子态的几何表示
    """
    fig = plt.figure(figsize=(14, 6))

    # 3D Bloch球
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')

    # Bloch球
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 25)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)), np.cos(v))

    ax1.plot_surface(x, y, z, color='lightblue', alpha=0.2, edgecolor='gray', linewidth=0.3)

    # 坐标轴
    ax1.plot([-1.5, 1.5], [0, 0], [0, 0], 'k-', linewidth=1)
    ax1.plot([0, 0], [-1.5, 1.5], [0, 0], 'k-', linewidth=1)
    ax1.plot([0, 0], [0, 0], [-1.5, 1.5], 'k-', linewidth=1)

    # 标注
    ax1.text(1.6, 0, 0, 'x', fontsize=12)
    ax1.text(0, 1.6, 0, 'y', fontsize=12)
    ax1.text(0, 0, 1.6, 'z', fontsize=12)
    ax1.text(0, 0, -1.6, '-z', fontsize=10)

    # 标记南北极
    ax1.scatter([0], [0], [1], color='red', s=100, marker='^', label='|0⟩ (激发态)')
    ax1.scatter([0], [0], [-1], color='blue', s=100, marker='v', label='|1⟩ (基态)')

    # 绘制一个示例态矢量
    theta = np.pi / 3  # 极角
    phi = np.pi / 4    # 方位角
    r = 0.95

    x_state = r * np.sin(theta) * np.cos(phi)
    y_state = r * np.sin(theta) * np.sin(phi)
    z_state = r * np.cos(theta)

    ax1.plot([0, x_state], [0, y_state], [0, z_state], 'r-', linewidth=3)
    ax1.scatter([x_state], [y_state], [z_state], color='red', s=150)

    ax1.text(x_state*1.2, y_state*1.2, z_state*1.2,
            f'|ψ⟩\nθ={theta:.2f}π\nφ={phi:.2f}π', fontsize=9, ha='center')

    ax1.set_title('Bloch球表示', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.set_xlim(-1.5, 1.5)
    ax1.set_ylim(-1.5, 1.5)
    ax1.set_zlim(-1.5, 1.5)

    # 右图：与球面点的对应关系
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-2, 2)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('态矢量的参数化', fontsize=14, fontweight='bold')

    # 圆表示赤道平面
    circle = plt.Circle((0, 0), 1, fill=False, color='gray', linewidth=1, linestyle='--')
    ax2.add_patch(circle)

    # 特殊态的位置
    states_pos = [
        ('|0⟩', 0, 1, 'red'),
        ('|1⟩', 0, -1, 'blue'),
        ('|±x⟩', 1, 0, 'green'),
        ('|±y⟩', 0.05, 0, 'purple'),
    ]

    for name, x, y, color in states_pos:
        ax2.scatter([x], [y], color=color, s=200, zorder=5)
        ax2.text(x*1.2, y*1.2, name, fontsize=11, ha='center', va='center', color=color)

    # 一般态
    theta_ex = np.pi / 3
    phi_ex = np.pi / 4
    x_ex = np.sin(theta_ex) * np.cos(phi_ex)
    y_ex = np.cos(theta_ex)

    ax2.scatter([x_ex], [y_ex], color='red', s=200, zorder=5, marker='*')
    ax2.plot([0, x_ex], [y_ex, y_ex], 'r--', alpha=0.5)
    ax2.plot([x_ex, x_ex], [0, y_ex], 'r--', alpha=0.5)

    ax2.text(x_ex*1.3, y_ex*1.3, f'|ψ⟩\nθ=π/3\nφ=π/4', fontsize=10, ha='center')

    ax2.text(0, 0, '+', fontsize=20, ha='center', va='center')
    ax2.set_title('赤道平面投影', fontsize=12)

    # 说明
    explanation = """
    一般纯态: |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩

    • Bloch球半径 = 1（纯态）
    • 混合态在球内部
    • 对径点代表正交态
    """
    ax2.text(0, -1.8, explanation, fontsize=9, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    output = output_path or get_output_path('bloch_sphere')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Bloch球可视化已保存: {output}")
    return output


def viz_photon_statistics(output_path: str = None, **params):
    """
    光子统计对比：泊松vs热光vs聚束vs反聚束
    """
    n = np.arange(0, 30)

    # 泊松分布（相干态）
    alpha_coh = 4
    P_poisson = np.exp(-alpha_coh**2) * (alpha_coh**(2*n)) / np.array([math.factorial(int(nn)) for nn in n])

    # 热光分布（热辐射）
    n_th = 2
    P_thermal = (1/(n_th+1))**1 * (1/(n_th+1))**n

    # Fock态 (n=4)
    P_fock = np.zeros_like(n, dtype=float)
    P_fock[4] = 1.0

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('光子统计对比', fontsize=16, fontweight='bold')

    # 泊松分布
    ax1 = axes[0, 0]
    ax1.bar(n, P_poisson, width=0.6, color='steelblue', alpha=0.8)
    ax1.set_xlabel('光子数 n')
    ax1.set_ylabel('P(n)')
    ax1.set_title(f'泊松统计（相干态 |α={alpha_coh}⟩）\nΔn/⟨n⟩ = 1/√⟨n⟩ = {1/np.sqrt(alpha_coh**2):.2f}')
    ax1.set_xlim(-1, 25)
    ax1.annotate(f'⟨n⟩={alpha_coh**2}\nσ={alpha_coh:.1f}', xy=(15, 0.15),
                fontsize=10, bbox=dict(boxstyle='round', facecolor='lightblue'))

    # 热光分布
    ax2 = axes[0, 1]
    ax2.bar(n, P_thermal, width=0.6, color='coral', alpha=0.8)
    ax2.set_xlabel('光子数 n')
    ax2.set_ylabel('P(n)')
    ax2.set_title(f'热光分布（黑体辐射）\n⟨n⟩ = {n_th}')
    ax2.set_xlim(-1, 25)
    ax2.annotate(f'⟨n⟩={n_th}\nσ²=⟨n⟩²+⟨n⟩', xy=(15, 0.15),
                fontsize=10, bbox=dict(boxstyle='round', facecolor='lightyellow'))

    # Fock态
    ax3 = axes[1, 0]
    ax3.bar(n, P_fock, width=0.6, color='green', alpha=0.8)
    ax3.set_xlabel('光子数 n')
    ax3.set_ylabel('P(n)')
    ax3.set_title('Fock态 |n⟩（光子数确定态）\nΔn = 0 (无涨落)')
    ax3.set_xlim(-1, 25)
    ax3.annotate('纯粒子性\n无统计涨落', xy=(15, 0.5),
                fontsize=10, bbox=dict(boxstyle='round', facecolor='lightgreen'))

    # 对比图
    ax4 = axes[1, 1]
    ax4.semilogy(n, P_poisson, 's-', label='泊松（相干态）', markersize=5)
    ax4.semilogy(n, P_thermal, 'o-', label='热光', markersize=5)
    ax4.semilogy(n, P_fock, '^-', label='Fock态', markersize=5)

    ax4.set_xlabel('光子数 n')
    ax4.set_ylabel('P(n) (对数)')
    ax4.set_title('光子统计对比（对数坐标）')
    ax4.legend()
    ax4.set_xlim(-1, 25)
    ax4.grid(True, alpha=0.3)

    # g²(0)值标注
    text = """
    二阶相干函数 g²(0):

    • 相干态: g²(0) = 1  (经典光)
    • 热光:    g²(0) = 2  (聚束)
    • Fock态:  g²(0) = 0  (反聚束)
    • 压缩态:  g²(0) > 2  (强聚束)
    """
    ax4.text(15, 0.01, text, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    output = output_path or get_output_path('photon_statistics')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"光子统计可视化已保存: {output}")
    return output


def viz_antibunching(output_path: str = None, **params):
    """
    Antibunching效应可视化 - HBT实验示意
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Antibunching效应与HBT实验', fontsize=16, fontweight='bold')

    # 左图：HBT实验装置
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 8)
    ax1.axis('off')

    # 单光子源
    source = FancyBboxPatch((0.5, 3), 1.5, 2, boxstyle="round,pad=0.1",
                            facecolor='lightyellow', edgecolor='orange', linewidth=2)
    ax1.add_patch(source)
    ax1.text(1.25, 4, '单光子\n源', fontsize=10, ha='center', va='center')

    # 分束器(50:50)
    ax1.plot([3, 5], [4, 6], 'k-', linewidth=2)
    ax1.plot([3, 5], [6, 4], 'k-', linewidth=2)
    ax1.text(4, 3.5, 'BS', fontsize=12, ha='center')

    # 光子路径
    ax1.annotate('', xy=(3, 4), xytext=(2, 4),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax1.annotate('', xy=(7, 6), xytext=(5, 6),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    ax1.annotate('', xy=(7, 4), xytext=(5, 4),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))

    # 两个探测器
    det1 = FancyBboxPatch((7, 5.5), 1.5, 1, boxstyle="round,pad=0.1",
                          facecolor='lightgreen', edgecolor='green', linewidth=2)
    ax1.add_patch(det1)
    ax1.text(7.75, 6, 'D1', fontsize=11, ha='center', va='center')

    det2 = FancyBboxPatch((7, 3.5), 1.5, 1, boxstyle="round,pad=0.1",
                          facecolor='lightgreen', edgecolor='green', linewidth=2)
    ax1.add_patch(det2)
    ax1.text(7.75, 4, 'D2', fontsize=11, ha='center', va='center')

    # 说明文字
    ax1.text(4, 1.5, 'Hanbury Brown-Twiss (HBT) 实验装置\n检测光子反聚束效应',
            fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 右图：二阶相关函数
    ax2 = axes[1]
    tau = np.linspace(-10, 10, 500)

    # 单光子源：antibunching g²(τ) → 0 for τ=0
    g2_single = 1 - 0.9 * np.exp(-np.abs(tau) / 1)

    # 热光源：bunching g²(0) = 2
    g2_thermal = 1 + 0.9 * np.exp(-np.abs(tau) / 1)

    # 相干光源：g²(τ) = 1
    g2_coherent = np.ones_like(tau)

    ax2.plot(tau, g2_single, 'b-', linewidth=2, label='单光子源 (antibunching)')
    ax2.plot(tau, g2_thermal, 'r-', linewidth=2, label='热光 (bunching)')
    ax2.plot(tau, g2_coherent, 'g--', linewidth=2, label='相干光')

    ax2.axhline(y=1, color='gray', linestyle=':', alpha=0.5)
    ax2.axhline(y=2, color='red', linestyle=':', alpha=0.3)
    ax2.axvline(x=0, color='gray', linestyle=':', alpha=0.5)

    # 标注antibunching
    ax2.annotate('g²(0)=0\n(单光子)', xy=(0, 0.1), xytext=(2, 0.3),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='blue'))
    ax2.annotate('g²(0)=2\n(热光聚束)', xy=(0, 1.9), xytext=(2, 1.7),
                fontsize=10, arrowprops=dict(arrowstyle='->', color='red'))

    ax2.set_xlabel('时间延迟 τ')
    ax2.set_ylabel('g²(τ)')
    ax2.set_title('二阶相干函数')
    ax2.legend(loc='upper right')
    ax2.set_xlim(-10, 10)
    ax2.set_ylim(-0.2, 2.5)
    ax2.grid(True, alpha=0.3)

    # 说明
    explanation = """
    Antibunching判据: g²(0) < g²(τ)

    • 单光子: g²(0) ≈ 0  (光子不会同时到达)
    • 热光:   g²(0) = 2  (光子倾向于同时到达)
    • 相干光: g²(0) = 1  (无关联，泊松统计)
    """
    ax2.text(-8, 0.5, explanation, fontsize=9,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

    plt.tight_layout()

    output = output_path or get_output_path('antibunching')
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Antibunching可视化已保存: {output}")
    return output


# 可视化函数映射表
VISUALIZATION_FUNCTIONS = {
    'fock_state': viz_fock_state,
    'coherent_state': viz_coherent_state,
    'squeezed_state': viz_squeezed_state,
    'vacuum_fluctuation': viz_vacuum_fluctuation,
    'rabi_oscillation': viz_rabi_oscillation,
    'jaynes_cummings': viz_jaynes_cummings,
    'bell_state': viz_bell_state,
    'spdc': viz_spdC,
    'bloch_sphere': viz_bloch_sphere,
    'photon_statistics': viz_photon_statistics,
    'antibunching': viz_antibunching,
}


def list_concepts():
    """列出所有可用的可视化概念"""
    print("\n可用可视化概念:")
    print("-" * 50)
    for name, func in VISUALIZATION_FUNCTIONS.items():
        doc = func.__doc__.split('\n')[0] if func.__doc__ else '无描述'
        print(f"  {name:25s} - {doc}")
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(
        description='量子光学可视化引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python viz_engine.py --concept fock_state
  python viz_engine.py --concept rabi_oscillation --params "g=1.0,omega=0"
  python viz_engine.py --concept spdc --output ./output.png
  python viz_engine.py --list  # 列出所有概念
        """
    )

    parser.add_argument('--concept', '-c', type=str,
                       help='可视化概念名称')
    parser.add_argument('--params', '-p', type=str,
                       help='参数字符串，如 "alpha=2,g=1.0"')
    parser.add_argument('--output', '-o', type=str,
                       help='输出文件路径')
    parser.add_argument('--list', '-l', action='store_true',
                       help='列出所有可用概念')
    parser.add_argument('--output-dir', '-d', type=str,
                       default=DEFAULT_OUTPUT,
                       help=f'输出目录 (默认: {DEFAULT_OUTPUT})')

    args = parser.parse_args()

    if args.list:
        list_concepts()
        return

    if not args.concept:
        parser.print_help()
        list_concepts()
        return

    # 解析参数
    params = {}
    if args.params:
        for pair in args.params.split(','):
            key, value = pair.split('=')
            # 尝试转换为数字
            try:
                value = float(value)
            except ValueError:
                pass
            params[key.strip()] = value

    # 执行可视化
    if args.concept not in VISUALIZATION_FUNCTIONS:
        print(f"错误: 未知概念 '{args.concept}'")
        list_concepts()
        sys.exit(1)

    func = VISUALIZATION_FUNCTIONS[args.concept]

    try:
        output_path = args.output if args.output else None
        result = func(output_path=output_path, **params)
        print(f"\n✓ 可视化完成: {result}")

        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(result):
            result_abs = os.path.abspath(result)
            print(f"  绝对路径: {result_abs}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
