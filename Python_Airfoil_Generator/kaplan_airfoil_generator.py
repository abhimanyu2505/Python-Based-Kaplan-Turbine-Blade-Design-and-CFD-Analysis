import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# =====================================================
# NACA 4-Digit Airfoil Generator
# =====================================================

def naca4(m, p, t, num_points=300):

    x = np.linspace(0, 1, num_points)

    yt = 5 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )

    yc = np.where(
        x < p,
        m / p**2 * (2 * p * x - x**2),
        m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * x - x**2)
    )

    dyc_dx = np.where(
        x < p,
        2 * m / p**2 * (p - x),
        2 * m / (1 - p)**2 * (p - x)
    )

    theta = np.arctan(dyc_dx)

    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)

    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    x_coords = np.concatenate([xu[::-1], xl[1:]])
    y_coords = np.concatenate([yu[::-1], yl[1:]])

    return x_coords, y_coords


# =====================================================
# USER INPUTS
# =====================================================

P = float(input("Power Output (kW): "))
H = float(input("Head Available (m): "))
eff = float(input("Overall Efficiency (decimal): "))
Z = int(input("Number of Blades: "))
attack = float(input("Optimum Angle of Attack (deg): "))

naca_number = input("Enter NACA 4-digit airfoil (e.g. 2412): ")

# Parse NACA

m = int(naca_number[0]) / 100
p = int(naca_number[1]) / 10
t = int(naca_number[2:]) / 100

# =====================================================
# TURBINE DESIGN CALCULATIONS
# =====================================================

density = 1000
bladesections = 5

Q = P * 1000 / (eff * density * 9.81 * H)

Ns = 885.5 / (H ** 0.25)

N = Ns * (H ** 1.25) / (P ** 0.5)

phi = 0.0242 * (Ns ** (2 / 3))

d_runner = 84.5 * phi * (H ** 0.5) / N

m_ratio = 0.4

d_hub = m_ratio * d_runner

flowarea = np.pi * (d_runner**2 - d_hub**2) / 4

V_f = Q / flowarea

d_avg = (d_runner + d_hub) / 2

V_avg = np.pi * d_avg * N / 60

V_w = P * 1000 / (density * Q * V_avg)

s = np.linspace(1.3, 0.75, bladesections)

# =====================================================
# GENERATE AIRFOIL SECTIONS
# =====================================================

x_base, y_base = naca4(m, p, t)

for i in range(bladesections):

    d = d_hub + (d_runner - d_hub) * i / (bladesections - 1)

    u = np.pi * d * N / 60

    beta_1 = np.degrees(np.arctan(V_f / (u - V_w)))

    beta_2 = np.degrees(np.arctan(V_f / u))

    t_spacing = np.pi * d / Z

    chord = s[i] * t_spacing

    theta_rot = 180 - beta_1 + attack

    # Scale Airfoil

    x = x_base * chord
    y = y_base * chord

    # Center Airfoil

    x = x - chord / 2

    # Rotate

    theta_rad = np.radians(theta_rot)

    R = np.array([
        [np.cos(theta_rad), np.sin(theta_rad)],
        [-np.sin(theta_rad), np.cos(theta_rad)]
    ])

    coords = np.vstack((x, y))

    rotated = R @ coords

    x_coord = rotated[0]
    y_coord = rotated[1]

    z_coord = np.ones_like(x_coord) * d / 2

    # Close Profile

    x_coord = np.append(x_coord, x_coord[0])
    y_coord = np.append(y_coord, y_coord[0])
    z_coord = np.append(z_coord, z_coord[0])

    # DXF Export

    doc = ezdxf.new()

    msp = doc.modelspace()

    points = list(zip(x_coord, y_coord))

    msp.add_lwpolyline(points)

    doc.saveas(f"section{i+1}.dxf")

    # Plot Section

    plt.figure(figsize=(6, 6))

    plt.plot(x_coord, y_coord)

    plt.gca().set_aspect("equal", adjustable="box")

    plt.grid(True)

    plt.title(f"Blade Section {i+1}")

    plt.savefig(f"section{i+1}.png", dpi=300)

    plt.close()

print("\nBlade sections generated successfully.")
print("DXF files exported for CAD modelling.")