import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, url_for
from flask_login import login_required, current_user
from app import db
from app.models import ChatMessage, SafetyLog, MoodEntry, AssessmentResult, MindfulnessExercise, ExerciseCompletion

chat_bp = Blueprint('chat', __name__)

CRISIS_KEYWORDS = [
    'want to die', 'end it all', 'hurt myself', 'no reason to live',
    'kill myself', 'suicide', 'self-harm', 'end my life',
    'better off dead', 'can\'t go on'
]

EMOTION_RESPONSES = {
    'happy': "I'm glad you're feeling happy! That's wonderful. What's bringing you joy today?",
    'calm': "It's great that you're feeling calm. Maintaining this peace is valuable. Would you like to try a mindfulness exercise to deepen this feeling?",
    'anxious': "I hear that you're feeling anxious. That's a valid feeling. Let's try a grounding technique: can you name 5 things you can see right now?",
    'sad': "I'm sorry you're feeling sad. It's okay to feel this way. Would you like to talk about what's on your mind, or would you prefer a guided breathing exercise?",
    'angry': "I can sense you're feeling angry. Your feelings are valid. Let's take a moment — try taking 3 deep breaths with me. Would you like to explore what triggered this feeling?",
    'stressed': "It sounds like you're under a lot of stress. That must be tough. Let's break things down — what feels most overwhelming right now?",
    'neutral': "Thanks for checking in. Even neutral days are worth noting. Is there anything specific you'd like to talk about or explore today?"
}

COPING_SUGGESTIONS = [
    "Try the 4-7-8 breathing technique: breathe in for 4 seconds, hold for 7, exhale for 8.",
    "Consider taking a short walk outside. Even 5 minutes of movement can shift your mood.",
    "Write down three things you're grateful for right now.",
    "Try a body scan meditation — start from your toes and slowly move your attention upward.",
    "Reach out to someone you trust and share how you're feeling.",
    "Practice progressive muscle relaxation: tense each muscle group for 5 seconds, then release."
]

# Mood-specific follow-up questions
MOOD_QUESTIONS = {
    'anxious': [
        "What's been making you feel anxious?",
        "Can you name three things that are within your control right now?",
        "How long have you been feeling this way?"
    ],
    'stressed': [
        "What's the biggest source of stress right now?",
        "Is there something you need to let go of?",
        "What would help you feel more grounded?"
    ],
    'sad': [
        "Would you like to talk about what's making you feel sad?",
        "What's one small thing that might bring you comfort?",
        "Have you been able to get enough rest lately?"
    ],
    'angry': [
        "What triggered this feeling?",
        "What's the situation you'd like to change?",
        "How can you express this feeling in a healthy way?"
    ],
    'happy': [
        "That's wonderful! What's contributing to your happiness?",
        "How can you savor this feeling?",
        "Is there someone you'd like to share this with?"
    ],
    'calm': [
        "It's great to feel calm. What helps you maintain this peace?",
        "Would you like to do a mindfulness exercise to deepen this?",
        "What's making this moment feel peaceful?"
    ],
    'neutral': [
        "How are you feeling right now, in this moment?",
        "Is there anything you'd like to focus on?",
        "What's been on your mind lately?"
    ]
}

# Mood to exercise category mapping
MOOD_EXERCISE_SUGGESTIONS = {
    'anxious': {'categories': ['breathing', 'meditation'], 'title': 'calm anxiety'},
    'stressed': {'categories': ['breathing', 'body_scan'], 'title': 'relieve stress'},
    'sad': {'categories': ['meditation', 'body_scan'], 'title': 'lift your mood'},
    'angry': {'categories': ['breathing', 'meditation'], 'title': 'release anger'},
    'happy': {'categories': ['meditation', 'body_scan'], 'title': 'deepen happiness'},
    'calm': {'categories': ['meditation', 'body_scan'], 'title': 'deepen calm'},
    'neutral': {'categories': ['breathing', 'meditation', 'body_scan'], 'title': 'relax'}
}

# Mood to assessment mapping
MOOD_ASSESSMENT_SUGGESTIONS = {
    'anxious': {'category': 'anxiety', 'reason': 'better understand your anxiety'},
    'stressed': {'category': 'stress', 'reason': 'assess your stress levels'},
    'sad': {'category': 'wellbeing', 'reason': 'check in on your well-being'},
    'angry': {'category': 'wellbeing', 'reason': 'understand your emotional state'},
    'neutral': {'category': 'wellbeing', 'reason': 'regular wellness check'},
    'calm': {'category': 'wellbeing', 'reason': 'track your wellness'},
    'happy': {'category': 'wellbeing', 'reason': 'celebrate and track your wellness'}
}


