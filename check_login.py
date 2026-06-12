import asyncio, asyncpg, os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv('backend/.env')
url = os.getenv('DATABASE_URL','').replace('postgresql+asyncpg://','postgresql://')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test():
    conn = await asyncpg.connect(url)
    row = await conn.fetchrow(
        'SELECT id, username, hashed_password, role, distributor_id FROM users WHERE email=$1',
        'rahul.sharma@marutisuzuki.com'
    )
    if not row:
        print("USER NOT FOUND IN DATABASE")
    else:
        print("Found user:", dict(row))
        ok = pwd_context.verify('AdminPass@123', row['hashed_password'])
        print("Password OK:", ok)
    await conn.close()

asyncio.run(test())
