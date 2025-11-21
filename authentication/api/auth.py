from typing import Annotated

from fastapi import Depends, Request
from starlette.responses import Response

from ..controllers.auth import AuthController
from ..core.routing import AppRouter, post
from ..schemas.auth import EmailLogin, EmailRegister


class AuthRouter(AppRouter):
    controller: Annotated[AuthController, Depends()]

    @post("/login")
    async def login(self, login: EmailLogin, request: Request, response: Response):
        return await self.controller.login(login, request, response)

    @post("/login/social")
    async def social_login(self):
        return await self.controller.social_login()

    @post("/logout")
    async def logout(self):
        return await self.controller.logout()

    @post("/register")
    async def register(
        self, register_data: EmailRegister, request: Request, response: Response
    ):
        return await self.controller.register(register_data, request, response)

    @post("/refresh-token")
    async def refresh_token(self):
        return await self.controller.refresh_token()

    @post("/verify-email")
    async def verify_email(self):
        return await self.controller.verify_email()

    @post("/send-verification-email")
    async def send_verification_email(self):
        return await self.controller.send_verification_email()

    @post("/forgot-password")
    async def forgot_password(self):
        return await self.controller.forgot_password()

    @post("/reset-password")
    async def reset_password(self):
        return await self.controller.reset_password()


router = AuthRouter(prefix="/auth", tags=["Authentication"])
