"""Tuning knobs shared by every version that builds through a patch.

Only values and rules live here. Target paths stay in the version patches,
because directory names move between versions (`loot_tables/` before 26.1,
`loot_table/` after) while the values do not. A version patch imports these
constants, so adjusting one knob here reaches every patched version at once.

Every value is the current decision, not a default. A `vanilla` figure in a
comment is the reference used to convert, not what the knob falls back to.

An included set or feature is listed in the version patch, not here: which
vanilla entries exist, and therefore which names may be listed, differs between
versions. These tables only say what happens to an entry that is included.
"""

# --- Climate frequency -------------------------------------------------------

# Overworld climate frequency. Vanilla xz_scale is 0.25, so 1.8 is 7.2x.
#
# temperature and vegetation are inlined in noise_router, so they are scaled
# there. continents, erosion and ridges stay as references to named density
# functions: the biome source and the terrain both read those files, so one
# value in each file covers both sides and keeps them coupled.
XZ_SCALE_OVERWORLD = 1.8

# The two climate fields noise_router inlines. The other three stay references
# and are scaled in their own files, so the biome source keeps reading the same
# density functions as the terrain.
INLINE_CLIMATE_FIELDS = ('temperature', 'vegetation')

# Same role for the nether. Vanilla xz_scale is 0.25, so 1.0 is 4x.
XZ_SCALE_NETHER = 1.0
NETHER_CLIMATE_FIELDS = ('temperature', 'vegetation')

# Base parameters of the four-axis climate noise the pre-1.18 biome source
# reads: vanilla 1.18 values of the noise files the axes map onto. That source
# has no xz_scale, so the frequency is `firstOctave` and the octave weights have
# to be spelled out. The amplitudes set the weight of each octave; collapsing
# them to two entries would change the detail of the grid.
#
# temperature, humidity, altitude and weirdness map onto the vanilla 1.18
# temperature, vegetation, continentalness and ridge noise files in that order.
#
# `firstOctave + len(amplitudes) - 1` must stay <= 0: the old noise only
# allocates levels up to octave 0, and 1.17.1 throws on anything above it. The
# trailing entries of altitude and weirdness are cut for that reason; they are
# the finest octaves, so the layout is unchanged apart from the normalisation
# factor, which is derived from the list length.
LEGACY_CLIMATE_BASE = {
    'temperature': (-10, (1.5, 0.0, 1.0, 0.0, 0.0, 0.0)),
    'humidity': (-8, (1.0, 1.0, 0.0, 0.0, 0.0, 0.0)),
    'altitude': (-9, (1.0, 1.0, 2.0, 2.0, 2.0, 1.0, 1.0)),
    'weirdness': (-7, (1.0, 2.0, 1.0, 0.0, 0.0)),
}

# Octaves added to every axis of LEGACY_CLIMATE_BASE, so this is the only knob
# for how small the legacy biomes get. One octave doubles the frequency, so 3 is
# 8x, i.e. 1/8 in the layer-scale sense. It stays at 3 because 7.2x
# (XZ_SCALE_OVERWORLD) is not a power of two and the old mechanism cannot
# express it; 3 is the equivalent of an xz_scale of 2.0.
LEGACY_CLIMATE_OCTAVE_SHIFT = 3

# Tier of the projected biome table the legacy source reads. The old source
# scans the list linearly for every biome sample, so the tier bounds the
# per-chunk cost: full 2056 entries, balanced 1044, lite 128. The tables are
# generated into `common/biome_source/`; all three can be swapped wholesale.
LEGACY_BIOME_TIER = 'balanced'

# Nether climate axes of the old nether preset. Its entries only vary on
# temperature and humidity, so the other two are left alone.
LEGACY_NETHER_CLIMATE_FIELDS = ('temperature', 'humidity')

# --- Terrain relief ----------------------------------------------------------

# Peak sharpness. jaggedness is the amplitude of the jagged noise added to depth
# on low-erosion ridges; 14 of its 28 spline leaves are zero, covering oceans,
# coasts, plains and wetlands, so scaling it leaves those untouched. With the
# climate frequency raised, the same vertical amplitude would otherwise pile up
# into spikes, since peaks occur far more often than vanilla.
#
# 1.0 is vanilla; the value is the amplitude multiplier.
RELIEF_JAGGED = 0.45

