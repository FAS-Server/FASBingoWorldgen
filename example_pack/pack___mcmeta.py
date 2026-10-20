from patch_lib import mcmeta

TYPE = 'json'

# pack_format of the MC version this pack targets.
PACK_FORMAT = 1

# The example pack replaces the shared description of common/pack.mcmeta.
DESCRIPTION = 'Example datapack built with Youmiel/DatapackDevToolkit'

# reference_file and process_single come from the shared helper; the per-version
# data stays here. A version whose pack.mcmeta also needs supported_formats or
# overlays passes them as extra arguments, see patch_lib/mcmeta.py.
reference_file, process_single = mcmeta.make(PACK_FORMAT, description=DESCRIPTION)
