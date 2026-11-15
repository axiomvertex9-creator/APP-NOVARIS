import math
import requests
import streamlit as st


# Dedicated Modal for Planetary & Celestial Mapping Terminal
@st.dialog("🌌 Deep Space & Celestial Cartography Terminal", width="large")
def show_planet_mapping_terminal():
    # --- Corrected Space-Themed Background CSS ---
    
    # --- Deep Space Mission Control Theme ---
    
    st.markdown(
    """
    <style>
    /* Dark space-themed dialog */
    div[data-testid="stDialog"] > div,
    div[role="dialog"] {
        background:
            radial-gradient(ellipse at top left,
                rgba(64, 35, 120, 0.30), transparent 55%),
            linear-gradient(145deg, #080d20, #030611 75%, #01030a)
            !important;
        color: #eaf2ff !important;
        border: 1px solid #344b7d !important;
        border-radius: 16px !important;
    }

    /* Force readable text throughout the dialog */
    div[data-testid="stDialog"] p,
    div[data-testid="stDialog"] span,
    div[data-testid="stDialog"] label,
    div[data-testid="stDialog"] h1,
    div[data-testid="stDialog"] h2,
    div[data-testid="stDialog"] h3,
    div[data-testid="stDialog"] h4,
    div[data-testid="stDialog"] li,
    div[data-testid="stDialog"] [data-testid="stMarkdownContainer"],
    div[role="dialog"] p,
    div[role="dialog"] span,
    div[role="dialog"] label {
        color: #eaf2ff !important;
    }

    /* Main dialog heading */
    div[data-testid="stDialog"] h2 {
        color: #73e8ff !important;
    }

    /* Captions */
    div[data-testid="stDialog"] [data-testid="stCaptionContainer"],
    div[data-testid="stDialog"] [data-testid="stCaptionContainer"] * {
        color: #a9bddf !important;
    }

    /* Dropdown input */
    div[data-testid="stDialog"] [data-baseweb="select"] > div {
        background-color: #101a32 !important;
        border-color: #405b91 !important;
    }

    div[data-testid="stDialog"] [data-baseweb="select"] * {
        color: #f0f6ff !important;
    }

    /* Dropdown popup */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] li {
        background-color: #0b1329 !important;
        color: #eaf2ff !important;
    }

    /* Buttons */
    div[data-testid="stDialog"] .stButton > button {
        background: linear-gradient(110deg, #17264b, #293b70)
            !important;
        color: #ffffff !important;
        border: 1px solid #547bc2 !important;
        border-radius: 9px !important;
    }

    div[data-testid="stDialog"] .stButton > button:hover {
        background: linear-gradient(110deg, #244d7e, #483778)
            !important;
        border-color: #73e8ff !important;
    }

    /* Metrics */
    div[data-testid="stDialog"] [data-testid="stMetric"] {
        background: #0d1730 !important;
        border: 1px solid #2d426d !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }

    div[data-testid="stDialog"] [data-testid="stMetricLabel"],
    div[data-testid="stDialog"] [data-testid="stMetricLabel"] * {
        color: #b3c5e8 !important;
    }

    div[data-testid="stDialog"] [data-testid="stMetricValue"],
    div[data-testid="stDialog"] [data-testid="stMetricValue"] * {
        color: #73e8ff !important;
    }

    /* Formula panel */
    .math-box {
        background: linear-gradient(135deg, #111b38, #070d1e);
        border: 1px solid #354b7a;
        border-left: 4px solid #73e8ff;
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0 15px;
    }

    .math-title {
        color: #73e8ff !important;
        font-weight: 700;
        font-size: 0.98rem;
        letter-spacing: 1px;
        font-family: monospace;
    }

    /* Dividers */
    div[data-testid="stDialog"] hr {
        border-color: #293b60 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )


    st.caption(
        "NOVARIS CELESTIAL DATABASE // Cartography, Coordinates & Astrophysical Mathematics"
    )

    # Celestial Object Database
    celestial_database = {
        # --- PLANETS ---
        "Mars (Planet)": {
            "type": "Terrestrial Planet",
            "radius": "3,389.5 km",
            "gravity": "3.72 m/s²",
            "day_length": "24h 39m (1 Sol)",
            "math_title": "Orbital Velocity & Escape Speed Formula",
            "latex_formula": r"v_{\text{orb}} = \sqrt{\frac{GM}{r}}, \quad v_{\text{esc}} = \sqrt{\frac{2GM}{r}}",
            "math_breakdown": "Where $G = 6.674 \times 10^{-11} \text{ m}^3\text{kg}^{-1}\text{s}^{-2}$, $M_{\text{Mars}} = 6.417 \times 10^{23} \text{ kg}$. Surface $v_{\text{esc}} \approx 5.03 \text{ km/s}$.",
            "landmarks": {
                "Olympus Mons": {
                    "type": "Shield Volcano (Highest peak in solar system)",
                    "coords": "18.65°N, 226.2°E",
                    "query": "Olympus Mons Mars",
                },
                "Valles Marineris": {
                    "type": "Vast Canyon System",
                    "coords": "14.0°S, 301.0°E",
                    "query": "Valles Marineris Mars",
                },
            },
        },
        "Jupiter (Planet)": {
            "type": "Gas Giant Planet",
            "radius": "69,911 km",
            "gravity": "24.79 m/s²",
            "day_length": "9h 56m",
            "math_title": "Kepler's Third Law (Harmonic Law)",
            "latex_formula": r"T^2 = \frac{4\pi^2}{GM} a^3",
            "math_breakdown": "Relates orbital period $T$ to semi-major axis $a$. For Jupiter ($M = 1.898 \times 10^{27} \text{ kg}$), orbital period $T \approx 11.86$ Earth years at $a = 5.20 \text{ AU}$.",
            "landmarks": {
                "Great Red Spot": {
                    "type": "Anticyclonic Storm",
                    "coords": "22°S, 290°W",
                    "query": "Jupiter Great Red Spot Hubble",
                },
                "North Temperate Belt": {
                    "type": "Cloud Jet Stream Band",
                    "coords": "30°N, 180°W",
                    "query": "Jupiter atmosphere clouds Juno",
                },
            },
        },
        "Saturn (Planet)": {
            "type": "Ringed Gas Giant",
            "radius": "58,232 km",
            "gravity": "10.44 m/s²",
            "day_length": "10h 42m",
            "math_title": "Roche Limit for Ring Stability",
            "latex_formula": r"d = r_m \left( 2 \cdot \frac{\rho_M}{\rho_m} \right)^{1/3}",
            "math_breakdown": "Minimum distance $d$ where tidal forces from primary mass $M$ would tear apart satellite $m$ with radius $r_m$. Saturn's main rings reside inside its fluid Roche limit ($d \approx 2.44 R_{\text{Saturn}}$).",
            "landmarks": {
                "North Pole Hexagon": {
                    "type": "Persistent Hexagonal Jet Stream",
                    "coords": "78.5°N, 0°W",
                    "query": "Saturn hexagon Cassini",
                },
                "B-Ring Plane": {
                    "type": "Dense Icy Particle Ring",
                    "coords": "Equatorial Plane",
                    "query": "Saturn B ring Cassini",
                },
            },
        },
        # --- MOONS & DWARF PLANETS ---
        "Europa (Moon of Jupiter)": {
            "type": "Icy Ocean Satellite",
            "radius": "1,560.8 km",
            "gravity": "1.315 m/s²",
            "day_length": "3.55 Earth Days",
            "math_title": "Tidal Heating & Dissipation Energy",
            "latex_formula": r"\dot{E} = \frac{21}{2} \frac{I_2}{Q} \frac{G M_J^2 R^5 e^2}{a^6}",
            "math_breakdown": "Orbital eccentricity $e = 0.009$ causes tidal flexing of Europa's interior, generating internal heat to maintain a subsurface liquid ocean beneath its ice crust.",
            "landmarks": {
                "Conamara Chaos": {
                    "type": "Disrupted Ice Sheet Region",
                    "coords": "9.7°N, 272.7°W",
                    "query": "Europa surface Conamara Chaos",
                },
                "Lineae Fractures": {
                    "type": "Global Linear Cracks",
                    "coords": "Global Grid",
                    "query": "Europa lines ice surface",
                },
            },
        },
        "Titan (Moon of Saturn)": {
            "type": "Atmospheric Ocean Satellite",
            "radius": "2,574.7 km",
            "gravity": "1.352 m/s²",
            "day_length": "15.95 Earth Days",
            "math_title": "Hydrostatic Scale Height Equation",
            "latex_formula": r"H = \frac{k_B T}{m g}",
            "math_breakdown": "Low surface gravity $g$ and cold nitrogen atmosphere ($T \approx 94 \text{ K}$) result in a high scale height $H \approx 40 \text{ km}$ (4x higher than Earth's atmosphere).",
            "landmarks": {
                "Kraken Mare": {
                    "type": "Liquid Methane/Ethane Sea",
                    "coords": "68.0°N, 310.0°W",
                    "query": "Titan Kraken Mare Cassini",
                },
                "Shangri-La Dunes": {
                    "type": "Hydrocarbon Dune Field",
                    "coords": "10.0°S, 165.0°W",
                    "query": "Titan surface dunes",
                },
            },
        },
        "Pluto (Dwarf Planet)": {
            "type": "Kuiper Belt Object",
            "radius": "1,188.3 km",
            "gravity": "0.62 m/s²",
            "day_length": "6.38 Earth Days",
            "math_title": "Gravitational Barycenter Coordinates",
            "latex_formula": r"R_{\text{bary}} = a \cdot \frac{m_2}{m_1 + m_2}",
            "math_breakdown": "Charon's high mass ratio ($m_{\text{Charon}} \approx 0.122 m_{\text{Pluto}}$) places the Pluto-Charon barycenter $R_{\text{bary}}$ outside Pluto's surface at $\approx 960 \text{ km}$ above its center.",
            "landmarks": {
                "Sputnik Planitia": {
                    "type": "Nitrogen Ice Glacier Basin",
                    "coords": "24.0°N, 175.0°E",
                    "query": "Pluto Sputnik Planitia New Horizons",
                },
                "Tombaugh Regio": {
                    "type": "Heart-Shaped Bright Region",
                    "coords": "19.5°N, 183.0°E",
                    "query": "Pluto Tombaugh Regio heart",
                },
            },
        },
        # --- DEEP SPACE & HEAVENLY BODIES ---
        "Orion Nebula (M42)": {
            "type": "Stellar Nursery Nebula",
            "radius": "12 Light Years",
            "gravity": "N/A (Interstellar Gas)",
            "day_length": "Distance: 1,344 Light Years",
            "math_title": "Jeans Instability Criterion (Star Formation)",
            "latex_formula": r"M_J = \left(\frac{5 k_B T}{G \mu m_H}\right)^{3/2} \left(\frac{3}{4\pi \rho}\right)^{1/2}",
            "math_breakdown": "Gas clouds exceed Jeans Mass $M_J$ when internal gas pressure can no longer balance self-gravitational collapse, triggering proto-star collapse.",
            "landmarks": {
                "Trapezium Cluster": {
                    "type": "Young O-type Star Cluster",
                    "coords": "RA 05h 35m, Dec -05° 23'",
                    "query": "Orion Nebula Trapezium cluster",
                },
                "Orion Molecular Cloud Complex": {
                    "type": "Active Star-Forming Gas Region",
                    "coords": "RA 05h 36m, Dec -05° 22'",
                    "query": "Orion Nebula Hubble image",
                },
            },
        },
        "Sagittarius A* (Black Hole)": {
            "type": "Supermassive Black Hole",
            "radius": "12 Million km (Event Horizon)",
            "gravity": "Infinite (at Singularity)",
            "day_length": "Mass: 4.15 Million M☉",
            "math_title": "Schwarzschild Event Horizon Radius",
            "latex_formula": r"r_s = \frac{2GM}{c^2}",
            "math_breakdown": "Where $c = 2.998 \times 10^8 \text{ m/s}$. For $M = 4.15 \times 10^6 M_{\odot}$, Schwarzschild radius $r_s \approx 1.2 \times 10^{10} \text{ m}$ ($\approx 0.08 \text{ AU}$).",
            "landmarks": {
                "Event Horizon Shadow": {
                    "type": "Photon Ring Geometry",
                    "coords": "Galactic Center (RA 17h 45m, Dec -29° 00')",
                    "query": "Sagittarius A Event Horizon Telescope",
                },
                "S2 Star Orbit": {
                    "type": "Relativistic Elliptical Star Path",
                    "coords": "Galactic Core Orbit",
                    "query": "Sagittarius A star orbits ESO",
                },
            },
        },
        "Andromeda Galaxy (M31)": {
            "type": "Spiral Galaxy",
            "radius": "110,000 Light Years",
            "gravity": "Mass: ~1.5 Trillion M☉",
            "day_length": "Distance: 2.5 Million Light Years",
            "math_title": "Cosmological Redshift & Doppler Velocity",
            "latex_formula": r"z = \frac{\lambda_{\text{obs}} - \lambda_{\text{emit}}}{\lambda_{\text{emit}}} \approx \frac{v}{c}",
            "math_breakdown": "Andromeda exhibits blueshift ($z \approx -0.001001$), moving toward the Milky Way at $v \approx 300 \text{ km/s}$; collision predicted in $\approx 4.5$ billion years.",
            "landmarks": {
                "Andromeda Nucleus": {
                    "type": "Supermassive Core & Double Nucleus",
                    "coords": "RA 00h 42m, Dec +41° 16'",
                    "query": "Andromeda Galaxy nucleus Hubble",
                },
                "Outer Spiral Arms": {
                    "type": "Interstellar Dust Lanes",
                    "coords": "Galactic Disk Plane",
                    "query": "Andromeda Galaxy spiral arms",
                },
            },
        },
    }

    # Selection Header
    target_name = st.selectbox(
        "Select Celestial Body / Heavenly Object for Cartography",
        list(celestial_database.keys()),
        key="selected_celestial_target",
    )

    current_body = celestial_database[target_name]

    st.divider()

    # Display Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Object Classification", current_body["type"])
    with col2:
        st.metric("Radius / Scale", current_body["radius"])
    with col3:
        st.metric("Gravity / Property", current_body["gravity"])

    # Mathematical Formula Box
    st.markdown("#### 📐 Astrophysical & Orbital Mathematics")
    st.markdown(
        f"""
        <div class="math-box">
            <div class="math-title">⚡ {current_body['math_title']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.latex(current_body["latex_formula"])
    st.caption(current_body["math_breakdown"])

    st.divider()

    # Landmark / Feature Mapper
    st.markdown("### 📍 Mapping Coordinates & Features")
    selected_landmark = st.selectbox(
        "Select Feature to Map", list(current_body["landmarks"].keys())
    )

    landmark_info = current_body["landmarks"][selected_landmark]

    c_info1, c_info2 = st.columns(2)
    with c_info1:
        st.info(
            f"**Feature Type:** {landmark_info['type']}\n\n**Coordinates / Location:** `{landmark_info['coords']}`"
        )
    with c_info2:
        if st.button("🛰️ Pull NASA Mapping Telemetry", key="fetch_map_data"):
            with st.spinner(f"Querying NASA logs for {selected_landmark}..."):
                try:
                    res = requests.get(
                        f"https://images-api.nasa.gov/search?q={landmark_info['query']}&media_type=image",
                        timeout=8,
                    )
                    if res.status_code == 200:
                        items = (
                            res.json()
                            .get("collection", {})
                            .get("items", [])
                        )
                        if items:
                            st.session_state.mapped_item = {
                                "title": items[0]["data"][0].get("title"),
                                "desc": items[0]["data"][0].get("description"),
                                "img": items[0]["links"][0]["href"],
                            }
                        else:
                            st.warning(
                                "No specific imagery entry found in NASA archive."
                            )
                except Exception as e:
                    st.error(f"Connection error: {e}")

    # Display fetched imagery
    if "mapped_item" in st.session_state and st.session_state.mapped_item:
        m_item = st.session_state.mapped_item
        st.markdown(f"**Archive Record:** {m_item['title']}")
        if m_item["img"]:
            st.image(m_item["img"], use_container_width=True)
        st.caption(m_item["desc"][:350] + "...")



    
def render_planet_codex():
    st.markdown(
        """
        <style>
        .st-key-clean_celestial_mapper_btn button {
            background: linear-gradient(
                110deg, #111a38, #29366d, #422b70
            ) !important;
            color: #a8f2ff !important;
            border: 1px solid #587bd0 !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 0 18px rgba(78, 137, 255, 0.18);
            transition: all 0.25s ease;
        }

        .st-key-clean_celestial_mapper_btn button:hover {
            background: linear-gradient(
                110deg, #204c7c, #374b92, #65439a
            ) !important;
            color: #ffffff !important;
            border-color: #76eaff !important;
            box-shadow: 0 0 25px rgba(72, 211, 255, 0.35);
            transform: translateY(-2px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🌌 Celestial Mapper",
                 key="clean_celestial_mapper_btn"):
        show_planet_mapping_terminal()

   