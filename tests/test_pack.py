"""Quality gate for the pack: importing generate.py renders every sound.

People download these files, so the invariants worth enforcing are the ones a
listener would notice: nothing clipped, nothing silent, nothing truncated, and
nothing quietly missing from the demo reel.
"""

import numpy as np
import pytest

import generate
from generate import DEMO_EXTRA, GB_PICKS, SOUNDS

PATHS = {path for path, _, _ in SOUNDS}


def test_the_pack_is_the_advertised_size() -> None:
    assert len(SOUNDS) >= 150, "the README promises 150+"


def test_every_path_is_unique() -> None:
    assert len(PATHS) == len(SOUNDS), "a duplicate path would overwrite a rendered file"


@pytest.mark.parametrize("path,recipe,samples", SOUNDS, ids=[s[0] for s in SOUNDS])
def test_every_sound_is_usable(path: str, recipe: str, samples: np.ndarray) -> None:
    assert path.endswith(".wav")
    assert recipe, "every sound owes RECIPES.txt a line"
    assert len(samples), "no empty files"
    assert np.isfinite(samples).all()

    peak = float(np.max(np.abs(samples)))
    assert peak <= 1.0, f"clips at {peak:.3f}, save() would wrap it"
    assert peak > 0.05, f"inaudible at {peak:.3f}"


@pytest.mark.parametrize("path", sorted(p for p in PATHS if "crunch" in p))
def test_crunched_sounds_have_no_dead_tail(path: str) -> None:
    """crunch() quantises the fade straight to zero, leaving the file running
    after the sound has stopped. Untrimmed these carry ~73ms of silence."""
    samples = next(s for p, _, s in SOUNDS if p == path)
    trailing = len(samples) - int(np.max(np.nonzero(samples))) - 1
    assert trailing / 44100 < 0.01, f"{trailing / 44100 * 1000:.0f}ms of dead air"


@pytest.mark.parametrize("path", sorted(set(GB_PICKS) | set(DEMO_EXTRA)))
def test_the_demo_reel_only_names_sounds_that_exist(path: str) -> None:
    """A typo here drops a sound from the reel silently, which is the bug to catch."""
    assert path in PATHS


def test_the_gameboy_variants_cover_every_pick() -> None:
    for pick in GB_PICKS:
        variant = "gameboy/" + pick.replace("/", "_").removesuffix(".wav") + "_gb.wav"
        assert variant in PATHS, f"{pick} has no crunched twin"


def test_loopable_sounds_are_not_faded() -> None:
    """The README tells people these loop cleanly, so they must keep their edges."""
    for path in PATHS:
        if not path.startswith("engine/hum") and not path.startswith("text/scroll"):
            continue
        samples = next(s for p, _, s in SOUNDS if p == path)
        head = float(np.max(np.abs(samples[:200])))
        assert head > 0.01, f"{path} fades in, so it will click when looped"


def test_trim_cuts_the_silence_and_lands_on_zero() -> None:
    """Cutting at the last non-zero sample is not enough on its own: that sample
    is a whole quantisation step above zero, so the cut itself would click."""
    faded = generate.trim(np.array([0.5, 0.5, 0.5, 0.0, 0.0]))
    assert len(faded) == 3, "trailing zeros not cut"
    assert faded[-1] == 0.0, "the cut would click"
    assert faded[0] == 0.5, "the fade ate into the sound"