# Mean surface height per climate region, driven by the offset spline. Only the
# positive half (land above sea level) is compressed: negative leaves are ocean
# depth, and leaving them alone keeps sea floors and coastlines where they are.
# 1.0 is vanilla; the value multiplies the positive leaves.
RELIEF_HIGHLAND = 0.45

# Slope steepness, driven by the factor spline. Only leaves above 1.0 are
# compressed, since those are the steep mountain and cliff regions; the ocean
# leaf of 0.625 is left as is. Lifts above the threshold are scaled, so a leaf
# of 6.3 becomes 1.0 + 5.3 * RELIEF_FACTOR. 1.0 is vanilla.
RELIEF_FACTOR = 1.0

# Depth of the underground biome layers (dripstone_caves, lush_caves, deep_dark).
# They are read from the depth axis, where one unit is 128 blocks below the
# surface, so their absolute height follows the surface. Only the highlands are
# compressed, therefore plains and oceans keep both their surface and their
# underground layers, while the layers under a lowered mountain move down
# together with the mountain. Leaving this at 1.0 keeps the depth axis vanilla.
#
# Lower it only to shorten the underground layers themselves, which also lifts
# the layers on flat land; below about 0.90 that puts deep_dark under plains.
UNDERGROUND_RELIEF = 0.9

# depth is deliberately absent from the relief knobs. The terrain density reads
# it, but so does the biome source's depth axis (dripstone_caves, lush_caves,
# deep_dark) and the deep dark test in OverworldBiomeBuilder; all of them assume
# the vanilla slope of 1/128 and a surface-relative zero point. Changing the
# interval or the end values silently moves underground biomes.

# --- Structure density -------------------------------------------------------

# Factors applied to the vanilla spacing/separation of every structure set in a
# dimension. Sets pinned in SPECIAL_FIELD_OVERRIDES keep the values given there.
DIMENSION_SCALES = {
    'overworld': {'spacing': 3/8, 'separation': 1/4},
    'nether': {'spacing': 1/2, 'separation': 1/2},
    'end': {'spacing': 1/3, 'separation': 1/3},
}

# Final values for placement fields the dimension factors cannot express, such
# as the frequency of a structure that fires without a grid. Keyed by structure
# set name; an entry wins over the scaled spacing/separation. Vanilla: frequency
# 0.01 for buried_treasures; distance 32 and spread 3 for strongholds.
SPECIAL_FIELD_OVERRIDES = {
    'buried_treasures': {'frequency': 0.03},
    'strongholds': {'distance': 10, 'spread': 6},
}

# Same table for the sets a version leaves out of its dimension lists. Uncomment
# an entry, then remove the name from that version's list, to pin its fields
# while excluding it from scaling. The values are the vanilla ones, so an entry
# only restores what scaling would replace.
# SPECIAL_FIELD_OVERRIDES.update({
#     'mineshafts': {'frequency': 0.004},             # spacing 1; scaling it is a no-op.
#     'ocean_monuments': {'spacing': 32, 'separation': 5},
#     'nether_fossils': {'spacing': 2, 'separation': 1},
# })

# Structure definitions whose own fields change, keyed by structure name.
# Vanilla max_distance_from_center is 116.
STRUCTURE_FIELD_OVERRIDES = {
    'ancient_city': {'max_distance_from_center': 96},
}

# --- Placed features ---------------------------------------------------------

# `count` is how many times a chunk attempts the placement; vanilla 10 shallow,
# 4 deep. `max_y` caps the top of the vertical range the placement may pick,
# leaving the rest of the range at the vanilla bounds; the vanilla shallow bound
# is `below_top 0`.
PLACED_FEATURE_RULES = {
    'monster_room': {'count': 50, 'max_y': 128},
    'monster_room_deep': {'count': 20},
}

# --- Loot tables -------------------------------------------------------------

# Endermen: vanilla drops 0..1 pearls, the project guarantees at least 1.
ENDERMAN_PEARL_MIN = 1.0

# Bartering pearls: since 1.16.2 vanilla trades 2..4 pearls at weight 10;
# 1.16.1 traded 4..8 at weight 20. Only this entry is restored, so trades added
# by later versions stay in the table.
BARTERING_PEARL = 'minecraft:ender_pearl'
BARTERING_PEARL_WEIGHT = 20
BARTERING_PEARL_MIN = 4.0
BARTERING_PEARL_MAX = 8.0
