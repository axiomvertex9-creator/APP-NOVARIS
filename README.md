# 🚀 NOVARIS

**An interactive space-training dashboard built to train junior astronauts.**

Built for the **NASA Space Apps Challenge**.

---

## 🔗 Live App

> **Streamlit link:** `PASTE YOUR STREAMLIT LINK HERE`



---

## 📝 About the Project

NOVARIS is a learning platform for young people who dream of becoming astronauts. Instead of just reading about space, trainees explore it: they sign up as cadets, watch their own rocket launch, fly to planets, stars and black holes, step out on a spacewalk, and practise real-world skills through simulators.

**Target audience:** junior astronauts and students curious about space.

**Our goal:** make space science, spacecraft engineering and mission planning feel hands-on, visual and fun.

*(Write more about your idea, the problem you solve and your challenge here.)*

---

## ✨ Features

| Section | What it does |
|---|---|
| **Cinematic intro** | Animated opening sequence when the app starts |
| **Sign Up** | Cadets register (email form) and see a personalised rocket launch with their name, a live countdown, flight data and a downloadable registration form |
| **Planet Explorer** | Interactive map of the Solar System and deep space (stars and black holes). Hover for facts, click to fly there |
| **Space Travel** | Pick any destination, take a countdown-to-warp flight, then step out for a first-person spacewalk or surface walk |
| **Space Crafts** | Learn about famous missions such as Voyager 1, James Webb Space Telescope and Chandrayaan-3 |
| **Customization** | Change colours and dashboard title; your look is saved for next time |
| **Experimental Etudes** | Hands-on experiments and exercises |
| **Astronaut Simulation** | Astronaut training simulation |
| **Orbital Foundry** | Build and explore orbital concepts |
| **Mini Flight Simulator** | Practise flying a spacecraft |
| **Space Engineering and Flight** | Spacecraft and flight engineering simulator |
| **Radio Control and Planning** | Mission planning and communications practice |
| **Initiate Exopolis** | Space-colony / habitat experience |
| **Academy Lite** | A lighter version of the training academy |
| **Orion widget and Planet Codex** | Helper assistant and planet reference |
| **NOVARIS Game** | 3D "Astra Nexus Academy" game, started from the home-page button (**runs on a local Windows PC only**) |

---

## 🧰 Built With

- [Python](https://www.python.org/) and [Streamlit](https://streamlit.io/)
- HTML, CSS and JavaScript (Canvas, Web Audio) embedded in Streamlit
- Three.js-style 3D game assets (`.glb` models) for the academy game



---

## ▶️ How to Run Locally

1. Install Python 3.10 or newer.
2. Install the requirements:
   ```bash
   pip install streamlit
   ```
3. Keep all project files and folders together (see below).
4. Start the app:
   ```bash
   streamlit run dontask6.py
   ```
5. Open the link Streamlit prints (usually `http://localhost:8501`).

An internet connection is needed for fonts and the images on the Space Crafts page.

### 🎮 Running the game (Windows PC only)

Put the game files in a folder named `game files` next to the main Python file. On the home page, click **START NOVARIS GAME**. It starts a small local server and opens the game inside the page. The game does not run on Streamlit Cloud, which uses Linux.

---

## 📁 Project Structure

```
random_things/
├── APP_NOVARIS.py              # main Streamlit app
├── orion_widget.py          # Orion helper widget
├── planet_codex.py          # planet reference
├── novaris_intro/           # animated intro component
├── game files/              # NOVARIS 3D game (local only)
├── etude.html
├── astronaut sim.html
├── Orbital Foundry.html
├── orion-flight-sim.html
├── flight sim.html
├── mission.html
├── expolis.html
├── academy.html
├── users.json               # sign-up data (created automatically)
└── prefs.json               # saved looks and click data (created automatically)
```

---

## ⚠️ Known Limitations

- The NOVARIS game only runs on a local Windows PC.
- "Register with Gmail" is still under development; email sign-up works.
- Planet sizes and distances in the explorer are not to scale, and figures are approximate.

---

TEAM:
UJAAN GHOSH- (Team leader) Web animation
SUPRABHO MUKHERJEE- Webpage and backend
SHASHANK SRIVASTAVA- Game

---

## 🙏 Acknowledgements

- NASA Space Apps Challenge
- NASA and ISRO public mission information


---

