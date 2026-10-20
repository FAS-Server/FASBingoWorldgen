"""Measure nether biome patch size and the radius needed to cover all biomes.

Offline analysis helper. It rebuilds the climate noise from the published
Perlin noise formulation (Perlin 1985, improved noise 2002) using the noise
parameters found in the nether world preset, labels a tile of the noise field
with the nearest biome, and reports how large the patches are and how far a
player has to travel to have seen every biome.

The same script answers both questions a scale change raises:

- Do the patches still read as distinct biomes rather than noise?
- Does a single trip still reach all five?

Requirements: numpy, scipy.

Usage:
    python generator/biome_scale.py
    python generator/biome_scale.py --multiplier 2.6 --samples 1000
    python generator/biome_scale.py --multiplier 4 --json
"""

import argparse
import json
import sys
import typing as ty

import numpy as np
from scipy.ndimage import distance_transform_edt

# xz_scale of the nether climate noises as set by the nether world preset;
# the measured multiplier is applied on top of it.
VANILLA_XZ_SCALE = 0.25

# Noise parameters of the nether temperature and vegetation noises.
FIRST_OCTAVE = -7
AMPLITUDES = (1.0, 1.0)

# The climate noises average two octave stacks offset by this factor.
SECOND_INSTANCE_SCALE = 1.0181268882175227
VALUE_FACTOR_NUMERATOR = 0.16666666666666666

