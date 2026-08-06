"""Render the blip8 SFX pack: every sound in the zip comes out of this file.

Run with: uv run generate.py
Output lands in pack/, ready to zip. A manifest (RECIPES.txt) records the
exact call that made each file, so anyone can regenerate or tweak any sound
with `pip install blip8`.
"""

from pathlib import Path

import numpy as np
from blip8 import (
    BELL_TABLE,
    SAMPLE_RATE,
    SINE_TABLE,
    arpeggio,
    at,
    chord,
    crunch,
    envelope,
    layer,
    melody,
    noise,
    note,
    save,
    sequence,
    silence,
    square,
    triangle,
    wavetable,
)

HERE = Path(__file__).parent
OUT = HERE / "pack"

# Every entry: (relative path, human-readable recipe, samples).
SOUNDS: list[tuple[str, str, np.ndarray]] = []


def add(path: str, recipe: str, samples: np.ndarray) -> None:
    SOUNDS.append((path, recipe, samples))


def hit(samples: np.ndarray, length: float) -> np.ndarray:
    """Percussive shape: instant onset, decay to nothing over the whole sound."""
    return envelope(samples, attack=0.001, decay=length, sustain=0.0, release=0.0)


def trim(samples: np.ndarray, fade: float = 0.006) -> np.ndarray:
    """Drop trailing silence and fade the new ending down to zero.

    crunch() quantises a long fade straight to zero, so the file keeps running
    after the sound has stopped. Cutting at the last non-zero sample is not
    enough on its own: that sample is a whole quantisation step above zero, so
    the cut itself would click. The fade is what lands it on silence.
    """
    loud = np.nonzero(samples)[0]
    if not len(loud):
        return samples
    cut = samples[: loud[-1] + 1].copy()
    ramp = min(int(fade * SAMPLE_RATE), len(cut))
    cut[len(cut) - ramp:] *= np.linspace(1.0, 0.0, ramp)
    return cut


# ---------------------------------------------------------------- ui

for label, freq in [("low", 440), ("mid", 660), ("high", 880), ("higher", 1175), ("top", 1568)]:
    for tag, length in [("short", 0.045), ("long", 0.08)]:
        add(
            f"ui/blip_{label}_{tag}.wav",
            f"envelope(square(freq={freq}, length={length}, volume=0.4), attack=0.001, release=0.02)",
            envelope(square(freq=freq, length=length, volume=0.4), attack=0.001, release=0.02),
        )

for label, (a, b) in [("soft", (523, 784)), ("bright", (660, 990)), ("high", (880, 1319)),
                      ("wide", (523, 1047)), ("subtle", (587, 698))]:
    add(
        f"ui/confirm_{label}.wav",
        f"two rising blips at {a} and {b} Hz",
        sequence(
            envelope(square(freq=a, length=0.05, volume=0.4), attack=0.001, release=0.015),
            envelope(square(freq=b, length=0.09, volume=0.4), attack=0.001, release=0.03),
        ),
    )
    add(
        f"ui/cancel_{label}.wav",
        f"two falling blips at {b} and {a} Hz",
        sequence(
            envelope(square(freq=b, length=0.05, volume=0.4), attack=0.001, release=0.015),
            envelope(square(freq=a, length=0.09, volume=0.4), attack=0.001, release=0.03),
        ),
    )

for i, freq in enumerate([110, 147, 196], 1):
    add(
        f"ui/error_{i}.wav",
        f"envelope(square(freq={freq}, length=0.18, duty=0.125, volume=0.45), release=0.05)",
        envelope(square(freq=freq, length=0.18, duty=0.125, volume=0.45), attack=0.001, release=0.05),
    )
    add(
        f"ui/error_double_{i}.wav",
        f"the same buzz at {freq} Hz, twice",
        sequence(
            envelope(square(freq=freq, length=0.08, duty=0.125, volume=0.45), attack=0.001, release=0.02),
            silence(0.04),
            envelope(square(freq=freq, length=0.12, duty=0.125, volume=0.45), attack=0.001, release=0.04),
        ),
    )

