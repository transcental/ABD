import binascii
import os
from typing import Optional

from aiohttp import ClientResponse
from aiohttp import ClientSession


BASE = "https://api.monzo.com"


class MonzoHandler:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.state: Optional[str] = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.session: ClientSession

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_in: Optional[int] = None
        self.user_id: Optional[str] = None

    def generate_state(self) -> str:
        signature = binascii.hexlify(os.urandom(32))
        state = signature.decode("utf-8")
        self.state = state
        return state

    def generate_monzo_url(self) -> str:
        self.generate_state()
        return f"https://auth.monzo.com/?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&state={self.state}"

    async def post(self, path: str, data: dict = {}) -> ClientResponse:
        data["Authorization"] = f"Bearer {self.access_token}"
        async with self.session.post(f"{BASE}/{path}", data=data) as res:
            if res.status == 401:
                await self.refresh_access_token()
                data["Authorization"] = f"Bearer {self.access_token}"
                async with self.session.post(f"{BASE}/{path}", data=data) as res:
                    return res
            return res

    async def get(self, path: str, headers: dict = {}) -> ClientResponse:
        headers["Authorization"] = f"Bearer {self.access_token}"
        async with self.session.get(f"{BASE}/{path}", headers=headers) as res:
            if res.status == 401:
                await self.refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                async with self.session.get(f"{BASE}/{path}", headers=headers) as res:
                    return res
            return res

    async def put(self, path: str, data: dict = {}) -> ClientResponse:
        data["Authorization"] = f"Bearer {self.access_token}"
        async with self.session.put(f"{BASE}/{path}", data=data) as res:
            if res.status == 401:
                await self.refresh_access_token()
                data["Authorization"] = f"Bearer {self.access_token}"
                async with self.session.put(f"{BASE}/{path}", data=data) as res:
                    return res
            return res

    async def delete(self, path: str, data: dict = {}) -> ClientResponse:
        data["Authorization"] = f"Bearer {self.access_token}"
        async with self.session.delete(f"{BASE}/{path}", data=data) as res:
            if res.status == 401:
                await self.refresh_access_token()
                data["Authorization"] = f"Bearer {self.access_token}"
                async with self.session.delete(f"{BASE}/{path}", data=data) as res:
                    return res
            return res

    async def exchange_code(self, code: str) -> bool:
        res = await self.post(
            "oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": code,
            },
        )
        if res.status != 200:
            return False
        res = await res.json()
        self.access_token = res.get("access_token")
        self.refresh_token = res.get("refresh_token")
        self.expires_in = res.get("expires_in")
        self.user_id = res.get("user_id")
        return True

    async def refresh_access_token(self) -> bool:
        res = await self.post(
            "oauth2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
        )
        if res.status != 200:
            return False
        res = await res.json()
        self.access_token = res.get("access_token")
        self.refresh_token = res.get("refresh_token")
        self.expires_in = res.get("expires_in")
        self.user_id = res.get("user_id")
        return True

    async def logout(self) -> bool:
        res = await self.post("oauth2/logout")
        return res.status == 200

    async def test_auth(self) -> bool:
        res = await self.get("ping/whoami")
        return res.status == 200