# Gradient table of the improved noise reference implementation.
GRADIENTS = np.array([
    [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
    [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
    [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
    [1, 1, 0], [0, -1, 1], [-1, 1, 0], [0, -1, -1],
], dtype=float)

# Climate parameters of each nether biome, as listed by the nether preset:
# temperature, humidity, offset (the humidity axis carries vegetation noise).
# offset is stored quantized to 1/10000 and enters the distance as a squared
# term.
NETHER_BIOMES = (
    ('nether_wastes', 0.0, 0.0, 0.0),
    ('soul_sand_valley', 0.0, -0.5, 0.0),
    ('crimson_forest', 0.4, 0.0, 0.0),
    ('warped_forest', 0.0, 0.5, 0.375),
    ('basalt_deltas', -0.5, 0.0, 0.175),
)


def _smoothstep(t: np.ndarray) -> np.ndarray:
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


class ImprovedNoise:
    '''One octave of improved noise.'''

    def __init__(self, rng: np.random.Generator):
        # The generator is seeded from a random source; the exact sequence is
        # irrelevant, only the statistical properties matter here.
        self.origin = rng.random(3) * 256.0
        table = np.arange(256)
        for i in range(256):
            swap = rng.integers(0, 256 - i)
            table[i], table[i + swap] = table[i + swap], table[i]
        self.table = table.astype(np.int64)

    def plane(self, x: np.ndarray, z: np.ndarray) -> np.ndarray:
        '''Samples the noise on a horizontal plane; climate noises do not vary
        with height.'''
        table = self.table
        fx = x + self.origin[0]
        fz = z + self.origin[2]
        fy = self.origin[1]
        ix = np.floor(fx).astype(np.int64)
        iz = np.floor(fz).astype(np.int64)
        iy = int(np.floor(fy))
        rx = fx - np.floor(fx)
        rz = fz - np.floor(fz)
        ry = fy - np.floor(fy)

        x0 = table[ix & 0xFF]
        x1 = table[(ix + 1) & 0xFF]
        xy00 = table[(x0 + iy) & 0xFF]
        xy01 = table[(x0 + iy + 1) & 0xFF]
        xy10 = table[(x1 + iy) & 0xFF]
        xy11 = table[(x1 + iy + 1) & 0xFF]

        def gradient(index: np.ndarray, dx: np.ndarray, dy: float, dz: np.ndarray) -> np.ndarray:
            g = GRADIENTS[index & 0xF]
            return g[..., 0] * dx + g[..., 1] * dy + g[..., 2] * dz

        d000 = gradient(table[(xy00 + iz) & 0xFF], rx, ry, rz)
        d100 = gradient(table[(xy10 + iz) & 0xFF], rx - 1.0, ry, rz)
        d010 = gradient(table[(xy01 + iz) & 0xFF], rx, ry - 1.0, rz)
        d110 = gradient(table[(xy11 + iz) & 0xFF], rx - 1.0, ry - 1.0, rz)
        d001 = gradient(table[(xy00 + iz + 1) & 0xFF], rx, ry, rz - 1.0)
        d101 = gradient(table[(xy10 + iz + 1) & 0xFF], rx - 1.0, ry, rz - 1.0)
        d011 = gradient(table[(xy01 + iz + 1) & 0xFF], rx, ry - 1.0, rz - 1.0)
        d111 = gradient(table[(xy11 + iz + 1) & 0xFF], rx - 1.0, ry - 1.0, rz - 1.0)

        ax = _smoothstep(rx)
        ay = _smoothstep(ry)
        az = _smoothstep(rz)

        def lerp(t: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
            return a + t * (b - a)

        x00 = lerp(ax, d000, d100)
        x10 = lerp(ax, d010, d110)
        x01 = lerp(ax, d001, d101)
        x11 = lerp(ax, d011, d111)
        return lerp(az, lerp(ay, x00, x10), lerp(ay, x01, x11))


class PerlinNoise:
    '''Octave stack of improved noise.'''

    def __init__(self, rng: np.random.Generator, first_octave: int, amplitudes: ty.Sequence[float]):
        self.amplitudes = tuple(amplitudes)
        self.levels = [ImprovedNoise(rng) if a != 0.0 else None for a in amplitudes]
        nonzero = [i for i, a in enumerate(amplitudes) if a != 0.0]
        # Input and value factors of the lowest frequency octave.
        self.input_factor = 2.0 ** first_octave
        self.value_factor = 2.0 ** (len(nonzero) - 1) / (2.0 ** len(nonzero) - 1.0)

    def plane(self, x: np.ndarray, z: np.ndarray) -> np.ndarray:
        result = np.zeros_like(x)
        factor = self.input_factor
        value_factor = self.value_factor
        for amplitude, level in zip(self.amplitudes, self.levels):
            if level is not None:
                result += amplitude * level.plane(x * factor, z * factor) * value_factor
            factor *= 2.0
            value_factor /= 2.0
        return result


class NormalNoise:
    '''Two averaged octave stacks, giving unit scale noise.'''

    def __init__(self, rng: np.random.Generator, first_octave: int, amplitudes: ty.Sequence[float]):
        self.first = PerlinNoise(rng, first_octave, amplitudes)
        self.second = PerlinNoise(rng, first_octave, amplitudes)
        nonzero = [i for i, a in enumerate(amplitudes) if a != 0.0]
        span = max(nonzero) - min(nonzero)
        expected_deviation = 0.1 * (1.0 + 1.0 / (span + 1))
        self.value_factor = VALUE_FACTOR_NUMERATOR / expected_deviation

    def plane(self, x: np.ndarray, z: np.ndarray) -> np.ndarray:
        first = self.first.plane(x, z)
        second = self.second.plane(x * SECOND_INSTANCE_SCALE, z * SECOND_INSTANCE_SCALE)
        return (first + second) * self.value_factor


def label_field(multiplier: float, extent: int, step: int, seed: int) \
        -> ty.Tuple[np.ndarray, int, int]:
    '''Labels every sample of a square tile with the nearest biome index.'''
    rng = np.random.default_rng(seed)
    temperature = NormalNoise(rng, FIRST_OCTAVE, AMPLITUDES)
    vegetation = NormalNoise(rng, FIRST_OCTAVE, AMPLITUDES)

    xz_scale = VANILLA_XZ_SCALE * multiplier
    count = extent // step
    coords = np.arange(count) * step
    grid_x, grid_z = np.meshgrid(coords, coords)

    field_t = temperature.plane(grid_x * xz_scale, grid_z * xz_scale)
    field_v = vegetation.plane(grid_x * xz_scale, grid_z * xz_scale)

    best = np.full(field_t.shape, np.inf)
    labels = np.zeros(field_t.shape, dtype=np.int16)
    for index, (_, target_t, target_v, offset) in enumerate(NETHER_BIOMES):
        distance = (field_t - target_t) ** 2 + (field_v - target_v) ** 2 + offset ** 2
        closer = distance < best
        best[closer] = distance[closer]
        labels[closer] = index
    return labels, step, count


def _run_lengths(labels: np.ndarray) -> np.ndarray:
    '''Lengths of consecutive same-label stretches along rows, in samples.'''
    lengths = []
    for row in labels:
        current = 1
        for index in range(1, len(row)):
            if row[index] == row[index - 1]:
                current += 1
            else:
                lengths.append(current)
                current = 1
        lengths.append(current)
    return np.array(lengths)


def _origins(count: int, samples: int, seed: int) -> ty.Tuple[np.ndarray, np.ndarray]:
    '''Random origins, kept away from the tile edge so distances are not truncated.'''
    rng = np.random.default_rng(seed)
    margin = count // 10
    rows = rng.integers(margin, count - margin, samples)
    cols = rng.integers(margin, count - margin, samples)
    return rows, cols


def measure(multiplier: float, extent: int, step: int, samples: int, seed: int) -> ty.Dict:
    labels, step, count = label_field(multiplier, extent, step, seed)
    rows, cols = _origins(count, samples, seed + 1)

    distances = {}
    for index, (name, _, _, _) in enumerate(NETHER_BIOMES):
        distance = distance_transform_edt(labels != index) * step
        distances[name] = distance[rows, cols]

    stacked = np.stack([distances[name] for name, _, _, _ in NETHER_BIOMES])
    radius = stacked.max(axis=0)
    bottleneck = stacked.argmax(axis=0)

    shares = {name: float((labels == index).mean()) for index, (name, _, _, _) in enumerate(NETHER_BIOMES)}
    patch = _run_lengths(labels) * step

    def summary(values: np.ndarray) -> ty.Dict:
        return {
            'mean': float(values.mean()),
            'median': float(np.median(values)),
            'p90': float(np.percentile(values, 90)),
        }

    return {
        'multiplier': multiplier,
        'xz_scale': VANILLA_XZ_SCALE * multiplier,
        'extent': extent,
        'step': step,
        'seed': seed,
        'shares': shares,
        'patch_length': summary(patch),
        'nearest': {name: summary(values) for name, values in distances.items()},
        'coverage_radius': summary(radius),
        'bottleneck': {
            name: float((bottleneck == index).mean())
            for index, (name, _, _, _) in enumerate(NETHER_BIOMES)
        },
    }


def _print_report(result: ty.Dict) -> None:
    print(f"multiplier {result['multiplier']:.2f}  xz_scale {result['xz_scale']:.3f}  "
          f"extent {result['extent']}  step {result['step']}  seed {result['seed']}")
    print()

    print('share of the surface')
    for name, share in result['shares'].items():
        print(f'  {name:<18} {share * 100:5.1f}%')
    print()

    patch = result['patch_length']
    print(f"patch length along a row: median {patch['median']:.0f}  "
          f"mean {patch['mean']:.0f}  p90 {patch['p90']:.0f} blocks")
    print()

    print('distance to the nearest patch')
    for name, near in result['nearest'].items():
        print(f"  {name:<18} median {near['median']:6.0f}  mean {near['mean']:6.0f}  "
              f"p90 {near['p90']:6.0f}")
    print()

    radius = result['coverage_radius']
    print(f"radius covering all biomes: median {radius['median']:.0f}  "
          f"mean {radius['mean']:.0f}  p90 {radius['p90']:.0f} blocks")
    print()

    print('which biome sets the radius')
    for name, share in sorted(result['bottleneck'].items(), key=lambda item: -item[1]):
        print(f'  {name:<18} {share * 100:5.1f}%')


def main(argv: ty.Optional[ty.Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--multiplier', type=float, default=4.0,
                        help='nether climate frequency relative to vanilla (default 4)')
    parser.add_argument('--extent', type=int, default=0,
                        help='tile side in blocks; 0 picks a value from the multiplier')
    parser.add_argument('--step', type=int, default=4,
                        help='sampling step in blocks (default 4)')
    parser.add_argument('--samples', type=int, default=600,
                        help='number of random origins (default 600)')
    parser.add_argument('--seed', type=int, default=12345)
    parser.add_argument('--json', action='store_true', help='emit JSON instead of text')
    args = parser.parse_args(argv)

    # Keep the tile large enough for the patch scale: four times the vanilla
    # wavelength at the requested multiplier, rounded to the sampling step.
    extent = args.extent or int(16384 / args.multiplier)
    extent = max(extent - extent % args.step, args.step * 64)

    result = measure(args.multiplier, extent, args.step, args.samples, args.seed)
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write('\n')
    else:
        _print_report(result)
    return 0


if __name__ == '__main__':
    sys.exit(main())
