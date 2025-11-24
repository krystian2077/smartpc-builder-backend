from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import csv
import io
from datetime import datetime

from app.core.database import get_db
from app.models.product import Product, ProductType, ProductSegment
from app.models.inquiry import Inquiry
from app.schemas.product import ProductCreate

router = APIRouter(prefix="/import-export", tags=["import-export"])


@router.post("/products/import")
async def import_products_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Import products from CSV file"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    csv_content = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    
    imported = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):
        try:
            # Parse CSV row to ProductCreate
            product_data = {
                "name": row.get("name", ""),
                "type": ProductType(row.get("type", "").lower()),
                "segment": ProductSegment(row.get("segment", "").lower()) if row.get("segment") else None,
                "price": float(row.get("price", 0)),
                "currency": row.get("currency", "PLN"),
                "specifications": eval(row.get("specifications", "{}")) if row.get("specifications") else {},
                "compatibility": eval(row.get("compatibility", "{}")) if row.get("compatibility") else None,
                "brand": row.get("brand"),
                "model": row.get("model"),
                "image_url": row.get("image_url"),
                "description": row.get("description"),
                "in_stock": row.get("in_stock", "true").lower() == "true",
                "performance_score": float(row.get("performance_score", 0)) if row.get("performance_score") else None,
                "gaming_score": float(row.get("gaming_score", 0)) if row.get("gaming_score") else None,
                "productivity_score": float(row.get("productivity_score", 0)) if row.get("productivity_score") else None,
            }
            
            product = ProductCreate(**product_data)
            
            # Create product in DB
            db_product = Product(
                **product.model_dump(),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            db.add(db_product)
            imported += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    await db.commit()
    
    return {
        "imported": imported,
        "errors": errors,
        "total_rows": row_num - 1,
    }


@router.get("/products/export")
async def export_products_csv(
    type: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Export products to CSV"""
    query = select(Product)
    if type:
        query = query.where(Product.type == ProductType(type))
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "id", "name", "type", "segment", "price", "currency",
        "specifications", "compatibility", "brand", "model",
        "image_url", "description", "in_stock",
        "performance_score", "gaming_score", "productivity_score",
    ])
    
    # Write data
    for product in products:
        writer.writerow([
            str(product.id),
            product.name,
            product.type.value,
            product.segment.value if product.segment else "",
            product.price,
            product.currency,
            str(product.specifications),
            str(product.compatibility) if product.compatibility else "",
            product.brand or "",
            product.model or "",
            product.image_url or "",
            product.description or "",
            product.in_stock,
            product.performance_score or "",
            product.gaming_score or "",
            product.productivity_score or "",
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_export.csv"},
    )


@router.get("/inquiries/export")
async def export_inquiries_csv(
    db: AsyncSession = Depends(get_db),
):
    """Export inquiries to CSV"""
    result = await db.execute(select(Inquiry).order_by(Inquiry.created_at.desc()))
    inquiries = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "id", "reference_number", "first_name", "last_name", "email",
        "phone", "company", "inquiry_type", "source", "status",
        "created_at", "message",
    ])
    
    # Write data
    for inquiry in inquiries:
        writer.writerow([
            str(inquiry.id),
            inquiry.reference_number,
            inquiry.first_name,
            inquiry.last_name,
            inquiry.email,
            inquiry.phone or "",
            inquiry.company or "",
            inquiry.inquiry_type.value,
            inquiry.source.value,
            inquiry.status,
            inquiry.created_at,
            inquiry.message or "",
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inquiries_export.csv"},
    )

