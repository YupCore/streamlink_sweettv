"""
$description Ukrainian OTT TV service owned by SWEET.TV Group offering live TV channels and videos on demand.
$url sweet.tv
$type live
$account Required for subscription channels
"""

import re
import time
import uuid

import requests.cookies

from streamlink.logger import getLogger
from streamlink.plugin import Plugin, pluginmatcher
from streamlink.plugin.api import useragents, validate
from streamlink.stream.hls import HLSStream

log = getLogger(__name__)


@pluginmatcher(
    re.compile(
        r"https?://(?:www\.)?sweet\.tv/(?:[a-z]{2}(?:-[a-z]{2})?/)?(?:tv|free-tv)/(?P<channel_id>\d+)(?:-[\w-]+)?/?(?:\?.*)?$",
    ),
)
class SweetTV(Plugin):
    _API_OPEN_STREAM = "https://api.sweet.tv/TvService/OpenStream.json"
    _API_TOKEN = "https://api.sweet.tv/AuthenticationService/Token.json"

    _SCHEMA_TOKEN = validate.Schema(
        validate.parse_json(),
        validate.any(
            {
                "access_token": str,
                validate.optional("expires_in"): int,
            },
            {
                "code": int,
                "message": str,
            },
        ),
    )

    _SCHEMA = validate.Schema(
        validate.parse_json(),
        validate.any(
            {
                "result": str,
                validate.optional("url"): validate.none_or_all(validate.url()),
                validate.optional("drm_type"): validate.none_or_all(str),
                validate.optional("license_server"): validate.none_or_all(str),
            },
            {
                "code": int,
                "message": str,
            },
        ),
    )

    def _get_cookie(self, name: str) -> str | None:
        for cookie in self.session.http.cookies:
            if cookie.name == name:
                if cookie.domain == "sweet.tv" or cookie.domain.endswith(".sweet.tv"):
                    return cookie.value

        return None

    def _refresh_access_token(self, refresh_token: str, device_uuid: str) -> str | None:
        log.debug("Refreshing Sweet.tv access token...")
        res = self.session.http.post(
            self._API_TOKEN,
            headers={
                "User-Agent": useragents.CHROME,
                "X-Device": "DT_Web_Browser",
            },
            json={
                "refresh_token": refresh_token,
                "device": {
                    "type": "DT_Web_Browser",
                    "application": {
                        "type": "AT_SWEET_TV_Player",
                    },
                    "uuid": device_uuid,
                },
            },
            acceptable_status=(200, 400, 401),
            schema=self._SCHEMA_TOKEN,
        )

        if "message" in res:
            log.warning(f"Failed to refresh Sweet.tv access token: {res['message']}")
            return None

        access_token = res.get("access_token")
        if access_token:
            expires_in = res.get("expires_in") or 10800
            cookie = requests.cookies.create_cookie(
                name="access_token",
                value=access_token,
                domain="sweet.tv",
                path="/",
                expires=int(time.time()) + expires_in,
                rest={"HttpOnly": None},
            )
            self.session.http.cookies.set_cookie(cookie)
            self.save_cookies(lambda c: c.name == "access_token")
            return access_token

        return None

    def _get_token(self, device_uuid: str) -> str | None:
        access_token = self._get_cookie("access_token")
        if access_token:
            return access_token
        
        log.warning(f"access_token cookie not found, refreshing token" )

        refresh_token = self._get_cookie("refresh_token")
        if refresh_token:
            return self._refresh_access_token(refresh_token, device_uuid)

        log.warning(f"refresh_token cookie not found, no auth possible" )
        return None

    def _get_streams(self):
        channel_id = int(self.match["channel_id"])

        device_uuid = self.cache.get("device_uuid")
        if not device_uuid:
            device_uuid = str(uuid.uuid4())
            self.cache.set("device_uuid", device_uuid)

        headers = {
            "User-Agent": useragents.CHROME,
            "X-Device": "DT_Web_Browser",
        }

        token = self._get_token(device_uuid)
        if token:
            headers["Authorization"] = f"Bearer {token}"

        res = self.session.http.post(
            self._API_OPEN_STREAM,
            headers=headers,
            json={
                "channel_id": channel_id,
                "accept_scheme": ["HTTP_HLS"],
                "multistream": True,
                "uuid": device_uuid,
            },
            acceptable_status=(200, 401, 403),
            schema=self._SCHEMA,
        )

        if "message" in res:
            log.error(f"Sweet.tv API error: {res['message']}")
            return

        result = res.get("result")
        if result == "NoAuth":
            log.error("Authentication required for this channel. Please specify account cookies.")
            return
        if result == "UnavailableInSubscription":
            log.error("This channel is not included in your current subscription.")
            return
        if result == "Deny":
            log.error("Access denied by Sweet.tv (check region or subscription).")
            return
        if result == "NeedConfirmAge":
            log.error("This channel requires age confirmation.")
            return
        if result != "OK":
            log.error(f"Failed to open stream: {result}")
            return

        if res.get("drm_type") or res.get("license_server"):
            log.error(f"This stream is protected by DRM ({res.get('drm_type') or 'DRM'}) and cannot be played.")
            return

        stream_url = res.get("url")
        if not stream_url:
            log.error("No stream URL found in API response.")
            return

        self.id = str(channel_id)

        return HLSStream.parse_variant_playlist(
            self.session,
            stream_url,
            headers={"Referer": "https://sweet.tv/"},
        )


__plugin__ = SweetTV
