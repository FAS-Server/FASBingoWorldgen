# =============================================================================
# Build settings
#
# This is the only project-specific configuration the build framework needs.
# Fill in the values below and add one constant per supported MC version.
# =============================================================================

# Directory that holds the generated packs (usually git-ignored).
BUILD_PATH = 'build/'

# Directory that holds vanilla source files shared by the patchers.
COMMON_PATH = 'common/'

# Keyword a patcher uses to reference the version currently being built.
SAME_VERSION = 'MC_0'

# Files copied into the root of every generated pack.
# Paths are relative to the project root. For example:
#   EXTRA_FILE = ['README.md', 'LICENSE']
EXTRA_FILE = ['README.md', 'LICENSE']

# Files inside a version source directory that must never be treated as static
# resources. Paths are relative to the version source root.
EXCLUDE_FILE = ['spyglass.json']


# Datapack release version, substituted into every pack name via {version}.
PROJECT_VERSION = '2.0.0'


# -----------------------------------------------------------------------------
# Supported MC versions
# -----------------------------------------------------------------------------
# One constant per supported MC version. The constant name is the id a patcher
# uses when it references another version, so keep the MC_ prefix.
#
# Build order is the declaration order below, therefore a version may only
# reference versions declared BEFORE it.
#
#   'path'    : version source directory, relative to the project root.
#   'name'    : output file name; {version} is filled from the config itself.
#   'version' : datapack release version written into this pack.
#
# Name a version after the FIRST MC version it supports. When a later MC
# version is compatible with the same sources, no rename is needed.
#
# Declared oldest first, because a version may only reference versions
# declared before it.

MC_1_16_5 = {'path': '1_16_5/', 'name': 'FASBingoWorldgen_1.16.5_{version}', 'version': PROJECT_VERSION}
MC_1_17_1 = {'path': '1_17_1/', 'name': 'FASBingoWorldgen_1.17.1_{version}', 'version': PROJECT_VERSION}
MC_1_18_2 = {'path': '1_18_2/', 'name': 'FASBingoWorldgen_1.18.2_{version}', 'version': PROJECT_VERSION}
MC_1_19 = {'path': '1_19/', 'name': 'FASBingoWorldgen_1.19_{version}', 'version': PROJECT_VERSION}
MC_1_20 = {'path': '1_20/', 'name': 'FASBingoWorldgen_1.20_{version}', 'version': PROJECT_VERSION}
MC_1_21 = {'path': '1_21/', 'name': 'FASBingoWorldgen_1.21_{version}', 'version': PROJECT_VERSION}
MC_26_1 = {'path': '26_1/', 'name': 'FASBingoWorldgen_26.1_{version}', 'version': PROJECT_VERSION}


def __collect_constant() -> dict:
    ret = {}
    global_temp = globals().copy()
    for key in global_temp:
        if key.startswith('MC_'):
            ret[key] = global_temp[key]
    # ret.pop(*['COMMON_PATH', 'BUILD_PATH', 'SAME_VERSION', 'EXTRA_FILE', 'EXCLUDE_FILE'])
    return ret

__VERSION_CONFIG = __collect_constant()
