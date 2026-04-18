"""CSV parsing and validation service."""

import pandas as pd
from models import db, Product, MarketplaceInventory, Marketplace


REQUIRED_COLUMNS = ['sku', 'name', 'cost_price', 'quantity']
OPTIONAL_COLUMNS = ['category']


def parse_csv(file_storage):
    """Parse an uploaded CSV file into a DataFrame."""
    try:
        df = pd.read_csv(file_storage)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        return df
    except Exception as e:
        raise ValueError(f'Could not parse CSV: {str(e)}')


def validate_csv(df):
    """Validate that required columns exist and data is clean."""
    errors = []

    # Check required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors

    # Check for empty SKUs
    if df['sku'].isna().any() or (df['sku'].astype(str).str.strip() == '').any():
        errors.append('Some rows have empty SKU values')

    # Check numeric columns
    for col in ['cost_price', 'quantity']:
        try:
            pd.to_numeric(df[col], errors='raise')
        except (ValueError, TypeError):
            errors.append(f'Column "{col}" contains non-numeric values')

    # Check for duplicate SKUs within file
    dupes = df[df['sku'].duplicated(keep=False)]
    if not dupes.empty:
        errors.append(f'Duplicate SKUs found in file: {dupes["sku"].unique().tolist()[:5]}')

    return len(errors) == 0, errors


def import_csv(df, user_id):
    """Import products from DataFrame. Upserts by SKU."""
    imported = 0
    updated = 0
    errors = []

    # Detect marketplace price columns
    marketplaces = Marketplace.query.filter_by(user_id=user_id, is_active=True).all()
    mp_price_cols = {}
    for mp in marketplaces:
        col_name = f'{mp.code}_price'
        if col_name in df.columns:
            mp_price_cols[mp] = col_name

    for idx, row in df.iterrows():
        try:
            sku = str(row['sku']).strip()
            name = str(row['name']).strip()
            cost_price = float(row['cost_price'])
            quantity = int(float(row['quantity']))
            category = str(row.get('category', 'General')).strip() if 'category' in row else 'General'

            if not sku or not name:
                errors.append(f'Row {idx + 2}: Empty SKU or name')
                continue

            # Upsert product
            product = Product.query.filter_by(sku=sku, user_id=user_id).first()
            if product:
                product.name = name
                product.cost_price = cost_price
                product.total_warehouse_qty = quantity
                product.category = category
                updated += 1
            else:
                product = Product(
                    sku=sku,
                    name=name,
                    category=category,
                    cost_price=cost_price,
                    total_warehouse_qty=quantity,
                    user_id=user_id,
                )
                db.session.add(product)
                db.session.flush()
                imported += 1

            # Handle marketplace prices
            for mp, col in mp_price_cols.items():
                try:
                    price = float(row[col])
                    mi = MarketplaceInventory.query.filter_by(
                        product_id=product.id,
                        marketplace_id=mp.id,
                    ).first()
                    if mi:
                        mi.selling_price = price
                    else:
                        mi = MarketplaceInventory(
                            product_id=product.id,
                            marketplace_id=mp.id,
                            selling_price=price,
                            allocated_qty=0,
                            is_listed=True,
                        )
                        db.session.add(mi)
                except (ValueError, TypeError):
                    pass  # Skip invalid prices

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return imported, updated, errors
