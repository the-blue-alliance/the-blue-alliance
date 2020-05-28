import json

from api.apiv3.api_base_controller import ApiBaseController
from consts.media_tag import MediaTag


class ApiMediaTagsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self):
        self._track_call_defer('media/tags', 'media/tags')

    def _render(self):
        tagData = zip(MediaTag.tag_names, MediaTag.tag_url_names)

        mediaTags = []
        for index in MediaTag.tag_names:
            mediaTags.append({
                'name': MediaTag.tag_names[index],
                'code': MediaTag.tag_url_names[index]
            })

        return json.dumps(mediaTags, ensure_ascii=True, indent=2, sort_keys=False)
