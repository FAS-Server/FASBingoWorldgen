from patch_lib import mcmeta

TYPE = 'json'

# 1.20 ~ 1.20.6: data format 15 (1.20, 1.20.1), 18 (1.20.2), 26 (1.20.3,
# 1.20.4) and 41 (1.20.5, 1.20.6). Every target file has the same content
# across the series, so one pack covers it: 1.20.2 and later read
# `supported_formats`, while 1.20 and 1.20.1 read `pack_format` only and
# ignore the extra field.
PACK_FORMAT = 15
SUPPORTED_FORMATS = {'min_inclusive': 15, 'max_inclusive': 41}

# The description lives in common/pack.mcmeta.
reference_file, process_single = mcmeta.make(
    pack_format=PACK_FORMAT,
    supported_formats=SUPPORTED_FORMATS,
)
