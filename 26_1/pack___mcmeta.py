from patch_lib import mcmeta

TYPE = 'json'

# 26.1 through 26.1.2 all declare data format 101.1 (data_major 101,
# data_minor 1) and ship identical loot_table/ and worldgen/ data, so one
# source tree covers the whole 26.1 series. Widen the range only after
# diffing a newer version's vanilla files against these sources.
DATA_FORMAT_MIN = [101, 1]
DATA_FORMAT_MAX = [101, 1]

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(
    min_format=DATA_FORMAT_MIN,
    max_format=DATA_FORMAT_MAX,
)

