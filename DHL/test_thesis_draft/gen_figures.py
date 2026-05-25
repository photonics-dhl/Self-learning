"""
生成博士论文配图 — 阿秒电子显微术
绪论和理论基础章节的示意图
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 200

out_dir = os.path.join(os.path.dirname(__file__), 'figures')


def gen_resolution_map():
    """图1-1: 超快测量技术的时间-空间分辨率对比"""
    fig, ax = plt.subplots(figsize=(10, 7))

    techniques = {
        '泵浦-探测 UEM': (100e-15, 1e-9),
        '阿秒光子条纹': (50e-18, 15e-9),
        'THz电子压缩': (1e-15, 1e-9),
        's-SNOM': (20e-15, 10e-9),
        'HHG-XUV': (43e-18, 15e-9),
        '光学泵浦-探测': (10e-15, 400e-9),
        '超快电子衍射': (200e-15, 0.1e-9),
    }

    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#95a5a6', '#1abc9c']

    for (name, (t, s)), c in zip(techniques.items(), colors):
        ax.scatter(t, s, s=150, c=c, zorder=5, label=name)
        ax.annotate(name, (t, s), textcoords="offset points",
                    xytext=(10, 5), fontsize=9)

    # 本工作
    ax.scatter(800e-18, 50e-9, s=400, c='red', marker='*', zorder=10,
               edgecolors='darkred', linewidths=1.5, label='本文工作')
    ax.annotate('本文工作', (800e-18, 50e-9), textcoords="offset points",
                xytext=(12, -10), fontsize=12, fontweight='bold', color='red')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('时间分辨率 (s)', fontsize=13)
    ax.set_ylabel('空间分辨率 (m)', fontsize=13)
    ax.set_title('超快测量技术的时间-空间分辨率对比', fontsize=14, fontweight='bold')

    ax.axvline(x=2.7e-15, color='gray', linestyle='--', alpha=0.5, label='光学周期 (800nm)')
    ax.axhline(y=400e-9, color='gray', linestyle=':', alpha=0.5, label='光学衍射极限 (800nm)')

    ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
    ax.set_xlim(10e-18, 1e-12)
    ax.set_ylim(1e-10, 1e-5)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ch1', 'fig_resolution_map.png'))
    plt.close()
    print('  -> fig_resolution_map.png')


def gen_framework():
    """图1-2: 研究框架图"""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # 理论基础
    box_style = dict(boxstyle="round,pad=0.4", facecolor='#3498db', alpha=0.8)
    ax.text(2, 5, '理论基础\n(第2章)', fontsize=12, ha='center', va='center',
            bbox=box_style, color='white', fontweight='bold')

    # 方法
    box_style2 = dict(boxstyle="round,pad=0.4", facecolor='#2ecc71', alpha=0.8)
    ax.text(6, 5, '阿秒电子脉冲\n产生与表征\n(第3章)', fontsize=11, ha='center', va='center',
            bbox=box_style2, color='white', fontweight='bold')

    # 三个结果
    boxes = [
        (2, 2, '针尖手性\n表面波\n(第4章)', '#e74c3c'),
        (6, 2, '介质共振器\n多极动力学\n(第5章)', '#f39c12'),
        (10, 2, '超原子\n对称性破缺\n(第6章)', '#9b59b6'),
    ]
    for x, y, txt, c in boxes:
        box_s = dict(boxstyle="round,pad=0.4", facecolor=c, alpha=0.8)
        ax.text(x, y, txt, fontsize=11, ha='center', va='center',
                bbox=box_s, color='white', fontweight='bold')

    # 总结
    box_style5 = dict(boxstyle="round,pad=0.4", facecolor='#34495e', alpha=0.8)
    ax.text(10, 5, '总结与展望\n(第7章)', fontsize=12, ha='center', va='center',
            bbox=box_style5, color='white', fontweight='bold')

    # 箭头
    arrow_props = dict(arrowstyle='->', lw=2, color='#2c3e50')
    ax.annotate('', xy=(4.5, 5), xytext=(3.5, 5), arrowprops=arrow_props)
    ax.annotate('', xy=(7.5, 5), xytext=(8.5, 5), arrowprops=arrow_props)

    for x in [2, 6, 10]:
        ax.annotate('', xy=(x, 3.2), xytext=(6, 4.2),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='#7f8c8d'))

    ax.set_title('本文研究框架', fontsize=14, fontweight='bold', pad=15)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ch1', 'fig_framework.png'))
    plt.close()
    print('  -> fig_framework.png')


def gen_talbot():
    """图2-1: 时间Talbot效应"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # (a) 能量侧带
    ax = axes[0]
    n_bands = np.arange(-8, 9)
    g = 3.0
    from scipy.special import jv
    amplitudes = [jv(n, 2*g) for n in n_bands]
    colors = plt.cm.RdBu_r(np.linspace(0.1, 0.9, len(n_bands)))
    ax.bar(n_bands, [a**2 for a in amplitudes], color=colors, edgecolor='gray', linewidth=0.5)
    ax.set_xlabel('侧带阶数 $n$')
    ax.set_ylabel('$|J_n(2|g|)|^2$')
    ax.set_title('(a) 能量侧带分布', fontweight='bold')
    ax.set_xlim(-9, 9)

    # (b) 脉冲压缩
    ax = axes[1]
    t = np.linspace(-3, 3, 1000)
    T = 1.0
    # 简化模型：多阶侧带干涉
    signal = np.zeros_like(t)
    for n in range(-8, 9):
        signal += amplitudes[n + 8] * np.cos(2 * np.pi * n * t / T)
    signal = signal**2
    signal /= signal.max()

    ax.plot(t, signal, 'b-', linewidth=1.5)
    ax.fill_between(t, signal, alpha=0.3, color='blue')
    ax.set_xlabel('时间 ($T$)')
    ax.set_ylabel('电子概率密度')
    ax.set_title('(b) 半Talbot距离处\n阿秒脉冲串', fontweight='bold')
    ax.set_xlim(-2, 2)

    # 标注脉冲宽度
    half_max = 0.5
    idx = np.where(signal[:len(signal)//2] > half_max)[0]
    if len(idx) > 0:
        pw = t[idx[-1]] - t[idx[0]]
        ax.annotate('', xy=(t[idx[0]], half_max), xytext=(t[idx[-1]], half_max),
                    arrowprops=dict(arrowstyle='<->', color='red', lw=2))
        ax.text(0, 0.55, f'$\\tau \\approx$ {pw:.3f} T\n$\\approx$ 800 as',
                ha='center', fontsize=10, color='red')

    # (c) 传播距离 vs 脉冲宽度
    ax = axes[2]
    z = np.linspace(0, 2, 500)
    # 简化模型
    tau = np.abs(np.sin(np.pi * z)) * 0.5 + 0.05
    tau[0] = 1.0
    ax.plot(z, tau, 'r-', linewidth=2)
    ax.axvline(x=0.5, color='green', linestyle='--', alpha=0.7, label='半Talbot距离')
    ax.axvline(x=1.0, color='blue', linestyle='--', alpha=0.7, label='Talbot距离')
    ax.set_xlabel('传播距离 ($z/z_T$)')
    ax.set_ylabel('归一化脉冲宽度')
    ax.set_title('(c) 脉冲宽度随传播\n距离的演化', fontweight='bold')
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.1)

    fig.suptitle('时间Talbot效应与阿秒脉冲形成', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ch2', 'fig_talbot.png'), bbox_inches='tight')
    plt.close()
    print('  -> fig_talbot.png')


def gen_hhg_model():
    """图2-2: 三步模型示意图"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # (a) 势垒倾斜
    ax = axes[0]
    x = np.linspace(-3, 5, 500)
    V0 = np.where(np.abs(x) < 1, -5, 0)
    V_tilt = -0.8 * x  # 激光场导致的倾斜
    ax.plot(x, V0, 'b-', linewidth=2, label='无激光场')
    ax.plot(x, V0 + V_tilt, 'r--', linewidth=2, label='有激光场')
    ax.fill_between(x, V0 + V_tilt, -8, alpha=0.1, color='blue')
    ax.annotate('隧道电离', xy=(1.2, -3.5), fontsize=11, color='red',
                arrowprops=dict(arrowstyle='->', color='red'),
                xytext=(2.5, -2))
    ax.set_xlabel('位置')
    ax.set_ylabel('势能')
    ax.set_title('(a) 隧道电离', fontweight='bold')
    ax.legend(fontsize=9)
    ax.set_ylim(-8, 2)

    # (b) 电子轨迹
    ax = axes[1]
    t = np.linspace(0, 1.5 * np.pi, 500)
    E_field = np.cos(t)
    # 经典轨迹
    for t0, c, lab in [(0.1, 'blue', '短轨道'), (1.2, 'red', '长轨道')]:
        dt = t - t0
        x_traj = dt - np.sin(dt) + np.sin(t0) - t0
        y_traj = -np.cos(dt) + np.cos(t0)
        mask = (y_traj >= 0) & (dt > 0)
        ax.plot(x_traj[mask], y_traj[mask], c=c, linewidth=2, label=lab)
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    ax.plot(0, 0, 'ko', markersize=10)
    ax.annotate('离子', xy=(0, 0), xytext=(-1, 0.5), fontsize=10)
    ax.set_xlabel('位移 (a.u.)')
    ax.set_ylabel('速度 (a.u.)')
    ax.set_title('(b) 电子轨迹', fontweight='bold')
    ax.legend(fontsize=9)

    # (c) HHG谱
    ax = axes[2]
    harmonics = np.arange(1, 40)
    # 三区结构
    intensity = np.zeros_like(harmonics, dtype=float)
    for i, h in enumerate(harmonics):
        if h < 5:
            intensity[i] = 1.0 / h**3
        elif h < 25:
            intensity[i] = 0.05 * (1 + 0.1 * np.random.randn())
        else:
            intensity[i] = 0.05 * np.exp(-(h - 25) / 2)

    ax.semilogy(harmonics, intensity, 'bo-', markersize=4, linewidth=1.5)
    ax.axvline(x=5, color='green', linestyle='--', alpha=0.7)
    ax.axvline(x=25, color='red', linestyle='--', alpha=0.7)
    ax.text(3, 0.1, '扰动区', fontsize=10, ha='center')
    ax.text(15, 0.15, '平台区', fontsize=10, ha='center', color='green')
    ax.text(28, 0.03, '截止区', fontsize=10, ha='center', color='red')
    ax.annotate('截止频率\n$I_p + 3.17 U_p$', xy=(25, 0.03), xytext=(30, 0.3),
                arrowprops=dict(arrowstyle='->', color='red'), fontsize=9, color='red')
    ax.set_xlabel('谐波阶数')
    ax.set_ylabel('强度 (arb. u.)')
    ax.set_title('(c) HHG谱', fontweight='bold')
    ax.set_ylim(1e-4, 10)

    fig.suptitle('高次谐波产生的三步模型', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ch2', 'fig_hhg_model.png'), bbox_inches='tight')
    plt.close()
    print('  -> fig_hhg_model.png')


def gen_pinem():
    """图2-3: PINEM原理"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # (a) 电子穿过近场
    ax = axes[0]
    theta = np.linspace(0, 2 * np.pi, 100)
    # 纳米结构
    rect = mpatches.Rectangle((-0.5, -0.3), 1, 0.6, linewidth=2,
                               edgecolor='blue', facecolor='lightblue', alpha=0.5)
    ax.add_patch(rect)
    # 近场等高线
    for r in [0.8, 1.2, 1.6]:
        x_ell = r * np.cos(theta)
        y_ell = r * 0.5 * np.sin(theta)
        ax.plot(x_ell, y_ell, 'r--', alpha=0.5, linewidth=1)
    # 电子轨迹
    ax.annotate('', xy=(0, 3), xytext=(0, -3),
                arrowprops=dict(arrowstyle='->', color='black', lw=2))
    ax.text(0.3, 2.5, '电子', fontsize=12)
    ax.text(0.7, 0.5, '近场', fontsize=10, color='red')
    ax.text(-0.2, -0.1, '纳米\n结构', fontsize=9, ha='center', color='blue')
    ax.set_xlim(-2, 2)
    ax.set_ylim(-3, 3)
    ax.set_aspect('equal')
    ax.set_title('(a) 电子穿越近场', fontweight='bold')
    ax.axis('off')

    # (b) 能量侧带
    ax = axes[1]
    n = np.arange(-5, 6)
    heights = np.exp(-np.abs(n) / 2.5)
    colors = ['red' if ni > 0 else ('blue' if ni < 0 else 'gray') for ni in n]
    ax.bar(n, heights, color=colors, edgecolor='gray', linewidth=0.5, alpha=0.7)
    ax.set_xlabel('光子数 $n$ ($\\Delta E = n\\hbar\\omega$)')
    ax.set_ylabel('概率')
    ax.set_title('(b) 能量侧带', fontweight='bold')
    ax.text(-4, 0.5, '损失\n光子', fontsize=9, color='blue', ha='center')
    ax.text(4, 0.5, '获得\n光子', fontsize=9, color='red', ha='center')
    ax.axhline(y=0, color='black', linewidth=0.5)

    # (c) 能量滤波成像
    ax = axes[2]
    # 简化的空间分布
    x = np.linspace(-5, 5, 200)
    field = np.exp(-x**2 / 2) * (1 + 0.3 * np.sin(2 * x))
    ax.plot(x, field, 'r-', linewidth=2, label='能量增益信号')
    ax.fill_between(x, field, alpha=0.2, color='red')

    # 标注能量滤波
    ax.axhline(y=0.3, color='green', linestyle='--', linewidth=1.5)
    ax.text(3.5, 0.35, '$E_{\\mathrm{cut}}$', fontsize=11, color='green')

    ax.set_xlabel('位置 (nm)')
    ax.set_ylabel('信号强度')
    ax.set_title('(c) 能量滤波成像', fontweight='bold')
    ax.legend(fontsize=9)

    fig.suptitle('光子诱导近场电子显微术 (PINEM) 原理', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, 'ch2', 'fig_pinem.png'), bbox_inches='tight')
    plt.close()
    print('  -> fig_pinem.png')


if __name__ == '__main__':
    print('生成博士论文配图...')
    os.makedirs(os.path.join(out_dir, 'ch1'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'ch2'), exist_ok=True)

    gen_resolution_map()
    gen_framework()
    gen_talbot()
    gen_hhg_model()
    gen_pinem()

    print('全部配图生成完毕。')
