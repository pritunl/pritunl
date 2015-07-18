from pritunl.settings.settings import Settings

import sys

sys.modules[__name__] = Settings()
