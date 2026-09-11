import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.store_ports import AuditEntry, StorePublication
from app.config.settings import Settings
from app.domain.product import Product, ProductFile, ProductFileRole, ProductFileType, ProductStatus
from app.infrastructure.database import create_engine, create_session_factory
from app.infrastructure.product_repository import SqlAlchemyProductRepository


def make_product() -> Product:
    return Product(
        product_code=f"P-STORE-{uuid4().hex[:8].upper()}",
        name="Store Product",
        price=Decimal(1000),
        files=[
            ProductFile("preview", 1001, -100123, ProductFileType.IMAGE, ProductFileRole.PREVIEW, None, "image/jpeg", 10),
            ProductFile("main", 1002, -100123, ProductFileType.ARCHIVE, ProductFileRole.MAIN, "model.zip", "application/zip", 20),
        ],
    )


@pytest.mark.asyncio
async def test_store_publication_and_audit_round_trip() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not configured for integration tests")
    settings = Settings(telegram_bot_token="integration-test-token", database_url=url)
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    product = make_product()
    product.mark_ready()
    product.mark_published()
    try:
        async with session_factory() as session:
            repository = SqlAlchemyProductRepository(session)
            await repository.add(product)
            await repository.commit()
            publication = StorePublication(product.id, -100999, (20, 21), 22)
            await repository.save_publication(publication)
            await repository.save_audit(
                AuditEntry(42, "publish", "product", str(product.id), datetime.now(UTC), {"test": True})
            )
            await repository.commit()
            loaded = await repository.get_publication(product.id)
            assert loaded == publication
            await session.rollback()
    finally:
        await engine.dispose()
