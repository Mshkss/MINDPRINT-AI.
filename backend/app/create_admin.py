"""Create an admin through an interactive local terminal; never embeds credentials."""

import asyncio
import getpass
from sqlalchemy import select
from app.core.database import Session
from app.core.security import hasher
from app.models import User


async def main():
    email = input("Email администратора: ").strip().lower()
    name = input("Имя: ").strip()
    password = getpass.getpass("Пароль (минимум 12 символов): ")
    if "@" not in email or not name or len(password) < 12:
        raise SystemExit("Проверьте email, имя и длину пароля.")
    async with Session() as db:
        if await db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Пользователь с таким email уже существует.")
        db.add(
            User(
                name=name,
                email=email,
                password_hash=hasher.hash(password),
                role="admin",
            )
        )
        await db.commit()
    print("Администратор создан. Войдите через /login.")


if __name__ == "__main__":
    asyncio.run(main())
