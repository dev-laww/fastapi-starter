from typing import Annotated

from fastapi import Depends, Request
from starlette.responses import Response

from ..controllers.auth import AuthController
from ..core.routing import AppRouter, post, get
from ..schemas.auth import (
    EmailLogin,
    EmailRegister,
    EmailWithCallback,
    ResetPassword,
    VerifyEmail,
)


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
    async def refresh_token(self, request: Request, response: Response):
        return await self.controller.refresh_token()

    @get("/verify")
    async def verify_email(self, data: VerifyEmail = Depends()):
        return await self.controller.verify_email(data)

    @post("/send-verification")
    async def send_verification_email(self, data: EmailWithCallback):
        return await self.controller.send_verification_email(data)

    @post("/forgot")
    async def forgot_password(self, data: EmailWithCallback):
        return await self.controller.forgot_password(data)

    @post("/reset")
    async def reset_password(self, data: ResetPassword):
        return await self.controller.reset_password(data)


router = AuthRouter(prefix="/auth", tags=["Authentication"])