for i, (start, end) in enumerate([(440, 880), (523, 1047), (660, 1319)], 1):
    add(
        f"ui/open_{i}.wav",
        f"square glide {start} to {end} Hz",
        envelope(square(freq=(start, end), length=0.12, volume=0.35), attack=0.002, release=0.04),
    )
    add(
        f"ui/close_{i}.wav",
        f"square glide {end} to {start} Hz",
        envelope(square(freq=(end, start), length=0.12, volume=0.35), attack=0.002, release=0.04),
    )

# ---------------------------------------------------------------- pickups

for label, (a, b) in [("classic", (988, 1319)), ("low", (784, 1047)), ("high", (1175, 1568)),
                      ("tiny", (1319, 1760)), ("fat", (659, 880)), ("fifth", (880, 1319))]:
    add(
        f"pickups/coin_{label}.wav",
        f"short note {a} Hz into a longer one at {b} Hz",
        sequence(
            envelope(square(freq=a, length=0.07, volume=0.4), attack=0.001, release=0.01),
            envelope(square(freq=b, length=0.32, volume=0.4), attack=0.001, release=0.2),
        ),
    )

for label, notes in [("major", "C5 E5 G5 C6"), ("minor", "C5 Eb5 G5 C6"),
                     ("sus", "C5 F5 G5 C6"), ("octaves", "C5 C6 C5 C6")]:
    for tag, ln in [("fast", 0.045), ("slow", 0.07)]:
        add(
            f"pickups/powerup_{label}_{tag}.wav",
            f'four rising blips: "{notes}", {ln}s each',
            sequence(*[
                envelope(square(freq=note(n), length=ln, volume=0.4), attack=0.001, release=0.015)
                for n in notes.split()
            ]),
        )

for i, freq in enumerate([1047, 1319, 1568], 1):
    add(
        f"pickups/gem_{i}.wav",
        f"bell wavetable at {freq} Hz, quick fade",
        envelope(wavetable(BELL_TABLE, freq=freq, length=0.35, volume=0.4),
                 attack=0.002, decay=0.35, sustain=0.0, release=0.0),
    )

# ---------------------------------------------------------------- player

for label, (start, end) in [("short", (400, 800)), ("classic", (400, 900)),
                            ("high", (500, 1100)), ("floaty", (300, 700))]:
    add(
        f"player/jump_{label}.wav",
        f"square glide {start} to {end} Hz, duty 0.125",
        envelope(square(freq=(start, end), length=0.13, duty=0.125, volume=0.4),
                 attack=0.001, release=0.03),
    )

for i, (start, end) in enumerate([(300, 120), (400, 150), (250, 90)], 1):
    add(
        f"player/land_{i}.wav",
        f"triangle drop {start} to {end} Hz",
        envelope(triangle(freq=(start, end), length=0.1, volume=0.45),
                 attack=0.001, release=0.03),
    )

for label, (start, end, ln) in [("quick", (440, 110, 0.18)), ("hard", (523, 98, 0.22)),
                                ("long", (392, 82, 0.3))]:
    add(
        f"player/hurt_{label}.wav",
        f"harsh square fall {start} to {end} Hz, duty 0.125",
        envelope(square(freq=(start, end), length=ln, duty=0.125, volume=0.45),
                 attack=0.001, release=0.06),
    )

for i, (start, end) in enumerate([(200, 600), (300, 900)], 1):
    add(
        f"player/dash_{i}.wav",
        f"noise burst with a square swoosh {start} to {end} Hz",
        envelope(square(freq=(start, end), length=0.15, duty=0.25, volume=0.3), attack=0.002, release=0.05)
        + envelope(noise(length=0.15, volume=0.2, seed=7), attack=0.002, decay=0.15, sustain=0.0, release=0.0),
    )

add(
    "player/death.wav",
    "long fall through two octaves, then a thud",
    sequence(
        envelope(square(freq=(660, 82), length=0.5, duty=0.25, volume=0.4), attack=0.001, release=0.1),
        envelope(triangle(freq=(120, 40), length=0.25, volume=0.5),
                 attack=0.001, decay=0.25, sustain=0.0, release=0.0),
    ),
)

# ---------------------------------------------------------------- weapons

