"""Sales recording routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Product, Marketplace, MarketplaceInventory, Sale
from services.sales_service import record_sale, InsufficientStockError
from datetime import datetime, date, timedelta

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/record', methods=['GET', 'POST'])
@login_required
def record():
    marketplaces = Marketplace.query.filter_by(user_id=current_user.id, is_active=True).all()
    products = Product.query.filter_by(user_id=current_user.id, is_active=True).order_by(Product.name).all()

    if request.method == 'POST':
        product_id = int(request.form.get('product_id', 0))
        marketplace_id = int(request.form.get('marketplace_id', 0))
        quantity = int(request.form.get('quantity', 0))
        sale_price = float(request.form.get('sale_price', 0))

        if not product_id or not marketplace_id or quantity <= 0:
            flash('All fields are required.', 'error')
            return render_template('sales/record.html', marketplaces=marketplaces, products=products)

        try:
            sale = record_sale(product_id, marketplace_id, quantity, sale_price, current_user.id)
            mi = MarketplaceInventory.query.filter_by(product_id=product_id, marketplace_id=marketplace_id).first()
            mp = Marketplace.query.get(marketplace_id)
            flash(f'Sale recorded! {quantity} units on {mp.name}. Remaining: {mi.allocated_qty}', 'success')
            return redirect(url_for('sales.record'))
        except InsufficientStockError as e:
            flash(str(e), 'error')
        except ValueError as e:
            flash(str(e), 'error')

    return render_template('sales/record.html', marketplaces=marketplaces, products=products)


@sales_bp.route('/history')
@login_required
def history():
    products = Product.query.filter_by(user_id=current_user.id, is_active=True).all()
    product_ids = [p.id for p in products]
    marketplaces = Marketplace.query.filter_by(user_id=current_user.id, is_active=True).all()

    mp_filter = request.args.get('marketplace_id', type=int)
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.now() - timedelta(days=days)

    query = Sale.query.filter(
        Sale.product_id.in_(product_ids),
        Sale.sale_date >= cutoff,
    )
    if mp_filter:
        query = query.filter(Sale.marketplace_id == mp_filter)

    sales = query.order_by(Sale.sale_date.desc()).limit(200).all()
    return render_template('sales/history.html', sales=sales, marketplaces=marketplaces,
                           selected_mp=mp_filter, days=days)


@sales_bp.route('/api/product-inventory/<int:product_id>')
@login_required
def product_inventory(product_id):
    """API: Get marketplace inventory for a product (used by sale form AJAX)."""
    mis = MarketplaceInventory.query.filter_by(product_id=product_id, is_listed=True).all()
    result = []
    for mi in mis:
        mp = Marketplace.query.get(mi.marketplace_id)
        if mp and mp.is_active:
            result.append({
                'marketplace_id': mi.marketplace_id,
                'marketplace_name': mp.name,
                'color': mp.color,
                'allocated_qty': mi.allocated_qty,
                'selling_price': mi.selling_price,
            })
    return jsonify(result)
