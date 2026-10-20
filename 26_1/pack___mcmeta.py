from patch_lib import mcmeta

TYPE = 'json'

# 26.1 snapshot-11 ~ 26.2
DATA_FORMAT_MIN = [100, 0]
DATA_FORMAT_MAX = [107, 1]

OVERLAYS = [
    {
        'directory': '26_2_overworld',    # 26.2 snapshot-8 ~ 26.2
        'min_format': [106, 0],
        'max_format': [107, 1],
    },
    {
        'directory': '26_2_nether',    # 26.2 snapshot-5 ~ 26.2
        'min_format': [104, 0],
        'max_format': [107, 1],
    },
    {
        'directory': '26_2_loot',    # 26.2 snapshot-5 ~ 26.2
        'min_format': [104, 0],
        'max_format': [107, 1],
    },
]

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(
    min_format=DATA_FORMAT_MIN,
    max_format=DATA_FORMAT_MAX,
    overlays=OVERLAYS,
)