for label, (start, end, duty) in [("zap", (1800, 200, 0.25)), ("thin", (1600, 300, 0.125)),
                                  ("heavy", (900, 100, 0.5)), ("fast", (2200, 400, 0.25)),
                                  ("pew", (1400, 500, 0.125))]:
    for tag, ln in [("short", 0.16), ("long", 0.28)]:
        add(
            f"weapons/laser_{label}_{tag}.wav",
            f"square fall {start} to {end} Hz, duty {duty}, {ln}s",
            envelope(square(freq=(start, end), length=ln, duty=duty, volume=0.45),
                     attack=0.001, release=0.05),
        )

for i, seed in enumerate([11, 23, 42], 1):
    add(
        f"weapons/shoot_noise_{i}.wav",
        f"short noise burst, seed {seed}",
        envelope(noise(length=0.09, volume=0.4, seed=seed),
                 attack=0.001, decay=0.09, sustain=0.0, release=0.0),
    )

# ---------------------------------------------------------------- explosions

for label, (ln, thump_start, seed) in [("small", (0.4, 100, 3)), ("mid", (0.7, 130, 5)),
                                       ("big", (1.0, 150, 8)), ("huge", (1.4, 170, 13))]:
    debris = envelope(noise(length=ln, volume=0.35, seed=seed),
                      attack=0.001, decay=ln, sustain=0.0, release=0.0)
    thump = envelope(triangle(freq=(thump_start, 30), length=ln, volume=0.3),
                     attack=0.001, decay=ln * 0.6, sustain=0.0, release=0.0)
    add(
        f"explosions/explosion_{label}.wav",
        f"noise ({ln}s, seed {seed}) over a triangle thump from {thump_start} Hz",
        debris + thump,
    )
    add(
        f"explosions/explosion_{label}_crunched.wav",
        "the same explosion through crunch(bits=4), dead tail trimmed off",
        trim(crunch(debris + thump, bits=4)),
    )

# ---------------------------------------------------------------- drums

for label, (start, end) in [("soft", (100, 45)), ("classic", (120, 40)), ("hard", (150, 35))]:
    add(
        f"drums/kick_{label}.wav",
        f"triangle drop {start} to {end} Hz",
        envelope(triangle(freq=(start, end), length=0.25, volume=0.5),
                 attack=0.001, decay=0.25, sustain=0.0, release=0.0),
    )

for i, seed in enumerate([2, 9, 17, 31], 1):
    body = envelope(noise(length=0.15, volume=0.35, seed=seed),
                    attack=0.001, decay=0.15, sustain=0.0, release=0.0)
    tone = envelope(triangle(freq=180, length=0.15, volume=0.15),
                    attack=0.001, decay=0.08, sustain=0.0, release=0.0)
    add(f"drums/snare_{i}.wav", f"noise (seed {seed}) with a 180 Hz triangle under it", body + tone)

for label, ln in [("closed", 0.03), ("mid", 0.05), ("open", 0.09)]:
    add(
        f"drums/hat_{label}.wav",
        f"a {ln}s tick of noise",
        envelope(noise(length=ln, volume=0.3, seed=4),
                 attack=0.001, decay=ln, sustain=0.0, release=0.0),
    )

for label, ln in [("short", 0.8), ("long", 1.5)]:
    add(
        f"drums/crash_{label}.wav",
        f"noise fading over {ln}s",
        envelope(noise(length=ln, volume=0.35, seed=6),
                 attack=0.001, decay=ln, sustain=0.0, release=0.0),
    )

for label, freq in [("high", 220), ("mid", 165), ("low", 110)]:
    add(
        f"drums/tom_{label}.wav",
        f"triangle drop from {freq} Hz",
        envelope(triangle(freq=(freq, freq * 0.55), length=0.2, volume=0.45),
                 attack=0.001, decay=0.2, sustain=0.0, release=0.0),
    )

# ---------------------------------------------------------------- jingles

add("jingles/win_short.wav", 'melody("C5 E5 G5 C6", bpm=200)', melody("C5 E5 G5 C6", bpm=200))
add("jingles/win_long.wav", 'melody("C5 E5 G5 C6 . G5 C6 .", bpm=180)',
    melody("C5 E5 G5 C6 . G5 C6 .", bpm=180))
add("jingles/lose_short.wav", 'melody("E4 Eb4 D4 Db4", bpm=140)', melody("E4 Eb4 D4 Db4", bpm=140))
add("jingles/lose_long.wav", 'melody("G4 . Gb4 . F4 . E4 . .", bpm=150, voice=triangle)',
    melody("G4 . Gb4 . F4 . E4 . .", bpm=150, voice=triangle))
