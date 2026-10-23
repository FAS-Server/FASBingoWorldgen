from patch_lib import mcmeta

TYPE = 'json'

# 1.18 ~ 1.18.2
PACK_FORMAT = 9

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(pack_format=PACK_FORMAT)
