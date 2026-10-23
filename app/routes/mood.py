from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import MoodEntry, SafetyLog
from datetime import datetime, timedelta
from collections import Counter

mood_bp = Blueprint('mood', __name__)

MOOD_CATEGORIES = ['happy', 'calm', 'anxious', 'sad', 'angry', 'stressed', 'neutral']
NEGATIVE_MOODS = ['anxious', 'sad', 'angry', 'stressed']


@mood_bp.route('/')
@login_required
def index():
    period = request.args.get('period', '7')
    days = int(period) if period in ('7', '30', '90') else 7
    since = datetime.utcnow() - timedelta(days=days)

    entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= since
    ).order_by(MoodEntry.created_at.desc()).all()

    # Trend analysis
    trend = None
    if len(entries) >= 7:
        mood_counts = Counter(e.mood for e in entries)
        total = len(entries)
        most_common = mood_counts.most_common(1)[0]
        distribution = {mood: round(count / total * 100, 1)
                        for mood, count in mood_counts.items()}

        # Check for consecutive patterns
        consecutive = []
        for i in range(len(entries) - 2):
            if entries[i].mood == entries[i+1].mood == entries[i+2].mood:
                consecutive.append(entries[i].mood)

        trend = {
            'most_frequent': most_common[0],
            'most_frequent_count': most_common[1],
            'distribution': distribution,
            'consecutive_patterns': list(set(consecutive)),
            'total_entries': total
        }

    # Check for sustained negative trend (5 consecutive negative entries)
    negative_alert = False
    if len(entries) >= 5:
        recent_five = entries[:5]
        if all(e.mood in NEGATIVE_MOODS for e in recent_five):
            negative_alert = True

    return render_template('mood/index.html',
                           entries=entries,
                           period=days,
                           trend=trend,
                           negative_alert=negative_alert,
                           mood_categories=MOOD_CATEGORIES)


@mood_bp.route('/log', methods=['GET', 'POST'])
@login_required
def log():
    if request.method == 'POST':
        mood = request.form.get('mood')
        note = request.form.get('note', '').strip()

        if mood not in MOOD_CATEGORIES:
            flash('Please select a valid mood category.', 'danger')
            return render_template('mood/log.html', mood_categories=MOOD_CATEGORIES)

        if len(note) > 500:
            flash('Note must be 500 characters or less.', 'danger')
            return render_template('mood/log.html', mood_categories=MOOD_CATEGORIES)

        entry = MoodEntry(user_id=current_user.id, mood=mood, note=note if note else None)
        db.session.add(entry)
        db.session.commit()

        flash('Mood logged successfully!', 'success')
        
        # Store the mood in session for chat to access
        from flask import session as flask_session
        flask_session['last_mood'] = mood
        
        # Get recent entries for index page
        recent_entries = MoodEntry.query.filter_by(user_id=current_user.id)\
            .order_by(MoodEntry.created_at.desc()).limit(10).all()
        
        return render_template('mood/index.html',
                           entries=recent_entries,
                           period=7,
                           trend=None,
                           negative_alert=False,
                           mood_categories=MOOD_CATEGORIES,
                           just_logged=mood)

    return render_template('mood/log.html', mood_categories=MOOD_CATEGORIES)