@chat_bp.route('/')
@login_required
def index():
    # Check if this is a fresh chat (from mood log)
    fresh = request.args.get('fresh') == '1'
    
    if fresh:
        # Clear previous messages for a fresh chat
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        messages = []
    else:
        messages = ChatMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ChatMessage.created_at.desc()).limit(50).all()
        messages.reverse()
    
    # Get the user's last logged mood
    last_mood = session.get('last_mood')
    if not last_mood:
        latest_mood = MoodEntry.query.filter_by(user_id=current_user.id)\
            .order_by(MoodEntry.created_at.desc()).first()
        last_mood = latest_mood.mood if latest_mood else None
    
    # Get initial greeting based on mood
    initial_greeting = None
    if last_mood and last_mood in MOOD_QUESTIONS:
        initial_greeting = {
            'mood': last_mood,
            'question': MOOD_QUESTIONS[last_mood][0]
        }
    
    return render_template('chat/index.html', 
                           messages=messages, 
                           last_mood=last_mood,
                           initial_greeting=initial_greeting)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, role='user', content=user_message)
    db.session.add(user_msg)

    # Check for crisis keywords
    message_lower = user_message.lower()
    crisis_detected = any(keyword in message_lower for keyword in CRISIS_KEYWORDS)

    if crisis_detected:
        # Activate safety protocol
        safety_log = SafetyLog(
            user_id=current_user.id,
            trigger_source='Chatbot',
            trigger_content=user_message,
            event_type='activation'
        )
        db.session.add(safety_log)

        response = (
            "I'm concerned about what you've shared. Your feelings are valid, and you deserve support. "
            "Please reach out to a crisis service right away:\n\n"
            "📞 **988 Suicide & Crisis Lifeline**: Call or text 988\n"
            "💬 **Crisis Text Line**: Text HOME to 741741\n\n"
            "This app is not a substitute for professional help. A trained counselor can provide "
            "the support you need right now. You are not alone."
        )
    else:
        response = generate_response(user_message)

    # Save assistant response
    assistant_msg = ChatMessage(user_id=current_user.id, role='assistant', content=response)
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        'response': response,
        'crisis_detected': crisis_detected
    })


def generate_response(message):
    """Generate an empathetic response based on the message content."""
    message_lower = message.lower()

    # Check for emotion keywords
    for emotion, response in EMOTION_RESPONSES.items():
        if emotion in message_lower:
            return response

    # Check for greeting
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good evening']
    if any(g in message_lower for g in greetings):
        return ("Hello! I'm here to support you. How are you feeling today? "
                "You can share your emotions, ask for coping strategies, or "
                "just chat about what's on your mind.")

    # Check for help request
    if 'help' in message_lower or 'what can you do' in message_lower:
        return ("I'm here to provide emotional support and guidance. I can:\n\n"
                "• Listen to how you're feeling\n"
                "• Suggest coping strategies\n"
                "• Guide you through breathing exercises\n"
                "• Recommend mindfulness activities\n"
                "• Help you reflect on your emotions\n\n"
                "What would you like to explore?")

    # Check for thanks
    if 'thank' in message_lower:
        return ("You're welcome! Remember, taking time for your emotional wellness "
                "is an act of strength. I'm here whenever you need support.")

    # Default empathetic response with coping suggestion
    import random
    suggestion = random.choice(COPING_SUGGESTIONS)
    return (f"Thank you for sharing that with me. Your feelings matter. "
            f"Here's something that might help: {suggestion}\n\n"
            f"Would you like to tell me more about how you're feeling?")


@chat_bp.route('/suggestions', methods=['POST'])
@login_required
def get_suggestions():
    """Get exercise and assessment suggestions based on mood and chat context."""
    data = request.get_json()
    mood = data.get('mood', session.get('last_mood'))
    context = data.get('context', '')
    
    suggestions = {
        'exercises': [],
        'assessments': []
    }
    
    # Get exercise suggestions
    if mood and mood in MOOD_EXERCISE_SUGGESTIONS:
        exercise_info = MOOD_EXERCISE_SUGGESTIONS[mood]
        exercises = MindfulnessExercise.query.filter(
            MindfulnessExercise.category.in_(exercise_info['categories'])
        ).limit(3).all()
        
        suggestions['exercises'] = [
            {
                'id': ex.id,
                'title': ex.title,
                'category': ex.category,
                'duration': ex.duration_minutes,
                'url': url_for('mindfulness.exercise', exercise_id=ex.id, _external=True)
            }
            for ex in exercises
        ]
    
    # Get assessment suggestions
    if mood and mood in MOOD_ASSESSMENT_SUGGESTIONS:
        assessment_info = MOOD_ASSESSMENT_SUGGESTIONS[mood]
        # Check if user already took this assessment recently
        recent = AssessmentResult.query.filter(
            AssessmentResult.user_id == current_user.id,
            AssessmentResult.category == assessment_info['category']
        ).order_by(AssessmentResult.created_at.desc()).first()
        
        if not recent or (datetime.utcnow() - recent.created_at).days > 7:
            suggestions['assessments'] = [
                {
                    'category': assessment_info['category'],
                    'reason': assessment_info['reason'],
                    'url': url_for('assessment.take', category=assessment_info['category'], _external=True)
                }
            ]
    
    return jsonify(suggestions)