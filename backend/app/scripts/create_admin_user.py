from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from app.core.security import hash_password
from app.db.session import AsyncSessionFactory
from app.models.enums import AdminRole
from app.repositories.admin_users import create_admin_user, get_by_email


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an admin/resolver user for admin API.")
    parser.add_argument("--email", required=True, help="Admin email.")
    parser.add_argument(
        "--role",
        choices=[AdminRole.ADMIN.value, AdminRole.RESOLVER.value],
        default=AdminRole.ADMIN.value,
        help="Admin role.",
    )
    parser.add_argument("--zone", default=None, help="Resolver zone (required for resolver).")
    parser.add_argument("--password", default=None, help="Password (if omitted, interactive prompt).")
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    email = args.email.strip().lower()
    role = AdminRole(args.role)
    zone = args.zone.strip() if isinstance(args.zone, str) and args.zone.strip() else None

    if role == AdminRole.RESOLVER and not zone:
        print("ERROR: --zone is required for resolver role.", file=sys.stderr)
        return 1

    password = args.password
    if not password:
        password = getpass.getpass("Admin password: ")
    if not password:
        print("ERROR: Password cannot be empty.", file=sys.stderr)
        return 1

    password_hash = hash_password(password)

    async with AsyncSessionFactory() as session:
        existing = await get_by_email(session, email)
        if existing is not None:
            print(f"ERROR: Admin user with email '{email}' already exists.", file=sys.stderr)
            return 1

        admin_user = await create_admin_user(
            session,
            email=email,
            password_hash=password_hash,
            role=role,
            zone=zone,
        )
        await session.commit()
        print(
            f"Created admin user id={admin_user.id} email={admin_user.email} "
            f"role={admin_user.role.value} zone={admin_user.zone}"
        )
        return 0


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