add("jingles/level_up.wav", 'arpeggio("C5 E5 G5", 0.4) into a held C6',
    sequence(arpeggio("C5 E5 G5", length=0.4, rate=0.03),
         envelope(square(freq=note("C6"), length=0.4, volume=0.4), attack=0.005, release=0.25)))
add("jingles/game_over.wav", 'melody("C4 - G3 - E3 - C3 . .", bpm=120, voice=triangle)',
    melody("C4 - G3 - E3 - C3 . .", bpm=120, voice=triangle))
add("jingles/fanfare.wav", 'melody("G4 G4 G4 C5 . . E5 . C5 . E5 . G5 . . .", bpm=240)',
    melody("G4 G4 G4 C5 . . E5 . C5 . E5 . G5 . . .", bpm=240))
add("jingles/checkpoint.wav", "sine chime at 1047 Hz with a long fade",
    envelope(wavetable(SINE_TABLE, freq=1047, length=1.0, volume=0.4),
             attack=0.005, decay=1.0, sustain=0.0, release=0.0))

# ---------------------------------------------------------------- alerts

for i, (a, b) in enumerate([(660, 880), (523, 698), (784, 1047)], 1):
    add(
        f"alerts/notify_{i}.wav",
        f"two soft bell notes at {a} and {b} Hz",
        sequence(
            envelope(wavetable(BELL_TABLE, freq=a, length=0.15, volume=0.35),
                     attack=0.002, decay=0.15, sustain=0.0, release=0.0),
            envelope(wavetable(BELL_TABLE, freq=b, length=0.4, volume=0.35),
                     attack=0.002, decay=0.4, sustain=0.0, release=0.0),
        ),
    )

for label, (lo, hi) in [("slow", (440, 660)), ("fast", (523, 784))]:
    cycles = 3
    parts = []
    for _ in range(cycles):
        parts.append(square(freq=(lo, hi), length=0.18, duty=0.25, volume=0.35))
        parts.append(square(freq=(hi, lo), length=0.18, duty=0.25, volume=0.35))
    add(
        f"alerts/siren_{label}.wav",
        f"square sweeping {lo} to {hi} Hz and back, {cycles} times",
        envelope(sequence(*parts), attack=0.01, release=0.1),
    )

add("alerts/countdown_tick.wav", "550 Hz blip",
    envelope(square(freq=550, length=0.06, volume=0.4), attack=0.001, release=0.02))
add("alerts/countdown_go.wav", "1100 Hz long blip",
    envelope(square(freq=1100, length=0.35, volume=0.45), attack=0.001, release=0.15))

# ---------------------------------------------------------------- footsteps

# Noise has no pitch, so the surface comes from the tone underneath it: high and
# tight reads as wood or metal, low and dull reads as grass.
STEP_SURFACES = [
    ("stone", 0.05, 150, 0.30),
    ("grass", 0.07, 90, 0.22),
    ("wood", 0.045, 200, 0.28),
    ("metal", 0.05, 320, 0.30),
    ("snow", 0.08, 70, 0.18),
]

for label, ln, thump, vol in STEP_SURFACES:
    for i, seed in enumerate([21, 34], 1):
        add(
            f"footsteps/step_{label}_{i}.wav",
            f"a {ln}s noise tick (seed {seed}) over a triangle at {thump} Hz",
            hit(noise(length=ln, volume=vol, seed=seed), ln)
            + hit(triangle(freq=(thump, thump * 0.6), length=ln, volume=0.18), ln),
        )

for label, ln, thump, vol in STEP_SURFACES[:3]:
    steps = []
    for seed in [21, 34, 45, 56]:
        steps.append(
            hit(noise(length=ln, volume=vol, seed=seed), ln)
            + hit(triangle(freq=(thump, thump * 0.6), length=ln, volume=0.18), ln)
        )
        steps.append(silence(0.11))
    add(f"footsteps/run_{label}.wav", f"four {label} steps, 0.11s apart", sequence(*steps))

# ---------------------------------------------------------------- water

