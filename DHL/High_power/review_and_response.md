Response to Referee Report

Manuscript: "High-power continuous-wave optical waveguiding in a semiconductor nanowire"

Journal: Advanced Photonics Research

---

June 3, 2026

Dear Editor,

Thank you for forwarding the referee's comments on our manuscript. We have addressed each point below. In the revised manuscript, all changes are highlighted in red.

A version with revision marks is provided alongside the clean revised manuscript.

Sincerely yours,

Xin Guo, Associate Professor

Limin Tong, Professor

New Cornerstone Science Laboratory, State Key Laboratory of Extreme Photonics and Instrumentation, College of Optical Science and Engineering, Zhejiang University, Hangzhou 310027, China

---

**Referee's Comments and Our Responses**

---

1. In Figure 2c, the output power increases strictly linearly with input power up to 2.5 W of guided power, with no sign of thermal-induced deviation from linearity. For a subwavelength-diameter wire suspended in air, I would have expected some deviation at these power levels due to absorption-induced heating. What ensures thermal equilibrium across the entire tested range?

Response: This is a fair question. The linearity reflects a balance between heat generation and dissipation.

On the generation side, CdS at 1550 nm is far below its bandgap (~2.42 eV), and the residual absorption coefficient is extremely low. The heat generation rate therefore grows slowly with guided power. On the dissipation side, a 550-nm-diameter wire has a surface-to-volume ratio of ~4/d ≈ 7.3 μm⁻¹ — orders of magnitude larger than bulk geometries — which allows efficient heat transfer to the surrounding air.

The Varshni-effect measurement (Figure S4) gives a temperature of ~180 °C at 1.1 W guided power, well below the thermal damage threshold of CdS (>900 °C). At the maximum guided power of 2.5 W, the estimated temperature from linear extrapolation of the Varshni calibration remains within the safe operating range. The absence of hysteresis in the round-trip power sweeps (Figure S3) confirms that the thermal equilibrium is fully reversible.

We have added a discussion of this thermal balance in Section 2.2.

---

2. Figure 2c shows guided power reaching 2.5 W with strict linearity — the fiber-taper coupling performs impressively in power handling. The main text says little about what determines coupling efficiency: what roles do taper angle, overlap length, and effective index matching each play? Additionally, end-fire coupling at similar power levels often suffers from facet damage; does the evanescent coupling mechanism of the fiber taper offer an intrinsic advantage in high-power tolerance? A brief commentary comparing these schemes with end-fire coupling and free-space focusing would help readers understand the physical rationale behind this technical choice.

Response: Coupling efficiency is governed by three parameters. Taper angle: The taper angle determines adiabaticity (adiabaticity parameter). An excessively steep angle causes the fundamental fiber mode to leak into higher-order or radiation modes in the taper region, losing power before reaching the waist. The taper angle in our experiment is ~5°, which satisfies the adiabatic criterion — the energy remains almost entirely in the fundamental mode throughout the modal evolution. Overlap length: The parallel contact region between the taper waist and the nanowire defines the effective length of the evanescent coupling zone, which must exceed the coupling length $L_c = \pi/(\kappa_0 \Delta n_{\text{eff}})$ to achieve complete energy transfer. Effective index matching: The waist diameter must bring the effective index of the fiber mode close to that of the nanowire guided mode. In our experiment, a waist diameter of ~1–2 μm achieves good index matching with the CdS nanowire (550 nm diameter). Quantitative simulations of these parameters are provided in SI S2 and S3.

Compared with end-fire coupling, in the end-fire scheme focused light is incident on the nanowire end facet, where absorption produces localized heat accumulation — facet damage can occur at the hundred-mW level. Fiber-taper evanescent coupling avoids this problem: light is gradually transferred from the fiber fundamental mode into the nanowire guided mode over tens of microns of the taper region, with power density remaining below the material damage threshold throughout. The design principles of adiabatic fiber-to-chip coupling [Jin et al., Laser Photon. Rev. 17, 2200919 (2023)] apply equally here: the gradually varying modal overlap enables efficient energy transfer while avoiding concentrated absorption at an interface. Compared with free-space focusing, the latter is constrained by the diffraction limit — the focused spot size is ~λ, yielding a small mode overlap integral with a subwavelength-cross-section nanowire. The fiber taper, by contrast, adiabatically compresses the mode field to the subwavelength scale, providing a natural match to the nanowire guided mode.

We have added the physical basis of the coupling scheme and a qualitative comparison with end-fire coupling and free-space focusing in Section 2.1 of the revised manuscript.

---

