from datetime import datetime, timedelta
from flask_login import UserMixin
from app import db, login_manager
import bcrypt

# Trading Journey Database constants
MARKET_TYPES = ['stocks', 'forex', 'crypto', 'options', 'futures']
TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', 'daily', 'weekly']
EMOTIONS = ['confident', 'fearful', 'greedy', 'calm', 'anxious', 'revenge', 'neutral']


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    mood_entries = db.relationship('MoodEntry', backref='user', lazy='dynamic')
    assessments = db.relationship('AssessmentResult', backref='user', lazy='dynamic')
    chat_sessions = db.relationship('ChatMessage', backref='user', lazy='dynamic')
    exercise_completions = db.relationship('ExerciseCompletion', backref='user', lazy='dynamic')
    trades = db.relationship('Trade', backref='user', lazy='dynamic')

    def set_password(self, password):
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False


class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AssessmentResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    severity_label = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MindfulnessExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), nullable=False)  # breathing, meditation, body_scan
    difficulty = db.Column(db.String(15), nullable=False)  # beginner, intermediate, advanced
    duration_minutes = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    steps = db.Column(db.Text, nullable=False)  # JSON string of steps


class ExerciseCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('mindfulness_exercise.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    exercise = db.relationship('MindfulnessExercise')


class SafetyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trigger_source = db.Column(db.String(30), nullable=False)
    trigger_content = db.Column(db.Text, nullable=True)
    event_type = db.Column(db.String(20), nullable=False)  # 'activation' or 'dismissal'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    symbol = db.Column(db.String(20), nullable=False)  # e.g., AAPL, NIFTY, BTC
    trade_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=True)
    target = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(10), nullable=False, default='open')  # 'open', 'closed', 'cancelled'
    pnl = db.Column(db.Float, nullable=True)  # Profit/Loss
    strategy = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    emotion_before = db.Column(db.String(20), nullable=True)  # How you felt before the trade
    emotion_after = db.Column(db.String(20), nullable=True)  # How you felt after
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Enhanced fields for Trading Journey Database
    market_type = db.Column(db.String(20), nullable=True)  # stocks, forex, crypto, options, futures
    timeframe = db.Column(db.String(10), nullable=True)  # 1m, 5m, 15m, 1h, 4h, daily, weekly
    tags = db.Column(db.String(200), nullable=True)  # comma-separated, max 5 tags
    screenshot_url = db.Column(db.String(2048), nullable=True)  # must start with http:// or https://
    risk_reward_ratio = db.Column(db.Float, nullable=True)  # 0.1–100.0


class TradeReflection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id'), unique=True, nullable=False)
    reflection_text = db.Column(db.Text, nullable=True)
    lessons_learned = db.Column(db.Text, nullable=False)
    mistakes_made = db.Column(db.Text, nullable=True)
    what_went_well = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trade = db.relationship('Trade', backref=db.backref('reflection', uselist=False))