for label, ln, seed in [("small", 0.25, 19), ("big", 0.45, 26)]:
    add(
        f"water/splash_{label}.wav",
        f"noise ({ln}s, seed {seed}) layered with a triangle falling 400 to 80 Hz",
        layer(
            hit(noise(length=ln, volume=0.3, seed=seed), ln),
            hit(triangle(freq=(400, 80), length=ln * 0.8, volume=0.25), ln * 0.8),
        ),
    )

for i, freq in enumerate([1568, 1319], 1):
    add(
        f"water/drip_{i}.wav",
        f"sine wavetable dropping from {freq} Hz, very short",
        hit(wavetable(SINE_TABLE, freq=(freq, freq * 0.5), length=0.09, volume=0.4), 0.09),
    )

for i, (start, end) in enumerate([(300, 900), (400, 1200)], 1):
    add(
        f"water/bubble_{i}.wav",
        f"sine wavetable rising {start} to {end} Hz",
        hit(wavetable(SINE_TABLE, freq=(start, end), length=0.12, volume=0.35), 0.12),
    )

for i, seed in enumerate([12, 28], 1):
    add(
        f"water/swim_{i}.wav",
        f"soft noise swell (seed {seed}) under a triangle sweep",
        layer(
            envelope(noise(length=0.3, volume=0.22, seed=seed), attack=0.08, release=0.12),
            envelope(triangle(freq=(220, 330), length=0.3, volume=0.15), attack=0.08, release=0.12),
        ),
    )

# ---------------------------------------------------------------- doors

add(
    "doors/open_creak.wav",
    "thin square rising 180 to 320 Hz with noise grit over it",
    layer(
        envelope(square(freq=(180, 320), length=0.4, duty=0.125, volume=0.25),
                 attack=0.02, release=0.08),
        envelope(noise(length=0.4, volume=0.1, seed=37), attack=0.05, release=0.15),
    ),
)
add(
    "doors/close_creak.wav",
    "the same creak falling 320 to 180 Hz, ending in a thunk",
    sequence(
        layer(
            envelope(square(freq=(320, 180), length=0.3, duty=0.125, volume=0.25),
                     attack=0.02, release=0.06),
            envelope(noise(length=0.3, volume=0.1, seed=37), attack=0.05, release=0.1),
        ),
        hit(triangle(freq=(140, 45), length=0.18, volume=0.45), 0.18),
    ),
)
add(
    "doors/thunk.wav",
    "triangle drop from 160 Hz with a noise slap on top",
    layer(
        hit(triangle(freq=(160, 45), length=0.2, volume=0.45), 0.2),
        hit(noise(length=0.06, volume=0.2, seed=8), 0.06),
    ),
)
add(
    "doors/locked.wav",
    "two dull 98 Hz buzzes: the door does not move",
    sequence(
        envelope(square(freq=98, length=0.07, duty=0.125, volume=0.4), attack=0.001, release=0.02),
        silence(0.05),
        envelope(square(freq=98, length=0.1, duty=0.125, volume=0.4), attack=0.001, release=0.03),
    ),
)
add(
    "doors/unlock.wav",
    "a metal click, then two rising bell notes",
    sequence(
        hit(noise(length=0.04, volume=0.25, seed=15), 0.04),
        silence(0.03),
        hit(wavetable(BELL_TABLE, freq=880, length=0.1, volume=0.3), 0.1),
        hit(wavetable(BELL_TABLE, freq=1319, length=0.3, volume=0.3), 0.3),
    ),
)
add(
    "doors/gate_heavy.wav",
    "a long low grind: 60 Hz square under a slow noise bed",
    layer(
        envelope(square(freq=(60, 55), length=0.9, duty=0.5, volume=0.25), attack=0.05, release=0.2),
        envelope(noise(length=0.9, volume=0.12, seed=41), attack=0.1, release=0.3),
    ),
)

# ---------------------------------------------------------------- teleport

for label, (start, end) in [("in", (200, 1800)), ("out", (1800, 200))]:
    add(
        f"teleport/teleport_{label}.wav",
        f"sine wavetable gliding {start} to {end} Hz over 0.5s",
        envelope(wavetable(SINE_TABLE, freq=(start, end), length=0.5, volume=0.4),
                 attack=0.01, release=0.15),
    )

