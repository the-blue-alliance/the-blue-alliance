#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Client Library for Google Cloud Storage."""

__author__ = "yey@google.com (Ye Yuan)"

# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

#
# from .api_utils import RetryParams
# from .api_utils import set_default_retry_params
# from .cloudstorage_api import *
# from .common import CSFileStat
# from .common import GCSFileStat
# from .common import validate_bucket_name
# from .common import validate_bucket_path
# from .common import validate_file_path
# from .errors import *
# from .storage_api import *

# from cloudstorage import *
# flake8: noqa
from backend.common.storage.clients.cloudstorage.api_utils import RetryParams
from backend.common.storage.clients.cloudstorage.api_utils import (
    set_default_retry_params,
)
from backend.common.storage.clients.cloudstorage.cloudstorage_api import copy2
from backend.common.storage.clients.cloudstorage.cloudstorage_api import delete
from backend.common.storage.clients.cloudstorage.cloudstorage_api import delete_async
from backend.common.storage.clients.cloudstorage.cloudstorage_api import listbucket
from backend.common.storage.clients.cloudstorage.cloudstorage_api import open
from backend.common.storage.clients.cloudstorage.cloudstorage_api import stat
from backend.common.storage.clients.cloudstorage.cloudstorage_api import stat_async
from backend.common.storage.clients.cloudstorage.cloudstorage_api import compose
from backend.common.storage.clients.cloudstorage.cloudstorage_api import get_location
from backend.common.storage.clients.cloudstorage.cloudstorage_api import (
    get_location_async,
)
from backend.common.storage.clients.cloudstorage.cloudstorage_api import (
    get_storage_class,
)
from backend.common.storage.clients.cloudstorage.cloudstorage_api import (
    get_storage_class_async,
)
from backend.common.storage.clients.cloudstorage.common import CSFileStat
from backend.common.storage.clients.cloudstorage.common import GCSFileStat
from backend.common.storage.clients.cloudstorage.common import validate_bucket_name
from backend.common.storage.clients.cloudstorage.common import validate_bucket_path
from backend.common.storage.clients.cloudstorage.common import validate_file_path
from backend.common.storage.clients.cloudstorage.errors import *
from backend.common.storage.clients.cloudstorage.storage_api import *
