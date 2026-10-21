from patch_lib import mcmeta

TYPE = 'json'

# 1.16.2 ~ 1.16.5
PACK_FORMAT = 6

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(pack_format=PACK_FORMAT)
