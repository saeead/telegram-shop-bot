import os
from decimal import Decimal

import pytest

from app.config.settings import Settings
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType
from app.infrastructure.database import create_engine, create_session_factory
from app.infrastructure.product_repository import SqlAlchemyProductRepository


def make_product() -> Product:
    return Product(
        product_code="P-INTEGRATION-TEST",
        name="Integration Product",
        price=Decimal("1000"),
        files=[
            ProductFile(
                telegram_file_id="file-1",
                telegram_message_id=987654321,
                telegram_chat_id=-100123,
                file_type=ProductFileType.IMAGE,
                role=ProductFileRole.PREVIEW,
                original_filename=None,
                mime_type="image/jpeg",
                size=100,
            ),
            ProductFile(
                telegram_file_id="file-2",
                telegram_message_id=987654322,
                telegram_chat_id=-100123,
                file_type=ProductFileType.DOCUMENT,
                role=ProductFileRole.MAIN,
                original_filename="model.stl",
                mime_type="application/octet-stream",
                size=200,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_product_persistence_round_trip() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not configured for integration tests")

    settings = Settings(telegram_bot_token="integration-test-token", database_url=url)
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    product = make_product()
    try:
        async with session_factory() as session:
            repository = SqlAlchemyProductRepository(session)
            await repository.add(product)
            await repository.commit()
            loaded = await repository.get_by_code(product.product_code)
            assert loaded is not None
            assert loaded.name == product.name
            assert len(loaded.previews) == 1
            assert len(loaded.main_files) == 1
            await session.delete(await session.get(__import__("app.infrastructure.models", fromlist=["ProductModel"]).ProductModel, product.id))
            await session.commit()
    finally:
        await engine.dispose()
