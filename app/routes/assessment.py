import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import AssessmentResult, SafetyLog

assessment_bp = Blueprint('assessment', __name__)

ASSESSMENTS = {
    'anxiety': {
        'title': 'Anxiety Assessment (GAD-7 Adapted)',
        'description': 'This questionnaire helps evaluate your anxiety level over the past two weeks.',
        'questions': [
            'Feeling nervous, anxious, or on edge',
            'Not being able to stop or control worrying',
            'Worrying too much about different things',
            'Trouble relaxing',
            'Being so restless that it\'s hard to sit still',
            'Becoming easily annoyed or irritable',
            'Feeling afraid as if something awful might happen'
        ]
    },
    'stress': {
        'title': 'Perceived Stress Assessment',
        'description': 'This questionnaire measures your perception of stress over the past month.',
        'questions': [
            'How often have you been upset because of something unexpected?',
            'How often have you felt unable to control important things in your life?',
            'How often have you felt nervous and stressed?',
            'How often have you felt confident about handling personal problems?',
            'How often have you felt things were going your way?',
            'How often have you found you could not cope with all things you had to do?',
            'How often have you been able to control irritations in your life?',
            'How often have you felt you were on top of things?',
            'How often have you been angered by things outside of your control?',
            'How often have you felt difficulties were piling up so high you could not overcome them?'
        ]
    },
    'wellbeing': {
        'title': 'General Emotional Well-being Assessment',
        'description': 'This questionnaire evaluates your overall emotional health and wellness.',
        'questions': [
            'I have felt cheerful and in good spirits',
            'I have felt calm and relaxed',
            'I have felt active and vigorous',
            'I woke up feeling fresh and rested',
            'My daily life has been filled with things that interest me',
            'I have felt confident in myself',
            'I have been able to handle everyday challenges',
            'I have felt connected to others around me'
        ]
    }
}

SEVERITY_LABELS = [
    (80, 'thriving', 'You are doing exceptionally well emotionally.'),
    (60, 'managing well', 'You are handling things effectively with room for growth.'),
    (40, 'mild difficulty', 'You may benefit from additional self-care and coping strategies.'),
    (25, 'moderate difficulty', 'Consider seeking support and using available wellness tools regularly.'),
    (0, 'severe distress', 'We strongly recommend reaching out to a professional for support.')
]


def calculate_score(answers, category):
    """Calculate wellness score on 0-100 scale."""
    total_questions = len(answers)
    max_score = total_questions * 4  # Each question scored 0-4

    if category == 'wellbeing':
        # Higher answers = better wellness
        raw_score = sum(answers)
    else:
        # Higher answers = more distress, so invert
        raw_score = max_score - sum(answers)

    return round((raw_score / max_score) * 100)


def get_severity(score):
    """Get severity label based on score."""
    for threshold, label, description in SEVERITY_LABELS:
        if score >= threshold:
            return label, description
    return 'severe distress', SEVERITY_LABELS[-1][2]


@assessment_bp.route('/')
@login_required
def index():
    results = AssessmentResult.query.filter_by(user_id=current_user.id)\
        .order_by(AssessmentResult.created_at.desc()).all()
    return render_template('assessment/index.html',
                           assessments=ASSESSMENTS,
                           results=results)


@assessment_bp.route('/take/<category>')
@login_required
def take(category):
    if category not in ASSESSMENTS:
        flash('Invalid assessment category.', 'danger')
        return redirect(url_for('assessment.index'))

    assessment = ASSESSMENTS[category]
    return render_template('assessment/take.html',
                           category=category,
                           assessment=assessment)


@assessment_bp.route('/submit/<category>', methods=['POST'])
@login_required
def submit(category):
    if category not in ASSESSMENTS:
        flash('Invalid assessment category.', 'danger')
        return redirect(url_for('assessment.index'))

    assessment = ASSESSMENTS[category]
    answers = []

    for i in range(len(assessment['questions'])):
        answer = request.form.get(f'q{i}')
        if answer is None or answer == '':
            flash('Please answer all questions.', 'danger')
            return redirect(url_for('assessment.take', category=category))
        answers.append(int(answer))

    score = calculate_score(answers, category)
    severity_label, severity_desc = get_severity(score)

    # Save result
    result = AssessmentResult(
        user_id=current_user.id,
        category=category,
        score=score,
        severity_label=severity_label
    )
    db.session.add(result)

    # Check for severe distress - activate safety protocol
    crisis_triggered = False
    if score <= 25:
        crisis_triggered = True
        safety_log = SafetyLog(
            user_id=current_user.id,
            trigger_source='Assessment_Engine',
            trigger_content=f'{category} assessment score: {score}',
            event_type='activation'
        )
        db.session.add(safety_log)

    db.session.commit()

    # Return simple HTML response directly
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Assessment Result</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container py-5">
            <div class="card p-4 text-center">
                <h1>Your Result</h1>
                <h2>Category: {category}</h2>
                <h3>Score: {score}</h3>
                <h4>Severity: {severity_label}</h4>
                <p>{severity_desc}</p>
                <a href="/assessment" class="btn btn-primary">Back to Assessments</a>
            </div>
        </div>
    </body>
    </html>
    """
    