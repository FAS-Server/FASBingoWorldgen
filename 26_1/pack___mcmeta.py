from patch_lib import mcmeta

TYPE = 'json'

# 26.1 snapshot-11 ~ 26.3
DATA_FORMAT_MIN = [100, 0]
DATA_FORMAT_MAX = [121, 0]

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
    {
        'directory': '26_3_overworld',    # 26.3 snapshot-10 ~ 26.3
        'min_format': [118, 0],
        'max_format': [121, 0],
    },
    {
        'directory': '26_3_nether',    # 26.3 snapshot-10 ~ 26.3
        'min_format': [118, 0],
        'max_format': [121, 0],
    },
    {
        'directory': '26_3_loot',    # 26.3 pre-1 ~ 26.3
        'min_format': [119, 0],
        'max_format': [121, 0],
    },
]

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(
    min_format=DATA_FORMAT_MIN,
    max_format=DATA_FORMAT_MAX,
    overlays=OVERLAYS,
)