for i, (lo, hi) in enumerate([(400, 1600), (300, 1200)], 1):
    warble = []
    for _ in range(4):
        warble.append(wavetable(SINE_TABLE, freq=(lo, hi), length=0.09, volume=0.35))
        warble.append(wavetable(SINE_TABLE, freq=(hi, lo), length=0.09, volume=0.35))
    add(
        f"teleport/warp_{i}.wav",
        f"sine wavetable warbling between {lo} and {hi} Hz, four times",
        envelope(sequence(*warble), attack=0.01, release=0.12),
    )

add(
    "teleport/blink.wav",
    "a single fast sine sweep, 600 to 2400 Hz in 0.07s",
    hit(wavetable(SINE_TABLE, freq=(600, 2400), length=0.07, volume=0.4), 0.07),
)
add(
    "teleport/phase_out.wav",
    "warble falling into silence, then crunch(bits=4)",
    crunch(
        envelope(wavetable(SINE_TABLE, freq=(1400, 120), length=0.7, volume=0.4),
                 attack=0.005, decay=0.7, sustain=0.0, release=0.0),
        bits=4,
    ),
)

# ---------------------------------------------------------------- text

for label, freq in [("low", 660), ("mid", 990), ("high", 1319)]:
    tick = envelope(square(freq=freq, length=0.02, duty=0.25, volume=0.3),
                    attack=0.001, release=0.008)
    add(f"text/blip_{label}.wav", f"a 0.02s tick at {freq} Hz, quiet enough to repeat", tick)
    add(
        f"text/scroll_{label}.wav",
        f"eight {freq} Hz ticks 0.055s apart, loops cleanly",
        sequence(*[part for _ in range(8) for part in (tick, silence(0.035))]),
    )

add(
    "text/typewriter.wav",
    "a noise click with a 1200 Hz tick on top",
    layer(
        hit(noise(length=0.025, volume=0.25, seed=53), 0.025),
        hit(square(freq=1200, length=0.015, duty=0.125, volume=0.2), 0.015),
    ),
)

# ---------------------------------------------------------------- engine

# Loopable: no attack or release, so the end butts against the start without a
# click. Trim or repeat these in your engine, they are meant to be held.
for label, freq in [("low", 55), ("mid", 82), ("high", 110)]:
    add(
        f"engine/hum_{label}.wav",
        f"1s of {freq} Hz square (duty 0.125) plus its octave, no envelope: loopable",
        layer(
            square(freq=freq, length=1.0, duty=0.125, volume=0.25),
            square(freq=freq * 2, length=1.0, duty=0.25, volume=0.1),
        ),
    )

add(
    "engine/hum_rough.wav",
    "the low hum with a noise bed, then crunch(bits=4): loopable",
    crunch(
        layer(
            square(freq=55, length=1.0, duty=0.125, volume=0.25),
            noise(length=1.0, volume=0.06, seed=61),
        ),
        bits=4,
    ),
)
add(
    "engine/rev.wav",
    "square climbing 55 to 165 Hz over 0.8s",
    envelope(square(freq=(55, 165), length=0.8, duty=0.125, volume=0.35),
             attack=0.02, release=0.1),
)
add(
    "engine/ufo_hum.wav",
    "sine wavetable wobbling 220 to 260 Hz and back, twice: loopable",
    sequence(*[part for _ in range(2) for part in (
        wavetable(SINE_TABLE, freq=(220, 260), length=0.25, volume=0.3),
        wavetable(SINE_TABLE, freq=(260, 220), length=0.25, volume=0.3),
    )]),
)

# ---------------------------------------------------------------- character
#
# The sounds the grid cannot make: several voices overlapping on their own
# schedule (layer + at), chords, and short motifs. These are the showpieces.