3. The SHG and THG conversion efficiencies (6.9×10⁻⁶ and 6.4×10⁻⁸) are described as comparable to values obtained under pulsed excitation. I find this somewhat surprising — in pulsed excitation, the peak power density (typically ~GW/cm²) drives the nonlinear process, whereas CW operation would seem to lack this peak enhancement. What is the physical mechanism behind this comparability?

Response: The premise of the question — that CW power density is orders of magnitude below pulsed peak values — deserves a closer look. In our experiment, the guided power density at 1.1 W in a 550-nm-diameter CdS nanowire is 1.1×10¹³ W/m² (~1.1 GW/cm²). The peak power densities reported in the pulsed nanowire studies we cite are: ~1 GW/cm² for Ag-coated CdS nanowire SHG [36], ~10–100 GW/cm² for Si nanoplasmonic waveguide THG [37], and ~0.6–29 GW/cm² for GaAs nanowire SHG [38]. Our CW power density is within the same order of magnitude as refs. [36] and [38], and about one to two orders below ref. [37].

Nonlinear conversion efficiency scales with power density. Since the CW power density inside the nanowire overlaps with the range of peak power densities used in pulsed nanowire studies, the comparable efficiencies are not unexpected — they are a direct consequence of confining watt-level CW power into a subwavelength cross-section. The distinction is in the temporal nature of the output: CW operation provides a continuous, stable harmonic signal rather than the intermittent output of pulsed excitation.

The power-law slopes in the log-log plot (Figure 4d) — 1.97 ± 0.14 for SHG and 3.2 ± 0.18 for THG — match the expected quadratic and cubic dependencies, confirming that the nonlinear processes under CW excitation follow the same scaling laws as under pulsed excitation.

We have added this clarification to Section 2.4.

---

4. The conclusion states that the results "may push semiconductor nanowire photonics into the high-power regime and open new opportunities." The demonstrations are limited to CdS and ZnO at specific wavelengths. What constraints need to be met for extending this approach to other semiconductor nanowire materials?

Response: In the revised manuscript, we have rewritten the conclusion as follows:

"In summary, we have demonstrated high-power CW optical waveguiding in CdS and ZnO nanowires. A single 550-nm-diameter CdS nanowire safely waveguides 1550-nm CW light with power up to 2.5 W, nearly four orders of magnitude higher than previously reported results; a 690-nm-diameter ZnO nanowire supports guided powers of 292 mW at 1550 nm and 33 mW at 532 nm. These results were enabled by low-defect nanowires and efficient fiber-taper evanescent coupling. Building on this high-power platform, we further realized intermodal-phase-matched CW second- and third-harmonic generation with efficiencies comparable to pulsed excitation. While the current demonstrations are limited to CdS and ZnO at specific wavelengths, the fiber-taper coupling approach is in principle applicable to other semiconductor nanowire materials, provided that three conditions are met: low defect density, operation in a weak-absorption spectral window, and effective index matching for efficient coupling. Extending this approach to a broader range of materials and wavelengths may find applications in nonlinear optics, sensing, and integrated photonic systems."

---

**Minor Comments**

---

5. The Varshni fitting parameters in Equation (3) (α = 0.00059, β = 33.5) are given without units.

Response: We have added the units: α = 5.9×10⁻⁴ eV/K, β = 33.5 K, and a₀ = 2.459 eV.

---

6. The Supporting Information is referenced via figure citations (e.g., Figure S2), but including the corresponding section numbers (S1–S5) would make it easier for readers to locate the relevant content.

Response: We have updated the cross-references to include section numbers: surface roughness measurement (see SI S1), coupling efficiency simulation and waveguiding power calculation (see SI S2 and S3), temperature evaluation via the Varshni effect (see SI S4), and mode analysis (see SI S5).

---

**List of Changes in the Revised Manuscript**

Main text:

1. Section 2.2: added discussion of thermal balance underlying the linear Pout–Pin relationship.
2. Section 2.1: added physical basis for the fiber-taper coupling scheme — adiabatic taper angle condition, coupling length criterion, effective index matching — and comparison with end-fire coupling and free-space focusing.
3. Section 2.4: added quantitative comparison of CW power density (~1.1 GW/cm²) with pulsed peak power densities from refs. [36–38] (~0.6–100 GW/cm²), explaining the comparable nonlinear conversion efficiencies.
4. Conclusion revised to acknowledge material- and wavelength-specific conditions, with three requirements for extending the approach.
5. Varshni parameters in Equation (3): units added (α = 5.9×10⁻⁴ eV/K, β = 33.5 K, a₀ = 2.459 eV).
6. Cross-references to SI sections S1–S5 added in the main text.
