from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Trade

trading_bp = Blueprint('trading', __name__)

EMOTIONS = ['confident', 'fearful', 'greedy', 'calm', 'anxious', 'revenge', 'neutral']


@trading_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    query = Trade.query.filter_by(user_id=current_user.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    trades = query.order_by(Trade.date.desc()).all()

    # Stats
    closed_trades = [t for t in trades if t.status == 'closed']
    total_pnl = sum(t.pnl or 0 for t in closed_trades)
    winning_trades = [t for t in closed_trades if (t.pnl or 0) > 0]
    losing_trades = [t for t in closed_trades if (t.pnl or 0) < 0]
    win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0

    stats = {
        'total_trades': len(closed_trades),
        'total_pnl': total_pnl,
        'winning': len(winning_trades),
        'losing': len(losing_trades),
        'win_rate': round(win_rate, 1),
        'open_trades': len([t for t in trades if t.status == 'open'])
    }

    from datetime import date as date_cls
    today = date_cls.today().strftime('%Y-%m-%d')

    return render_template('trading/index.html',
                           trades=trades,
                           stats=stats,
                           status_filter=status_filter,
                           today=today)


@trading_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            trade_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            trade_date = date.today()

        symbol = request.form.get('symbol', '').strip().upper()
        trade_type = request.form.get('trade_type')
        entry_price = float(request.form.get('entry_price', 0))
        exit_price = request.form.get('exit_price', '').strip()
        quantity = float(request.form.get('quantity', 0))
        stop_loss = request.form.get('stop_loss', '').strip()
        target = request.form.get('target', '').strip()
        status = request.form.get('status', 'open')
        strategy = request.form.get('strategy', '').strip()
        notes = request.form.get('notes', '').strip()
        emotion_before = request.form.get('emotion_before')
        emotion_after = request.form.get('emotion_after')

        if not symbol or not trade_type or entry_price <= 0 or quantity <= 0:
            flash('Please fill in all required fields (symbol, type, entry price, quantity).', 'danger')
            return redirect(url_for('trading.index'))

        # Calculate P&L if trade is closed
        pnl = None
        exit_price_val = None
        if exit_price:
            exit_price_val = float(exit_price)
            if trade_type == 'buy':
                pnl = (exit_price_val - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price_val) * quantity

        trade = Trade(
            user_id=current_user.id,
            date=trade_date,
            symbol=symbol,
            trade_type=trade_type,
            entry_price=entry_price,
            exit_price=exit_price_val,
            quantity=quantity,
            stop_loss=float(stop_loss) if stop_loss else None,
            target=float(target) if target else None,
            status=status,
            pnl=pnl,
            strategy=strategy if strategy else None,
            notes=notes if notes else None,
            emotion_before=emotion_before if emotion_before else None,
            emotion_after=emotion_after if emotion_after else None
        )
        db.session.add(trade)
        db.session.commit()

        flash(f'Trade {symbol} logged successfully!', 'success')
        return redirect(url_for('trading.index'))

    # GET request — just show the main page
    return redirect(url_for('trading.index'))


@trading_bp.route('/edit/<int:trade_id>', methods=['GET', 'POST'])
@login_required
def edit(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if trade.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('trading.index'))

    if request.method == 'POST':
        try:
            trade.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

        trade.symbol = request.form.get('symbol', '').strip().upper()
        trade.trade_type = request.form.get('trade_type')
        trade.entry_price = float(request.form.get('entry_price', 0))
        trade.quantity = float(request.form.get('quantity', 0))
        trade.status = request.form.get('status', 'open')
        trade.strategy = request.form.get('strategy', '').strip() or None
        trade.notes = request.form.get('notes', '').strip() or None
        trade.emotion_before = request.form.get('emotion_before') or None
        trade.emotion_after = request.form.get('emotion_after') or None

        exit_price = request.form.get('exit_price', '').strip()
        stop_loss = request.form.get('stop_loss', '').strip()
        target = request.form.get('target', '').strip()

        trade.exit_price = float(exit_price) if exit_price else None
        trade.stop_loss = float(stop_loss) if stop_loss else None
        trade.target = float(target) if target else None

        # Recalculate P&L
        if trade.exit_price:
            if trade.trade_type == 'buy':
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
            else:
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.quantity
        else:
            trade.pnl = None

        db.session.commit()
        flash('Trade updated successfully!', 'success')
        return redirect(url_for('trading.index'))

    return render_template('trading/edit.html', trade=trade, emotions=EMOTIONS)


@trading_bp.route('/delete/<int:trade_id>', methods=['POST'])
@login_required
def delete(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if trade.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('trading.index'))

    db.session.delete(trade)
    db.session.commit()
    flash('Trade deleted.', 'info')
    return redirect(url_for('trading.index'))