add(
    "character/charge_and_fire.wav",
    "a rising charge whine, then the shot falls out of it",
    sequence(
        envelope(square(freq=(200, 1200), length=0.55, duty=0.125, volume=0.3),
                 attack=0.15, release=0.02),
        envelope(square(freq=(2000, 180), length=0.3, duty=0.25, volume=0.45),
                 attack=0.001, release=0.06),
    ),
)
add(
    "character/shield_up.wav",
    'chord("C4 G4 C5") under a sweep rising into it',
    layer(
        envelope(square(freq=(220, 523), length=0.35, duty=0.25, volume=0.25),
                 attack=0.05, release=0.05),
        at(0.28, chord("C4 G4 C5", length=0.6, volume=0.14)),
    ),
)
add(
    "character/magic_sparkle.wav",
    "five bell notes started 0.06s apart with at(), all ringing together",
    layer(*[
        at(i * 0.06, hit(wavetable(BELL_TABLE, freq=freq, length=0.5, volume=0.22), 0.5))
        for i, freq in enumerate([1047, 1319, 1568, 2093, 2637])
    ]),
)
add(
    "character/spell_cast.wav",
    "a noise swell, then an arpeggio bursting out of it",
    layer(
        envelope(noise(length=0.5, volume=0.18, seed=67), attack=0.35, release=0.1),
        at(0.32, arpeggio("C5 G5 C6 E6", length=0.35, rate=0.025, volume=0.3)),
    ),
)
add(
    "character/boss_hit.wav",
    "kick, noise slap and a low tom stacked with at() offsets",
    layer(
        hit(triangle(freq=(150, 35), length=0.35, volume=0.4), 0.35),
        at(0.01, hit(noise(length=0.25, volume=0.25, seed=71), 0.25)),
        at(0.05, hit(triangle(freq=(110, 60), length=0.3, volume=0.2), 0.3)),
    ),
)
add(
    "character/big_impact.wav",
    "the same idea, bigger: 0.9s of debris over a sub thump and a crunched layer",
    layer(
        hit(triangle(freq=(170, 28), length=0.9, volume=0.35), 0.9),
        hit(noise(length=0.9, volume=0.28, seed=73), 0.9),
        at(0.03, crunch(hit(noise(length=0.4, volume=0.15, seed=79), 0.4), bits=4)),
    ),
)
add(
    "character/one_up.wav",
    'melody("C5 E5 G5 C6 E6", bpm=300) with a bell chime laid over the last note',
    layer(
        melody("C5 E5 G5 C6 E6", bpm=300),
        at(0.4, hit(wavetable(BELL_TABLE, freq=2093, length=0.6, volume=0.22), 0.6)),
    ),
)
add(
    "character/treasure_reveal.wav",
    'a rising arpeggio into chord("C5 E5 G5 C6"), bells on top',
    sequence(
        arpeggio("C5 E5 G5 C6", length=0.5, rate=0.03, volume=0.3),
        layer(
            chord("C5 E5 G5 C6", length=0.9, volume=0.12),
            at(0.06, hit(wavetable(BELL_TABLE, freq=2637, length=0.8, volume=0.18), 0.8)),
        ),
    ),
)
add(
    "character/power_down.wav",
    "everything sagging at once: square, triangle and pitch all falling, crunched",
    crunch(
        layer(
            envelope(square(freq=(880, 60), length=0.9, duty=0.25, volume=0.3),
                     attack=0.005, release=0.2),
            at(0.1, envelope(triangle(freq=(440, 40), length=0.8, volume=0.25),
                             attack=0.005, release=0.2)),
        ),
        bits=4,
    ),
)
add(
    "character/heartbeat.wav",
    "two sub thumps 0.28s apart, the second softer",
    layer(
        hit(triangle(freq=(80, 35), length=0.22, volume=0.5), 0.22),
        at(0.28, hit(triangle(freq=(70, 32), length=0.3, volume=0.32), 0.3)),
    ),
)
add(
    "character/menu_stab.wav",
    "a noise swoosh with a chord stab landing on the end of it",
    layer(
        envelope(noise(length=0.22, volume=0.16, seed=83), attack=0.12, release=0.06),
        at(0.16, chord("E5 G5 B5", length=0.4, volume=0.13)),
    ),
)
add(
    "character/alarm_motif.wav",
    'melody("C5 G5 C5 G5 C5 G5", bpm=340) over a held low square',
    layer(
        melody("C5 G5 C5 G5 C5 G5", bpm=340),
        # The held square needs its own envelope: a raw oscillator starts and
        # ends mid-cycle at full amplitude, which is an audible click.
        envelope(square(freq=131, length=1.06, duty=0.125, volume=0.12),
                 attack=0.01, release=0.05),
    ),
)

# ---------------------------------------------------------------- gameboy variants

