from patch_lib import mcmeta

TYPE = 'json'

# 1.17 ~ 1.17.1
PACK_FORMAT = 7

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(pack_format=PACK_FORMAT)
