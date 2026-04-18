"""Marketplace management routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Marketplace

marketplaces_bp = Blueprint('marketplaces', __name__)


@marketplaces_bp.route('/')
@login_required
def list_marketplaces():
    mps = Marketplace.query.filter_by(user_id=current_user.id).order_by(Marketplace.priority.desc()).all()
    return render_template('marketplaces/list.html', marketplaces=mps)


@marketplaces_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_marketplace():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().lower().replace(' ', '_')
        color = request.form.get('color', '#6366f1')
        priority = int(request.form.get('priority', 1))

        if not name or not code:
            flash('Name and code are required.', 'error')
            return render_template('marketplaces/add.html')

        existing = Marketplace.query.filter_by(code=code, user_id=current_user.id).first()
        if existing:
            flash(f'Marketplace with code "{code}" already exists.', 'error')
            return render_template('marketplaces/add.html')

        mp = Marketplace(name=name, code=code, color=color, priority=priority, user_id=current_user.id)
        db.session.add(mp)
        db.session.commit()
        flash(f'{name} marketplace added!', 'success')
        return redirect(url_for('marketplaces.list_marketplaces'))

    return render_template('marketplaces/add.html')


@marketplaces_bp.route('/<int:mp_id>/edit', methods=['POST'])
@login_required
def edit_marketplace(mp_id):
    mp = Marketplace.query.get_or_404(mp_id)
    if mp.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('marketplaces.list_marketplaces'))

    mp.name = request.form.get('name', mp.name).strip()
    mp.color = request.form.get('color', mp.color)
    mp.priority = int(request.form.get('priority', mp.priority))
    db.session.commit()
    flash(f'{mp.name} updated.', 'success')
    return redirect(url_for('marketplaces.list_marketplaces'))


@marketplaces_bp.route('/<int:mp_id>/toggle', methods=['POST'])
@login_required
def toggle_marketplace(mp_id):
    mp = Marketplace.query.get_or_404(mp_id)
    if mp.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('marketplaces.list_marketplaces'))

    mp.is_active = not mp.is_active
    db.session.commit()
    status = 'activated' if mp.is_active else 'deactivated'
    flash(f'{mp.name} {status}.', 'success')
    return redirect(url_for('marketplaces.list_marketplaces'))