# A 4-bit crunched selection: the Game Boy only had 16 volume steps, and the
# grit reads instantly as handheld.
GB_PICKS = [
    "ui/blip_mid_short.wav", "ui/confirm_bright.wav", "ui/cancel_bright.wav",
    "pickups/coin_classic.wav", "pickups/powerup_major_fast.wav",
    "player/jump_classic.wav", "player/hurt_quick.wav",
    "weapons/laser_zap_short.wav", "drums/kick_classic.wav", "drums/snare_1.wav",
]
# Resolved before the loop: add() appends to SOUNDS as it goes.
for path, recipe, samples in [entry for entry in SOUNDS if entry[0] in GB_PICKS]:
    name = path.replace("/", "_").removesuffix(".wav")
    add(f"gameboy/{name}_gb.wav", f"{recipe}, then crunch(bits=4)", crunch(samples, bits=4))


# The demo reel is GB_PICKS (each original, then its crunched twin) plus these:
# one representative per folder, weighted toward the character sounds.
DEMO_EXTRA = [
    "explosions/explosion_big.wav",
    "jingles/win_short.wav",
    "jingles/fanfare.wav",
    "footsteps/run_stone.wav",
    "water/splash_big.wav",
    "doors/thunk.wav",
    "teleport/warp_1.wav",
    "text/scroll_mid.wav",
    "engine/rev.wav",
    "character/charge_and_fire.wav",
    "character/magic_sparkle.wav",
    "character/boss_hit.wav",
    "character/treasure_reveal.wav",
    "character/one_up.wav",
    "character/power_down.wav",
]


# ---------------------------------------------------------------- render

def counts() -> dict[str, int]:
    """Sounds per folder, in the order the folders were written."""
    tally: dict[str, int] = {}
    for path, _, _ in SOUNDS:
        folder = path.split("/")[0]
        tally[folder] = tally.get(folder, 0) + 1
    return tally


def write_readme() -> None:
    tally = counts()
    listing = "\n".join(f"  {folder:<12} {n:>3}" for folder, n in tally.items())
    (OUT / "README.txt").write_text(
        f"""8-bit SFX pack
{len(SOUNDS)} chiptune sound effects, free, CC0, no credit needed.

Mono 16-bit wav, 44100 Hz. Drop them straight into Unity, Godot, GameMaker,
Love2D, a browser game, whatever you are building.

{listing}

The engine/hum_*, engine/ufo_hum and text/scroll_* files loop cleanly: no fade
in or out, so the end butts against the start without a click. Everything else
is a one-shot, engine/rev.wav included.


The gimmick
Every sound here was generated from code, not recorded. No samples, no AI:
each file is arithmetic. RECIPES.txt lists the exact call that made every
single one, so you can change a number and render your own version.

    pip install blip8

Want the laser to fall from 2000 Hz instead of 1800? Open RECIPES.txt, find
weapons/laser_zap_short.wav, change the number, run it.

blip8 is my chiptune synthesis library:
https://github.com/sindriax/blip8


License
CC0 1.0. Public domain. Use them in anything, commercial included, no credit
required. See LICENSE.txt. If you do feel like linking back, sindriax.dev.


Made by Sandra
https://sindriax.dev
https://github.com/sindriax
"""
    )


def write_license() -> None:
    (OUT / "LICENSE.txt").write_text((HERE / "LICENSE").read_text())


def main() -> None:
    manifest = []
    for path, recipe, samples in SOUNDS:
        target = OUT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        save(samples, str(target))
        manifest.append(f"{path}\n    {recipe}")

    (OUT / "RECIPES.txt").write_text(
        "blip8 SFX pack: every sound, and the blip8 call that made it.\n"
        "Regenerate or tweak any of them: pip install blip8\n"
        "https://github.com/sindriax/blip8\n\n" + "\n\n".join(manifest) + "\n"
    )
    write_readme()
    write_license()

    demo_parts = []
    for path, _, samples in SOUNDS:
        if path in GB_PICKS or path in DEMO_EXTRA:
            demo_parts.append(samples)
            demo_parts.append(silence(0.18))
    save(sequence(*demo_parts), str(OUT / "demo_reel.wav"))

    tally = counts()
    print(f"rendered {len(SOUNDS)} sounds + demo_reel.wav into {OUT}/")
    print("  " + ", ".join(f"{folder} {n}" for folder, n in tally.items()))


if __name__ == "__main__":
    main()
