from patch_lib import mcmeta

TYPE = 'json'

# 1.21 ~ 1.21.11: data format 48 (1.21, 1.21.1), 57 (1.21.2, 1.21.3), 61
# (1.21.4), 71 (1.21.5), 80 (1.21.6), 81 (1.21.7, 1.21.8), 88.0 (1.21.9,
# 1.21.10) and 94.1 (1.21.11).
#
# This series straddles a metadata change: 1.21 ~ 1.21.8 read `pack_format`
# plus `supported_formats`, while 1.21.9 and later read `min_format` and
# `max_format`. Both spellings are therefore written, and they have to agree:
# 1.21.9 validates `supported_formats.min_inclusive` against `min_format` and
# `supported_formats.max_inclusive` against `max_format`, and still requires
# `pack_format` to lie inside the range.
DATA_FORMAT_MIN = [48, 0]
DATA_FORMAT_MAX = [94, 1]
PACK_FORMAT = 48
SUPPORTED_FORMATS = {'min_inclusive': 48, 'max_inclusive': 94}

# Each overlay replaces targets whose vanilla content changed later in the
# series; the main pack keeps the earlier content. Ranges may overlap as long
# as they cover different files.
#
# An overlay entry carries `formats` for 1.21 ~ 1.21.8 and `min_format` /
# `max_format` for 1.21.9 and later; the two must describe the same range.
OVERLAYS = [
    {
        'directory': '1_21_6_loot',    # 1.21.6 snapshot (25w18a) ~ 1.21.11
        'formats': {'min_inclusive': 75, 'max_inclusive': 94},
        'min_format': [75, 0],
        'max_format': [94, 1],
    },
    {
        'directory': '1_21_9_noise',   # 1.21.9 snapshot (25w31a) ~ 1.21.11
        'formats': {'min_inclusive': 82, 'max_inclusive': 94},
        'min_format': [82, 0],
        'max_format': [94, 1],
    },
]

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(
    pack_format=PACK_FORMAT,
    supported_formats=SUPPORTED_FORMATS,
    min_format=DATA_FORMAT_MIN,
    max_format=DATA_FORMAT_MAX,
    overlays=OVERLAYS,
)
