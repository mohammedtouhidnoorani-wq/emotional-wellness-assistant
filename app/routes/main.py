from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import MoodEntry, AssessmentResult, ExerciseCompletion
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('main/dashboard.html')
    return render_template('main/landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent mood entries (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_moods = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= week_ago
    ).order_by(MoodEntry.created_at.desc()).all()

    # Get latest assessment
    latest_assessment = AssessmentResult.query.filter_by(
        user_id=current_user.id
    ).order_by(AssessmentResult.created_at.desc()).first()

    # Get exercise completions count
    exercise_count = ExerciseCompletion.query.filter_by(
        user_id=current_user.id
    ).count()

    # Generate recommendations
    recommendations = generate_recommendations(recent_moods, latest_assessment)

    return render_template('main/dashboard.html',
                           recent_moods=recent_moods,
                           latest_assessment=latest_assessment,
                           exercise_count=exercise_count,
                           recommendations=recommendations)


def generate_recommendations(moods, assessment):
    recommendations = []

    if not moods:
        recommendations.append({
            'icon': '📝',
            'text': 'Start by logging your mood to get personalized recommendations.',
            'link': '/mood/log'
        })

    if not assessment:
        recommendations.append({
            'icon': '📋',
            'text': 'Take a wellness assessment to understand your emotional state.',
            'link': '/assessment/'
        })

    if moods:
        negative_moods = [m for m in moods if m.mood in ('anxious', 'sad', 'angry', 'stressed')]
        if len(negative_moods) > len(moods) / 2:
            recommendations.append({
                'icon': '🧘',
                'text': 'You seem stressed lately. Try a breathing exercise.',
                'link': '/mindfulness/'
            })
            recommendations.append({
                'icon': '💬',
                'text': 'Talk to our wellness chatbot for emotional support.',
                'link': '/chat/'
            })

    if len(recommendations) == 0:
        recommendations.append({
            'icon': '✨',
            'text': 'Keep up the great work! Continue logging your mood daily.',
            'link': '/mood/log'
        })

    return recommendations[:5]
    