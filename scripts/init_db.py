import asyncio

from app.database import create_db_and_tables, datbase_engine


async def main():
    await create_db_and_tables(datbase_engine)
    print("Database tables created successfully")


if __name__ == "__main__":
    asyncio.run(main())
