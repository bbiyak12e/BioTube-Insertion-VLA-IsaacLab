# BioTube-Insertion-VLA-IsaacLab

### Can a 30 mm tube go into a 31 mm hole? — Sim-to-Real VLA for precision insertion of bio-lab tubes (Franka FR3 · FAIRINO FR5, Isaac Sim / Isaac Lab)

[한국어](README.md) · [Contents](#contents) · Equation notes: [docs/math_en.md](docs/math_en.md) · Official write-up: [BioRoboticsIsaacSim / sim_isaac_tube](https://github.com/SungjinDavidLee/BioRoboticsIsaacSim/tree/main/sim_isaac_tube) · Dropper · beaker experiments on the same workcells: [BioRoboticsIsaacSim](https://github.com/SungjinDavidLee/BioRoboticsIsaacSim)

![GR00T N1.7 retrained with DAgger inserting on its own — FR3 (left) · FR5 (right), third-person camera, 4× speed](figures/demo_pair_dagger_third_4x.gif)

**GR00T N1.7 retrained with DAgger picks and inserts on its own (policy only)** — one bench scene not used in training (random layout, scene 1; both robots get the same layout and lighting), FR3 on the left · FR5 on the right, third-person camera, 4× speed. The models before DAgger failed this scene on both robots. 1× video (third-person · wrist): [demo_pair_dagger_1x.mp4](figures/demo_pair_dagger_1x.mp4) · first scripted demos (Nov 2): [demo_pair_third_4x.gif](figures/demo_pair_third_4x.gif)

> **Latest news**
> - 2026-11-20 · Front page rewritten with the Nov 19 results — policy-only video after DAgger · pipeline figure · per-robot differences (real-matched values) · results. The tube folder in the lab repository is now `sim_isaac_tube` (dropper · beaker experiments are in the folders next to it)
> - 2026-11-20 · Progress-log reports [5](docs/report05_main_bench_stop/README_EN.md) · [6](docs/report06_improve_1112_1113/README_EN.md) · [7](docs/report07_sim2real_1000/README_EN.md) · [8](docs/report08_dagger_1114_1116/README_EN.md) · [9](docs/report09_final_1116_1119/README_EN.md) (Nov 10 – Nov 19) — final numbers in [Section 11, Results](#11-results)
> - 2026-11-16 · [Report 4 — Sim benchmark results: VLA only · DAgger · VLA + formula](docs/report04_sim_bench/README_EN.md) ([FR5](docs/report04_sim_bench/fr5/README_EN.md) · [FR3](docs/report04_sim_bench/fr3/README_EN.md))

<details>
<summary>Earlier news (Nov 2 – Nov 10)</summary>

- 2026-11-10 · [Report 3 — Paired demos re-collected with real-matched settings](docs/report03_realmatched_data/README_EN.md)
- 2026-11-06 · [Report 2 — GR00T trained on 100 demos](docs/report02_vla100_bench/README_EN.md) · development log [docs/12](docs/12-자동수집기.md) updated (Korean)
- 2026-11-04 · Fine-tuned GR00T N1.7 (100 demos each for FR3 · FR5) · benchmark on 50 unseen scenes
- 2026-11-03 · Added [Real setup → digital twin](docs/real_to_twin/README_EN.md) · FR3 finished collecting 100 demonstrations
- 2026-11-02 · Started automatic collection of 100 FR3 · FR5 paired demonstrations · GR00T N1.7 installed · added review video · motion-jump check tools

</details>

---

## Contents

1. **Overview · task · pipeline** — [1](#1-overview) · [2](#2-task) · [3](#3-overall-pipeline)
2. **[Real setup → digital twin](docs/real_to_twin/README_EN.md)** — from measurements to shapes, image regions (segments), camera fitting, comparison with colour segments · summary in [4](#4-digital-twin-isaac-sim) · [per-robot differences](#per-robot-differences)
3. **Domain randomization (Isaac Lab)** — [5](#5-domain-randomization-isaac-lab)
4. **Scripted demo collector (BioTube-AutoDemo-IsaacLab)** — [6](#6-biotube-autodemo-isaaclab--scripted-demo-collector) · detailed development notes (Korean) [docs/12-자동수집기.md](docs/12-자동수집기.md)
5. **Equations** — summary [7](#7-equations-summary) · full notes [docs/math_en.md](docs/math_en.md) ([digital twin](docs/math_en.md#4-equations-and-application--digital-twin) · [domain randomization](docs/math_en.md#5-equations-and-application--domain-randomization) · [scripted demos](docs/math_en.md#6-equations-and-application--scripted-demo-generation-and-success-check))
6. **Data quality tools · dataset** — [8](#8-data-quality-tools) · [9](#9-dataset)
7. **GR00T · results · roadmap** — [10](#10-vla--gr00t-n17) · [11](#11-results) · [12](#12-roadmap) · reports [2](docs/report02_vla100_bench/README_EN.md) · [3](docs/report03_realmatched_data/README_EN.md) · **[4 — sim benchmark results](docs/report04_sim_bench/README_EN.md)** · progress logs [5](docs/report05_main_bench_stop/README_EN.md) · [6](docs/report06_improve_1112_1113/README_EN.md) · [7](docs/report07_sim2real_1000/README_EN.md) · [8](docs/report08_dagger_1114_1116/README_EN.md) · [9](docs/report09_final_1116_1119/README_EN.md)
8. **How to run · folders** — [13](#13-how-to-run) · [14](#14-folder-structure-and-environment)
9. **🍪 How we got here** — [at the bottom](#the-task-changed-three-times)

Official write-up (lab repository): [BioRoboticsIsaacSim / sim_isaac_tube](https://github.com/SungjinDavidLee/BioRoboticsIsaacSim/tree/main/sim_isaac_tube) · The dropper and beaker-pouring experiments on the same real-matched workcells are also in the lab repository [BioRoboticsIsaacSim](https://github.com/SungjinDavidLee/BioRoboticsIsaacSim).

## 1. Overview

In a bio lab, inserting a centrifuge tube into a rack is a precision manipulation with only 1 mm of clearance. This repo contains the full simulation-side pipeline for performing this manipulation with a VLA (Vision-Language-Action) model.

1. Measure the real workcells (FR3 · FR5) and build a **digital twin** in Isaac Sim,
2. **randomize the scenes** in Isaac Lab,
3. collect paired data for both robots with a scripted demo collector (**BioTube-AutoDemo-IsaacLab**) that **generates, checks, and saves demonstrations on its own** via path planning, and then
4. **post-train GR00T N1.7** on that data and transfer it to the real robots — that is the goal.

## 2. Task

| Item | Description |
|---|---|
| Instruction | `put the red tube in the red slot` |
| Scene | Source rack (red-water and yellow-water tubes in the two end holes) + empty rack (red ring on one hole) |
| Success | At the hole-collar height (51 mm above the rack bottom), the tube axis passes **within 2 mm** of the hole center, the tube reaches the bottom, and the tilt is **within 12°**. The yellow tube and the ring stay in place |
| Difficulty | Tube 30 mm · hole 31 mm → 1 mm clearance. The bottom is a hemisphere (radius 15 mm), so even a slight misalignment tilts the tube and it catches on the collar |
| Randomized per scene | Position · orientation of both racks, red/yellow left-right order, red-ring hole (red slot; one of 4), lighting brightness · color |

![The same scene in the real-matched sim — start (left) · insertion (right), top FR3 · bottom FR5](figures/scene_pair_v2.jpg)

The same scene in the real-matched sim (from Nov 13) — start on the left, insertion on the right, FR3 on top · FR5 below. The scene with the first setup (Nov 2): [scene_pair.png](figures/scene_pair.png)

## 3. Overall pipeline

![Pipeline and progress (2026-11-20)](figures/pipeline_v2_en.png)

Green stages are done, blue is the DAgger loop, gray is planned (2026-11-20). Reports by stage: real-format conversion [3](docs/report03_realmatched_data/README_EN.md) → real-matched sim and 1,000 demos per robot [7](docs/report07_sim2real_1000/README_EN.md) → VLA + formula and DAgger [4](docs/report04_sim_bench/README_EN.md) · [8](docs/report08_dagger_1114_1116/README_EN.md) · [9](docs/report09_final_1116_1119/README_EN.md); what is left is in the [roadmap (12)](#12-roadmap).

## 4. Digital twin (Isaac Sim)

![Digital twin pipeline](figures/pipeline_twin_en.png)

- **Measured assets:** the tube (length 108 mm, body 30 mm, cap 33×13 mm, hemispherical bottom R 15 mm) and the 4-hole rack (165×40×51 mm, hole pitch 37 mm) were measured with calipers, built with Blender scripts, and converted to USD with physics attached (rigid body · mass · collision · friction). The red ring is an STL of the real part (inner 34 · outer 41 · height 5 mm)
- **Colored-water tubes:** translucent body + 48 mL of water. Water height · mass · center of mass computed from the volume equation (51 g)
- **Camera fitting:** the positions · angles of the third-person · wrist cameras are determined by least-squares minimization of the reprojection error between points in the real images and the 3D positions of the same points (third-person error 2–4 px)
- **Start pose:** joint values set by solving inverse kinematics for the hand position estimated from the image
- **Two workcells:** the FR3 and FR5 workcells are reproduced separately, and the TCPs of both robots use the same definition (rubber pad contact surface − 7.12 mm)
- **Comparison with the real setup:** object position (px) · overlap (IoU) · color difference (ΔE) · brightness are measured numerically

### Per-robot differences

The scene, pipeline, and success check are the same for both robots; only the following differ. Values are for the **real-matched sim used now (from Nov 13)** ([Report 7](docs/report07_sim2real_1000/README_EN.md), Sections 2 · 4).

| Item | FR3 | FR5 |
|---|---|---|
| Robot · gripper | Franka Research 3 · Franka Hand (parallel, 40 mm per side) | FAIRINO FR5 · DH-Robotics AG-95 (47.5 mm per side) |
| Arm joints | 7 | 6 |
| TCP (sim) | Flange + 97.0 mm | Flange + 171.2 mm (both: pad contact surface − 7.12 mm) |
| Third-person camera | (1.060, −0.028, 0.527) m in the base frame · pitch −30.6° · FOV 88.7° — solved from the robot PC's camera calibration, 0.52 px mean against the real model | Settings matched by the real team (camera height, etc.) |
| Wrist camera | (62.3, −16.3, −46.2) mm in the hand frame · FOV 88.9° (8 real calibration points) | Real-team settings (wrist image not rotated) |
| Start pose | Real home joints [1.4, −17.2, 0.4, −141.7, 1.5, 124.8, 46.2]° — TCP (434.3, 17.3, 297.2) mm | Real-team settings — TCP (437, −19, 292) mm |
| Base height | Lowered 23.5 mm → grasp height within 0.3 mm of the real measurement | 23 mm below the table (real-team setting) |
| Planning limits | Joints 0.8 rad/s (joint 7: 0.15 rad/s) · speed scale 0.4–0.6 (real records) | Joints 45 °/s · 120 °/s² (real control-box limit, from Nov 5), point at flange + 167.6 mm at least 45 mm above the base |
| Sim assist | None (grasp by physics only) | Keeps the tube pose fixed relative to the TCP while grasped (back to physics on release) — not on the real robot |
| Training data (real format) | State 10 = TCP xyz + rot6d (first two columns of the rotation matrix) + finger width · base frame (`fr3_link0`) · TCP = flange + 103.4 mm | State 11 = TCP xyz + rot6d (first two rows) + half-width + (−half-width) · work frame (base rotated −77.2° about z) · TCP = flange + 167.6 mm |

<details>
<summary>First settings (Nov 2)</summary>

| Item | FR3 | FR5 |
|---|---|---|
| Third-person camera | (1.26, −0.02, 0.47) m in the base frame, pitch −21.4°, FOV 69.7° | (0.96, −0.09, 0.50) m, pitch −31.7°, FOV 87° |
| Start pose | [2.8, −16.0, 0, −150.9, 0, 134.9, 47.8]° | [−4.0, −70.2, −110.2, −89.6, 90.0, −1.5]° |
| Planning limits | Joints 0.8 rad/s (joint 7: 0.15 rad/s) | Joints 15 °/s · 120 °/s² |
| State · action dimension (collection records) | 17 (TCP 9 + gripper 1 + joints 7) | 16 (TCP 9 + gripper 1 + joints 6) |

</details>

## 5. Domain randomization (Isaac Lab)

![400 random layouts — top view of the table and the third-person views of both robots](figures/dr_layout.png)

- **What changes:** position · orientation of both racks, red/yellow left-right order, red-ring hole, lighting brightness (×0.6–1.4) · color (5000–8500 K)
- **Conditions (resampled until all are met):** on the table · spacing between the two racks · **0.38–0.76 m and within ±70° from both robot bases** · **inside both robots' third-person views** · not occluded by the robot body. Re-checked with inverse kinematics for both robots at the planning stage
- **Balancing:** left-right combinations · ring holes are shuffled in blocks so that they appear evenly
- **Pairing:** with the same seed, both robots receive the same layout · lighting

## 6. BioTube-AutoDemo-IsaacLab — scripted demo collector

![Scripted demo collector pipeline](figures/pipeline_autodemo_en.png)

### 6-1. Phases of a demonstration

![One FR5 scripted demo with the first setup (Nov 2) — 4× speed, left third-person · right wrist](figures/demo_fr5_full_4x.gif)

One FR5 scripted demo collected with the first setup (Nov 2, 640×360), at 4× speed. Demos are now collected in the real-matched sim, split into branches ([Section 9](#9-dataset)).

| Phase | What it does |
|---|---|
| Go to tube | From the start pose to above the red tube's cap. The wrist turns so the fingers open along the source-rack row |
| Pre-grasp pause · grasp | Closes the gripper over 0.5 s. If it stalls on contact, the "grasp latch" is set |
| Hold and wait · carry | Lifts and carries along a curve, turning the wrist toward the empty-rack row |
| Pause above hole · align with hole | **Re-measures** the in-hand tube pose and places the tube bottom over the hole axis |
| Insert | Descends **along the tube axis** |
| Release · retract upward | Releases, pauses, then retracts upward |

The path methods (minimum-jerk · rounded polyline · rotation about the vertical axis · joint-velocity check) were ported from the real-robot FR3 scripted demo code (`gello_auto.py`), and FR5 uses the same limits as the real control-box safety filter (joints 15 °/s → from Nov 5 the real values 45 °/s · 120 °/s², the point at flange + 167.6 mm at least 45 mm above the base).
Height · arc · dwell time · speed (0.85–1.15×) are varied slightly for each demonstration to add diversity.

![Scripted demo trajectories — top-view TCP path, height, wrist angle, joint velocity/limit (FR3 · FR5, same scene) (figure labels in Korean)](figures/trajectory_ko.png)

### 6-2. Check · save · retry

![FR5 insertion phase with the first setup (Nov 2) — 1× speed](figures/demo_fr5_insert_1x.gif)

- **Check:** tube-axis distance at the hole-collar height ≤ 2 mm · bottom depth · tilt ≤ 12° · at-rest check (yellow tube · ring in place)
- **Save:** only successes are saved, as LeRobot v2 (GR00T format). Failures are kept in `review/버림/` (discarded) together with their reasons
- **Retry:** the same scene is attempted once more; if it still fails, that scene is given up and the collector moves on to the next scene

### 6-3. FR3 · FR5 paired demonstrations

When FR3 saves a scene, FR5 immediately performs **the same scene with the same seed**. For each scene, whether both robots can perform it is checked in advance, and `set` (common · fr3_only · fr5_only) and `pair_id` are recorded.

### 6-4. Data format

The collector keeps sim records, and for training they are converted per robot to the **real format** (`tools/common_to_real.py`, [Report 3](docs/report03_realmatched_data/README_EN.md)).

| Item | Collection records (sim) | Training data (real format) |
|---|---|---|
| Video | `observation.images.third` · `observation.images.wrist`, 848×480 (`--cam-res 848x480`), H.264 — the first collection (Nov 2) was 640×360 · 30 fps | 848×480 · 10 Hz, first-frame brightness matched to the real target per demo, per-camera white balance. Model input 452×256 with the aspect ratio kept |
| State `observation.state` | TCP x · y · z + orientation rot6d (first two rows of the rotation matrix) + gripper (0 open – 1 closed) + joints (FR3 7 · FR5 6) | Real definition per robot — FR3 10 · FR5 11 ([per-robot differences](#per-robot-differences)) |
| Action `action` | Target values in the same layout | Recomputed with each robot's real definition (reference point · rot6d convention · frame · meaning of the gripper value). Trained as relative TCP motion + gripper |
| Instruction | `task_index` → `put the red tube in the red slot` | Same |
| Records | `progress/episodes.jsonl` — scene · seed · `pair_id` · `set` · check values · per-step time | — |

## 7. Equations (summary)

From coordinate frames, pinhole projection, camera fitting, inverse kinematics, the tube model, the jamming angle and funnel seat, randomization conditions, color temperature, the time law, paths, and SO(3) orientation interpolation to insertion along the axis, the success check, the FR5 assist, and the data representation, the equations exactly as the code computes them, together with how they are applied, are in [docs/math_en.md](docs/math_en.md). The key ones:

**Camera fitting** — least squares on the reprojection error between photo points $`u_i`$ and 3D points $`X_i`$

```math
\min_{R,\,t}\;\sum_i \big\lVert u_i - \pi\big(K(RX_i+t)\big)\big\rVert^2
```

**Time law** — minimum-jerk per segment, with the segment duration set by the joint velocity · acceleration limits of both robots

```math
s(\tau)=10\tau^3-15\tau^4+6\tau^5,\qquad
T_v=\max_{\tau,j}\frac{\lvert Q'_j(s)\,s'(\tau)\rvert}{\dot q_j^{max}},\quad
T_a=\sqrt{\max_{\tau,j}\frac{\lvert Q''_j s'^2+Q'_j s''\rvert}{\ddot q_j^{max}}}
```

```math
T=\max\big(T_{cart},\ 1.05\max(T_v,T_a),\ T_{floor},\ 0.6\ \text{s}\big)
```

$`T_{floor}`$ is the common duration matched to the slower of the two robots.

**Success check** — horizontal distance between the point on the tube axis whose height equals the collar height $`z_c`$ and the hole center $`h`$

```math
p(z_c)=b+\frac{z_c-b_z}{a_z}\,a,\qquad d=\big\lVert\,[p(z_c)-h]_{xy}\big\rVert\le 2\ \text{mm}
```

## 8. Data quality tools

| Tool | What it does |
|---|---|
| Review page `review/index.html` | Per demonstration: first · last frames, side-by-side third-person \| wrist video (with phase · gripper · check text overlays), discarded demonstrations and their reasons |
| `tools/common_progress.py` | Saved count · success rate · estimated finish time · pairing status · per-step time breakdown |
| `tools/common_check_dataset.py` | LeRobot v2 format check (row count = number of video frames, no empty values …) |
| `tools/common_check_motion.py` | Finds isolated acceleration spikes (motion jumps) in state · action |

## 9. Dataset

**Current training data (per robot, Nov 13 – 18):** 1,000 real-matched sim demos + DAgger segments (FR5 597 · FR3 449, from 300 runs each) — [Report 7](docs/report07_sim2real_1000/README_EN.md) · [8](docs/report08_dagger_1114_1116/README_EN.md)

| Branch | Demos | Motion | Part used for training |
|---|---|---|---|
| ① Basic | 150 | Same motion as the real scripted collector, without mistakes | All |
| ② Pause-correct | 300 | Stop above a guessed position → correct 1–8 mm sideways → descend | All |
| ③ Offset + correction | 250 | Stop above a position 10–40 mm off → correct while descending | From the offset position |
| ④ Retry after failure | 150 | Empty grasp → grasp again; insertion jams → insert again | From the failed state |
| ⑤ Real-data gaps | 150 | ② · ③ motions in far areas and widely varied layouts missing from the real data | Same as ② · ③ |

Only the 150 demos of ① are clean straight-line demos. Almost all failures are "not correcting the last 1–3 cm", and ② · ③ · ④ show exactly that motion.

<details>
<summary>First 100 pairs (Nov 2 – 3, 640×360 · 30 Hz)</summary>

| | Saved | Discarded · given up | Success rate (per attempt) | Demo length (sim) | Wall-clock time per demo |
|---|---|---|---|---|---|
| FR3 | 100 | 16 discarded · 2 given up | 86 % | about 41 s | about 6 min |
| FR5 | 100 | 1 discarded · 0 given up | 99 % (in-hand hold assist) | about 41 s | about 6 min |
| Pair (both saved) | 99 | — | — | — | — |

We then collected 200 more A pairs · 300 B pairs; the settings that differed from the real robots (30 Hz · 640×360 · state · action definitions · exposure) and the dome-light problem were fixed in [Report 2](docs/report02_vla100_bench/README_EN.md) · [3](docs/report03_realmatched_data/README_EN.md).

</details>

## 10. VLA — GR00T N1.7

- **Model:** the base model `nvidia/GR00T-N1.7-3B` (`NEW_EMBODIMENT`) fine-tuned per robot (vision-language backbone frozen, action part trained)
- **Training:** batch size 64 × 20,000 updates (1.28 M samples — FR3 accumulates two passes of 32 per update), LR 1e-4, color jitter on. The first batch size of 16 was dropped because bigger datasets were learned less ([Report 5](docs/report05_main_bench_stop/README_EN.md))
- **Input · output:** 2 cameras (model input 452×256, aspect ratio kept) + TCP state + gripper → relative TCP motion + gripper, action chunk of 16 steps (10 Hz → 1.6 s)
- **Benchmark:** reuses the collector's scenes · judgment with the policy as the input (`lab/common_bench.py` · policy server `tools/common_groot_server.py`). First try per scene, physics jump = failure, S0–S9 stage scoring (`tools/common_bench_stage.py`), VLA + formula (`lab/common_bench_hybrid.py`) reported separately
- **DAgger:** run the policy in 300 scenes, add only the segments where the formula corrected it from where it went off target, and retrain ([Report 8](docs/report08_dagger_1114_1116/README_EN.md))

## 11. Results

Success rates on the real-matched sim · the same 50 scenes not used in training · first try per scene (physics jump = failure), as of 2026-11-19 ([Report 9](docs/report09_final_1116_1119/README_EN.md)).

| Robot · model | Policy only · fixed | Policy only · random | VLA + formula · fixed | VLA + formula · random |
|---|---|---|---|---|
| FR5 · 1,000 | 62 % | 40 % | 88 % | 96 % |
| FR5 · 1,000 + DAgger | 68 % | 74 % | 94 % | 98 % |
| FR3 · 1,000 | 4 % | 4 % | 98 % | 78 % |
| FR3 · 1,000 + DAgger | 62 % | 34 % | 100 % | 90 % |

<img src="docs/report09_final_1116_1119/figures/fig9_final_pairs_en.png" alt="Final numbers — policy only (open dot) and VLA + formula (filled dot)" width="680">

- **Policy only:** GR00T N1.7 picks and inserts on its own. Converting the FR5 training videos the same way as FR3 (848×480 → 452×256 with the aspect ratio kept) took FR5 from 16 to 62 % on the fixed layout, and **DAgger** (retraining with only the segments where the formula corrected the policy from where it actually went wrong) raised both robots a lot — it fixed FR5's "goes to the nearer tube" habit and FR3's "closes about 6 mm too high".
- **VLA + formula:** the policy chooses the tube and slot, and the scripted-demo formula takes over only the final grasp and insertion once the policy comes within 25 mm of a cap or the red slot (same structure as the real FR3 station). The formula never changes the tube the policy chose.
- On the FR3 real-eval layouts (10 layouts × 5 lightings): 1,000 model 6 % → DAgger 28 % (VLA + formula 64 → 86 %).

![FR5 · policy only after DAgger — insertion phase, 1× speed, left third-person · right wrist](figures/demo_fr5_dagger_insert_1x.gif)

The FR5 insertion phase of the same run as the video at the top (policy only after DAgger, 1× speed, third-person on the left · wrist on the right). The policy aligns over the red slot and inserts without help from the formula.

**Read with care.** Sim success is not a prediction of real success; it is a tool for comparing models within the same sim and the same physics. FR5 sim success relies on a grasp assist the real robot does not have (attach while held), and FR3 sim (Isaac's default Panda model) has no such assist. The fixed layout is in effect two layouts × 25 scenes, so performance at unseen positions is read from the random layout. Details in [Report 4](docs/report04_sim_bench/README_EN.md) and progress logs [5](docs/report05_main_bench_stop/README_EN.md) – [9](docs/report09_final_1116_1119/README_EN.md).

## 12. Roadmap

- [x] Measured assets · digital twin (FR3 · FR5)
- [x] Isaac Lab domain randomization
- [x] Scripted demo collector · paired demonstrations · review page · data check tools
- [x] GR00T N1.7 fine-tuning (100 demos) · first sim benchmark — [Report 2](docs/report02_vla100_bench/README_EN.md)
- [x] Matching the real format (10 Hz · 848×480 · state · action definitions · exposure) · dome-light fix · paired demos with the real settings — [Report 3](docs/report03_realmatched_data/README_EN.md)
- [x] Training amount (batch size 64) · physics-jump rule · stage diagnosis — [Report 5](docs/report05_main_bench_stop/README_EN.md) · [6](docs/report06_improve_1112_1113/README_EN.md)
- [x] Real-matched sim (cameras · base height · start pose · color) · 1,000 demos per robot — [Report 7](docs/report07_sim2real_1000/README_EN.md)
- [x] VLA + formula · S0–S9 scoring · DAgger (FR5 · FR3) · FR5 video format made the same as FR3 — [Report 4](docs/report04_sim_bench/README_EN.md) · [8](docs/report08_dagger_1114_1116/README_EN.md) · [9](docs/report09_final_1116_1119/README_EN.md)

Planned:

- [ ] Check the formula under real-robot conditions (finds targets with the camera) again · VLA + formula side bench — first check on Nov 19 ([Report 9](docs/report09_final_1116_1119/README_EN.md), Section 5)
- [ ] S0–S9 comparison with the real FR5 evaluation
- [ ] One next experiment — DAgger round 2 · a simpler FR5 gripper model · the yellow-ring task · reinforcement-learning fine-tuning · GR00T N2
- [ ] Real-world deployment (Sim-to-Real)

## 13. How to run

```bash
# 1) Install Isaac Lab (extract a separate copy of Isaac Sim 6.0.1 and install into that copy only)
bash lab/common_lab_install.sh
# 2) 100 FR3 scripted demonstrations
bash lab/common_lab_run.sh lab/common_collector.py --robot franka --input auto --new-folder "demo" --base-seed 1103 --auto-count 100
# 3) The same scenes with FR5 (follows the FR3 folder; control panel on a different port)
F=$(ls -td datasets/fr3/*demo*/ | head -1)
bash lab/common_lab_run.sh lab/common_collector.py --robot fr5 --input auto --new-folder "demo" --base-seed 1103 --auto-follow "$F" --panel-port 8801
# 4) Monitor progress · run checks
python3 tools/common_progress.py --memo demo --watch 60
python3 tools/common_check_motion.py --memo demo
```

The control panel is at `http://127.0.0.1:8800` in the browser (8801 for FR5).

## 14. Folder structure and environment

```
├── common_isaacsim_run.py   Standalone Isaac Sim scene (FR3 · FR5)
├── config/                  Shared scene · per-robot settings · randomization · scripted demos · rack seat
├── lab/                     Isaac Lab environment · collector · auto-run · trajectory generator
├── tools/                   Asset building · camera fitting · checks · GR00T scripts
├── assets/usd/              Tube · rack · ring USD
└── docs/                    Documentation · equations · figures
```

Ubuntu · NVIDIA RTX 5090 · Isaac Sim 6.0.1 · Isaac Lab v3.0.0-beta2.patch1 · GR00T N1.7 (separate uv environment)

---

<details>
<summary><b>🍪 Behind the Scenes — How we got here</b></summary>

### The task changed three times
1. **Putting it in a basket** — a "place" action that needs no precision, so the VLA's precise manipulation was hard to observe
2. **The nearest hole of the empty rack** — defining the target in words (a rule) made it ambiguous which hole was meant
3. **The red-ring hole (final)** — the target is defined by a visible marker, focusing on precision insertion with 1 mm clearance

### Problems we ran into
- **The tube jammed at an 8° tilt** — a water-filled round-bottom tube has its center of mass above the center of its hemisphere, so it cannot stand on its own, and in the hollow rack it toppled and caught on the collar (the angle at which a cylinder of diameter 30 jams in a hole of diameter 31 through a plate of thickness 5 = 8.0°). → A sim-only, invisible 45° funnel seat settles it in the center

  ![Before · after the seat (figure labels in Korean)](figures/rack_seat_ko.png)
- **FR5 dropped the tube** — even with a higher grip-force limit, the tube slipped while being lifted and carried. → A sim assist that keeps the tube pose fixed relative to the TCP while grasped (back to physics on release)
- **The sim ran at 0.07× real time** — generating the review videos was using up all the CPU. → Lowest priority · 2 cores, and the bottleneck was found by measuring the per-step time split into physics · camera · rest
- **"Go to tube" took too long** — the wrist rotation continued throughout the whole motion. → Changed the rotation to time-proportional minimum-jerk, mean 11.2 → 8.2 s (joint limits unchanged)
- **The arm seemed to jump in the videos** — it was not the arm but the video compression's keyframes (the whole image changed abruptly every 8.3 s). → Fixed the review-video compression and built a tool that checks for jumps directly from the data values
- **We recorded at a different rate from the real robots** — sim at 30 Hz, real at 10 Hz. The training configuration was compared with the real one item by item, but the data itself was not, so the same "16-step action chunk" became 1.6 s on the real robots and 0.53 s in sim. → A converter to the real format per robot, and a data checklist before training
- **The dome light changed every time Isaac started** — the tube · holder USDs carried Blender's "world" dome (`env_light`), and at each start the renderer picked either our dome or this one → first-image brightness split into about 134 / 185 per run, and the FR3 benchmark ran under lighting different from its training. We had removed it from the warnings because its intensity was 1. → Turned that light off in the object USDs, and now check lighting by the per-run brightness rather than by the settings
- **Physics jumps got a free retry** — on FR5, trials where the sim contact broke were treated as server errors, not counted, and rerun, which in effect gave FR5 alone a second chance. → A jumped trial is a failure and only the first try per scene counts (100-demo model 12/50 → 6/50) — [Report 5](docs/report05_main_bench_stop/README_EN.md)
- **More data, lower scores** — with batch size 16, the 600-demo model saw its data only 1.5–2.6 times in 20,000 steps (real runs: 18–37 times). → Batch size 64; FR3 on the same 200 demos went from 0/50 to 13/50
- **The bench ran at 1/34 of real time** — the CPU clock had fallen back to a slow backup clock and large memory writes were capped at 0.7 GB/s (memory modules at 71–79 °C). → Reboot, hand recording frames over without copying, log memory temperature and speed every minute
- **"1,000 demos" were 675** — offset + correction demos use a different name for the pause stage, and the converter dropped them entirely. → Look for both names, and gate the upload on segment counts — [Report 7](docs/report07_sim2real_1000/README_EN.md)
- **Video compression erased the red cap** — 256×256 · 4:2:0 compression erased about 80 % of the red of the small red cap. → Via color preservation (4:4:4) to the same 848×480 → 452×256 conversion as FR3: FR5 policy-only fixed 16 → 62 % — [Report 9](docs/report09_final_1116_1119/README_EN.md)
- **FR5 went to the nearer tube** — the data was balanced (red nearer in 53 %), but the model learned position as a shortcut instead of color. Asking the same image 20 times aimed between the two tubes all 20 times. → With DAgger, in the 25 red-far scenes, trials that went to the red tube rose from 0 to 18 — [Report 8](docs/report08_dagger_1114_1116/README_EN.md)
- **FR3 closed 6 mm too high** — the demos always went down to exactly the right height, so "if you stopped too high, go lower" was never shown. → FR3 DAgger: policy-only fixed layout 2 → 31/50

Detailed log: [docs/12-자동수집기.md](docs/12-자동수집기.md) (Korean) · progress logs [Report 5](docs/report05_main_bench_stop/README_EN.md) – [9](docs/report09_final_1116_1119/README_EN.md)
</details>
