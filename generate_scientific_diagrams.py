#!/usr/bin/env python3
"""
Generate scientific diagrams for THz research
- THz-TDS System Diagram
- PCA THz Emitter Principle
- THz Communication 6G System
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle, FancyBboxPatch, Arc, Wedge
from matplotlib.lines import Line2D
import numpy as np
from matplotlib.collections import PatchCollection

# Set publication quality defaults
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.2

def draw_thz_tds_system():
    """Generate THz-TDS System Diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.set_aspect('equal')
    ax.axis('off')

    # White background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Helper functions
    def box(x, y, w, h, color='#f5f5f5', edgecolor='#333333', linewidth=1.5, label=None, label_size=9):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                               facecolor=color, edgecolor=edgecolor, linewidth=linewidth)
        ax.add_patch(rect)
        if label:
            ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                   fontsize=label_size, fontweight='bold', wrap=True)

    def arrow(x1, y1, x2, y2, color='black', linewidth=2, style='->', label=None, label_pos=0.5, linestyle='-'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle=style, color=color, lw=linewidth, linestyle=linestyle))
        if label:
            mid_x = x1 + (x2 - x1) * label_pos
            mid_y = y1 + (y2 - y1) * label_pos
            ax.text(mid_x, mid_y + 0.15, label, fontsize=8, ha='center', color=color)

    def line(x1, y1, x2, y2, color='black', linewidth=2, linestyle='-'):
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth, linestyle=linestyle)

    # Title
    ax.text(8, 8.5, 'THz-TDS System Diagram', fontsize=16, fontweight='bold', ha='center')

    # Ti:Sapphire Laser (source)
    box(0.3, 3.5, 1.4, 1.2, color='#ffe0e0', label='Ti:Sapphire\nLaser\n800nm, 100fs', label_size=8)

    # Beam Splitter
    box(2.2, 3.8, 0.8, 0.6, color='#e8e8e8', label='BS', label_size=10)

    # Pump arm components
    # Mechanical Chopper
    box(3.5, 2.0, 1.2, 0.8, color='#e0e8ff', label='Chopper', label_size=8)
    # Delay Stage
    box(5.2, 1.2, 1.6, 1.0, color='#e0ffe0', label='Delay Stage', label_size=8)

    # PCA Emitter (GaAs)
    box(5.2, 3.5, 1.4, 1.2, color='#fff0d0', label='PCA Emitter\n(GaAs)', label_size=8)

    # Parabolic Mirrors
    def draw_parabolic_mirror(x, y, label):
        # Draw mirror as a curved shape
        mirror = Arc((x, y), 0.6, 1.2, angle=0, theta1=0, theta2=180,
                    color='#333333', linewidth=2)
        ax.add_patch(mirror)
        ax.text(x, y - 0.5, label, fontsize=9, ha='center', fontweight='bold')

    draw_parabolic_mirror(7.3, 4.1, 'PM1')
    draw_parabolic_mirror(9.5, 4.1, 'PM2')

    # Sample position
    box(8.8, 3.5, 1.2, 1.0, color='#d0f0ff', label='Sample', label_size=9)

    # ZnTe Detector (EOS crystal)
    box(10.8, 3.5, 1.2, 1.0, color='#f0d0ff', label='ZnTe\nDetector', label_size=8)

    # Balanced Detector
    box(12.5, 3.8, 1.2, 0.6, color='#e8e8e8', label='Balance\nDetector', label_size=7)

    # Lock-in Amplifier
    box(14.0, 3.5, 1.4, 1.2, color='#e8e8e8', label='Lock-in\nAmplifier', label_size=7)

    # Computer/DAQ
    box(14.0, 1.5, 1.6, 1.0, color='#e8e8e8', label='Computer\n(DAQ)', label_size=8)

    # Probe arm (after beam splitter going up)
    box(2.2, 5.5, 1.0, 0.8, color='#d0ffd0', label='Probe', label_size=8)
    box(3.8, 5.5, 1.0, 0.8, color='#d0ffd0', label='Probe\nBeam', label_size=8)

    # Probe beam path to ZnTe
    line(4.8, 5.9, 10.0, 5.9, color='#00aa00', linewidth=1.5, linestyle='--')
    line(10.0, 5.9, 10.8, 4.5, color='#00aa00', linewidth=1.5, linestyle='--')

    # Draw beam paths with colors
    # Laser to BS
    arrow(1.7, 4.1, 2.2, 4.1, color='#cc0000', linewidth=2, label='Pump')

    # BS to PCA (reflected down)
    arrow(2.6, 3.8, 2.6, 3.2, color='#cc0000', linewidth=2)
    arrow(2.6, 3.2, 5.2, 3.2, color='#cc0000', linewidth=2)
    arrow(5.2, 3.2, 5.2, 3.5, color='#cc0000', linewidth=2)

    # PCA to PM1 (THz beam)
    arrow(6.6, 4.1, 7.0, 4.1, color='#0066cc', linewidth=2, label='THz')

    # PM1 reflects to sample
    arrow(7.6, 4.1, 8.0, 4.1, color='#0066cc', linewidth=2)

    # After sample to PM2
    arrow(9.0, 4.1, 9.2, 4.1, color='#0066cc', linewidth=2)
    arrow(9.8, 4.1, 10.2, 4.1, color='#0066cc', linewidth=2)

    # PM2 to ZnTe
    arrow(10.4, 4.1, 10.8, 4.1, color='#0066cc', linewidth=2)

    # Probe beam (green dashed) to ZnTe
    # ZnTe to Balance Detector
    arrow(12.0, 4.0, 12.5, 4.1, color='#0066cc', linewidth=2)

    # Balance to Lock-in
    arrow(13.7, 4.1, 14.0, 4.1, color='#333333', linewidth=1.5)

    # Lock-in to Computer
    arrow(14.7, 3.5, 14.7, 2.5, color='#333333', linewidth=1.5)
    arrow(14.7, 2.5, 14.8, 2.5, color='#333333', linewidth=1.5)

    # Chopper to Delay Stage
    arrow(4.7, 2.4, 5.2, 1.7, color='#666666', linewidth=1.5)

    # Delay Stage to PCA (optical trigger)
    arrow(6.0, 1.2, 5.5, 3.5, color='#cc0000', linewidth=1, linestyle=':')

    # Legend
    legend_elements = [
        Line2D([0], [0], color='#cc0000', linewidth=2, label='Pump (Red)'),
        Line2D([0], [0], color='#0066cc', linewidth=2, label='THz Beam (Blue)'),
        Line2D([0], [0], color='#00aa00', linewidth=1.5, linestyle='--', label='Probe (Green)'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

    plt.tight_layout()
    return fig

def draw_pca_emitter():
    """Generate PCA THz Emitter Principle diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Title
    ax.text(6, 7.5, 'PCA THz Emitter Principle', fontsize=16, fontweight='bold', ha='center')

    # GaAs Substrate
    substrate = FancyBboxPatch((1, 1), 10, 3, boxstyle="round,pad=0.05",
                                facecolor='#fff8dc', edgecolor='#8b7355', linewidth=2)
    ax.add_patch(substrate)
    ax.text(6, 2.5, 'GaAs Semiconductor Substrate', fontsize=11, ha='center', color='#5d4037')

    # Gold/Titanium dipole antenna electrodes
    # Left electrode
    left_electrode = Rectangle((1.5, 2.8), 0.15, 1.4, facecolor='#ffd700', edgecolor='#b8860b', linewidth=1.5)
    ax.add_patch(left_electrode)
    ax.text(1.58, 3.5, 'Au/Ti', fontsize=8, ha='center', va='center', rotation=90, color='#333')

    # Right electrode
    right_electrode = Rectangle((10.35, 2.8), 0.15, 1.4, facecolor='#ffd700', edgecolor='#b8860b', linewidth=1.5)
    ax.add_patch(right_electrode)
    ax.text(10.42, 3.5, 'Au/Ti', fontsize=8, ha='center', va='center', rotation=90, color='#333')

    # Antenna gap (center)
    ax.plot([1.65, 1.65], [2.8, 4.2], color='#333', linewidth=1)
    ax.plot([10.35, 10.35], [2.8, 4.2], color='#333', linewidth=1)

    # Bias voltage source
    ax.plot([0.3, 1.5], [4.5, 4.5], color='red', linewidth=2)
    ax.plot([0.3, 0.3], [4.2, 4.8], color='red', linewidth=2)
    ax.plot([1.5, 1.5], [4.2, 4.8], color='red', linewidth=2)
    ax.text(0.9, 4.8, 'V_bias', fontsize=10, ha='center', color='red')
    ax.text(0.9, 4.1, '-', fontsize=14, ha='center', color='red')
    ax.text(1.5, 4.1, '+', fontsize=14, ha='center', color='red')

    # Incident fs laser pulse
    ax.annotate('', xy=(6, 5.5), xytext=(2, 5.5),
               arrowprops=dict(arrowstyle='->', color='#cc0000', lw=2.5))
    ax.text(4, 5.8, 'fs Laser Pulse\n(800nm)', fontsize=10, ha='center', color='#cc0000', fontweight='bold')

    # Photo-generated carriers in gap (electron-hole pairs)
    for i, y in enumerate([3.0, 3.4, 3.8]):
        # Electron (negative)
        electron = Circle((5.5, y), 0.12, facecolor='blue', edgecolor='#000', linewidth=0.5)
        ax.add_patch(electron)
        ax.text(5.5, y - 0.25, 'e-', fontsize=8, ha='center', color='blue')

        # Hole (positive)
        hole = Circle((6.5, y), 0.12, facecolor='red', edgecolor='#000', linewidth=0.5)
        ax.add_patch(hole)
        ax.text(6.5, y - 0.25, 'h+', fontsize=8, ha='center', color='red')

    # Photocarrier current J arrow
    ax.annotate('', xy=(6, 3.5), xytext=(4.5, 3.5),
               arrowprops=dict(arrowstyle='->', color='#0000aa', lw=2))
    ax.text(5.25, 3.1, 'J', fontsize=11, ha='center', color='#0000aa', fontweight='bold')

    # THz radiation pattern (cone shape)
    theta = np.linspace(np.pi/6, 5*np.pi/6, 50)
    r = np.linspace(0, 2.5, 50)
    theta_grid, r_grid = np.meshgrid(theta, r)
    x = 6 + r_grid * np.cos(theta_grid)
    y = 3.5 + r_grid * np.sin(theta_grid)

    # Draw cone radiation pattern as lines
    for t in [np.pi/4, np.pi/2, 3*np.pi/4]:
        x_cone = 6 + np.linspace(0, 2.5, 50) * np.cos(t)
        y_cone = 3.5 + np.linspace(0, 2.5, 50) * np.sin(t)
        ax.plot(x_cone, y_cone, color='#0066cc', linewidth=1.5, alpha=0.7)

    # THz radiation label
    ax.annotate('', xy=(8.5, 5.5), xytext=(7.5, 4.5),
               arrowprops=dict(arrowstyle='->', color='#0066cc', lw=2))
    ax.text(8.8, 5.7, 'THz Radiation', fontsize=10, ha='center', color='#0066cc', fontweight='bold')

    # Formula annotation
    formula_box = FancyBboxPatch((8.5, 1.2), 3, 0.8, boxstyle="round,pad=0.05",
                                  facecolor='#f0f0f0', edgecolor='#333', linewidth=1.5)
    ax.add_patch(formula_box)
    ax.text(10, 1.6, r'$E_{THz} \propto \frac{d\mathbf{J}}{dt}$', fontsize=14, ha='center', va='center')

    # Gap label
    ax.text(6, 2.5, 'Gap\n(antenna feed)', fontsize=9, ha='center', va='center', style='italic')

    # Dipole antenna arms label
    ax.annotate('', xy=(1.65, 3.5), xytext=(0.8, 3.5),
               arrowprops=dict(arrowstyle='<->', color='#8b7355', lw=1.5))
    ax.text(0.5, 2.5, 'Dipole\nAntenna', fontsize=8, ha='center', va='center', color='#5d4037')

    plt.tight_layout()
    return fig

def draw_thz_communication():
    """Generate THz Communication 6G System diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Title
    ax.text(8, 8.5, 'THz Communication for 6G System', fontsize=16, fontweight='bold', ha='center')

    # Transmitter Chain
    tx_y = 5.5
    tx_start = 0.8

    # Data source
    box_tx(ax,0.5, tx_y - 0.4, 0.9, 0.8, '#e8e8e8', 'Data')
    # FEC
    box_tx(ax,1.7, tx_y - 0.4, 0.9, 0.8, '#d0e8d0', 'FEC')
    # Modulator
    box_tx(ax,2.9, tx_y - 0.4, 1.1, 0.8, '#d0d0e8', 'Modulator')
    # Upconversion
    box_tx(ax,4.3, tx_y - 0.4, 1.1, 0.8, '#e8d0d0', 'Upconversion')
    # PA
    box_tx(ax,5.7, tx_y - 0.4, 0.9, 0.8, '#e0e0d0', 'PA')
    # TX Antenna Array
    box_tx(ax,6.9, tx_y - 0.6, 1.3, 1.2, '#d0e0e8', 'TX\nAntenna\nArray')
    # Beamforming
    box_tx(ax,8.4, tx_y - 0.4, 1.0, 0.8, '#e8e0d0', 'Beam-\nforming')

    # Arrows in TX chain
    arrows_tx = [
        (1.4, tx_y, 1.7, tx_y),
        (2.6, tx_y, 2.9, tx_y),
        (4.0, tx_y, 4.3, tx_y),
        (5.4, tx_y, 5.7, tx_y),
        (6.6, tx_y, 6.9, tx_y),
        (8.2, tx_y, 8.4, tx_y),
    ]
    for x1, y1, x2, y2 in arrows_tx:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

    # THz Channel Box
    channel_box = FancyBboxPatch((9.5, 2.5), 2.5, 5, boxstyle="round,pad=0.1",
                                   facecolor='#f5f5ff', edgecolor='#333', linewidth=2)
    ax.add_patch(channel_box)
    ax.text(10.75, 7.2, 'THz Channel', fontsize=12, fontweight='bold', ha='center')

    # Frequency bands inside channel
    freq_bands = [
        ('W-band', '140 GHz', 6.8),
        ('D-band', '220 GHz', 5.8),
        ('H-band', '300 GHz', 4.8),
    ]
    for name, freq, y_pos in freq_bands:
        band_box = FancyBboxPatch((9.8, y_pos - 0.3), 1.9, 0.6, boxstyle="round,pad=0.02",
                                   facecolor='#e0e0ff', edgecolor='#666', linewidth=1)
        ax.add_patch(band_box)
        ax.text(10.75, y_pos, f'{name}\n{freq}', fontsize=9, ha='center', va='center', fontweight='bold')

    # Data rate indicator
    rate_box = FancyBboxPatch((9.8, 3.5), 1.9, 0.9, boxstyle="round,pad=0.02",
                               facecolor='#ffffd0', edgecolor='#996600', linewidth=1.5)
    ax.add_patch(rate_box)
    ax.text(10.75, 3.95, '100 Gbps\n- 1 Tbps', fontsize=10, ha='center', va='center', fontweight='bold', color='#996600')

    # Receiver Chain
    rx_y = 5.5
    rx_components = [
        (12.3, 'RX\nAntenna\nArray', '#d0e0e8'),
        (13.7, 'LNA', '#e0e0d0'),
        (15.0, 'Down-\nconversion', '#e8d0d0'),
    ]

    for i, (x, label, color) in enumerate(rx_components):
        box_tx(ax,x - 0.6, rx_y - 0.4, 1.1, 0.8, color, label)

    # Demodulator and FEC
    box_tx(ax,0.8, 2.0, 1.1, 0.8, '#d0d0e8', 'Demodulator')
    box_tx(ax,2.1, 2.0, 0.9, 0.8, '#d0e8d0', 'FEC')
    box_tx(ax,3.2, 2.0, 0.9, 0.8, '#e8e8e8', 'Data')

    # Arrows in RX chain (going right to left for visual flow, then down)
    arrows_rx = [
        (12.3, rx_y, 13.7, rx_y),
        (14.2, rx_y, 15.0, rx_y),
    ]
    for x1, y1, x2, y2 in arrows_rx:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

    # Channel to RX antenna
    ax.annotate('', xy=(12.3, rx_y), xytext=(12.0, 5.0),
               arrowprops=dict(arrowstyle='->', color='#0066cc', lw=2))

    # TX antenna to channel
    ax.annotate('', xy=(10.5, 5.0), xytext=(9.5, tx_y),
               arrowprops=dict(arrowstyle='->', color='#0066cc', lw=2))

    # RX output going down
    ax.annotate('', xy=(10.75, 2.8), xytext=(10.75, 5.0),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

    # RX chain arrows
    ax.annotate('', xy=(2.1, 2.4), xytext=(0.8, 2.4),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    ax.annotate('', xy=(3.2, 2.4), xytext=(2.1, 2.4),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

    # RX to Data output
    ax.annotate('', xy=(3.2, 2.4), xytext=(3.2, 2.0),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))

    # Labels for chains
    ax.text(4.5, 6.7, 'Transmitter Chain', fontsize=11, fontweight='bold', ha='center', color='#333')
    ax.text(4.5, 6.4, '(Digital to Analog)', fontsize=9, ha='center', color='#666')

    ax.text(4.5, 1.3, 'Receiver Chain', fontsize=11, fontweight='bold', ha='center', color='#333')
    ax.text(4.5, 1.0, '(Analog to Digital)', fontsize=9, ha='center', color='#666')

    plt.tight_layout()
    return fig

def box_tx(ax, x, y, w, h, color, label):
    """Draw a box on the TX/RX chain"""
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                          facecolor=color, edgecolor='#333', linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=8, fontweight='bold')

# Generate all three diagrams
if __name__ == '__main__':
    output_dir = r'z:\321\DHL\Self_Learning\Obsidian-Vault\6️⃣ 工具\visualizations'

    print("Generating THz-TDS System Diagram...")
    fig1 = draw_thz_tds_system()
    fig1.savefig(output_dir + '/THz_TDS_System.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig1)
    print("[OK] THz_TDS_System.png")

    print("Generating PCA THz Emitter Principle...")
    fig2 = draw_pca_emitter()
    fig2.savefig(output_dir + '/PCA_THz_Emitter_Principle.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig2)
    print("[OK] PCA_THz_Emitter_Principle.png")

    print("Generating THz Communication 6G System...")
    fig3 = draw_thz_communication()
    fig3.savefig(output_dir + '/THz_6G_Communication.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig3)
    print("[OK] THz_6G_Communication.png")

    print("\nAll diagrams generated successfully!")