# blip8-sounds

The generator behind the blip8 SFX pack: 181 chiptune sound effects, CC0, all
of them produced by running this one script. No samples, no recordings, no AI.
Every file is arithmetic.

```sh
uv run generate.py
```

Output lands in `pack/`, ready to zip: mono 16-bit wav at 44100 Hz, sorted into
folders (`ui/`, `pickups/`, `player/`, `weapons/`, `explosions/`, `drums/`,
`jingles/`, `alerts/`, `footsteps/`, `water/`, `doors/`, `teleport/`, `text/`,
`engine/`, `character/`, `gameboy/`), plus a demo reel, a README, and the
license.

## How it works

Every sound is one entry in a list: a path, a plain-English recipe, and the
samples themselves.

```python
add(
    "pickups/coin_classic.wav",
    "short note 988 Hz into a longer one at 1319 Hz",
    sequence(
        envelope(square(freq=988, length=0.07, volume=0.4), attack=0.001, release=0.01),
        envelope(square(freq=1319, length=0.32, volume=0.4), attack=0.001, release=0.2),
    ),
)
```

The recipe string is not a comment. It ships with the pack as `RECIPES.txt`,
one entry per sound, so anyone who downloads it can `pip install blip8`, find
the sound they want to change, edit a number, and render their own version.
That is the whole point of the pack: the sounds are a starting point, not a
fixed set.

Sounds are built with [blip8](https://github.com/sindriax/blip8), my chiptune
synthesis library — `square`, `triangle`, `noise` and `wavetable` oscillators,
shaped with `envelope`, combined with `sequence`, `layer` and `at`.

## Repository layout

| Path | |
| --- | --- |
| `generate.py` | Every sound in the pack, and the render step. |
| `brand/` | Cover art originals. `finalize.py` pads them to the sizes itch and GitHub want. |
| `pack/` | Build output. Regenerated, not committed. |

## License

CC0 1.0. Public domain, commercial use included, no attribution required. See
[LICENSE](LICENSE).
