from patch_lib import mcmeta

TYPE = 'json'

# 1.19 ~ 1.19.3
PACK_FORMAT = 10

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(pack_format=PACK_FORMAT)
