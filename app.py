from flask import Flask, render_template, request, redirect, url_for, flash, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from weasyprint import HTML
from io import StringIO
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///risk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ---------------------------
# User Model
# ---------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------
# Risk Model
# ---------------------------
class Risk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    likelihood = db.Column(db.Integer, nullable=False)
    impact = db.Column(db.Integer, nullable=False)
    severity = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    risk_color = db.Column(db.String(20), nullable=False)
    risk_description = db.Column(db.String(200), nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Risk {self.id} - Score: {self.risk_score}>"

# Create all tables if they don't exist
with app.app_context():
    db.create_all()

# ---------------------------
# Utility Functions
# ---------------------------
def calculate_risk_score(likelihood, impact, severity, frequency):
    likelihood_weight = 0.4
    impact_weight = 0.3
    severity_weight = 0.2
    frequency_weight = 0.1
    return (
        (likelihood * likelihood_weight) +
        (impact * impact_weight) +
        (severity * severity_weight) +
        (frequency * frequency_weight)
    )

def calculate_risk_level(risk_score):
    if risk_score <= 2:
        return "Low", "green", "Minimal impact, unlikely to occur."
    elif risk_score <= 4:
        return "Medium", "yellow", "Moderate impact, possible occurrence."
    else:
        return "High", "red", "Severe impact, highly likely to occur."

def get_mitigation_strategies(risk_level):
    if risk_level == "High":
        return ("Mitigation Strategies for High Risk: Immediately review access controls, update firmware/software, "
                "isolate vulnerable devices, and increase monitoring.")
    elif risk_level == "Medium":
        return ("Mitigation Strategies for Medium Risk: Schedule regular security audits, apply necessary patches, "
                "and improve monitoring and alerting systems.")
    else:
        return "Mitigation Strategies for Low Risk: Maintain routine security checks and monitoring."

# ---------------------------
# Routes
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    risk_score = None
    risk_level = None
    risk_color = None
    risk_description = None

    if request.method == 'POST':
        try:
            likelihood = int(request.form['likelihood'])
            impact = int(request.form['impact'])
            severity = int(request.form['severity'])
            frequency = int(request.form['frequency'])

            if not all(1 <= v <= 5 for v in [likelihood, impact, severity, frequency]):
                risk_score = "Invalid input. Please enter integers between 1 and 5."
            else:
                risk_score = calculate_risk_score(likelihood, impact, severity, frequency)
                risk_level, risk_color, risk_description = calculate_risk_level(risk_score)

                new_risk = Risk(
                    likelihood=likelihood,
                    impact=impact,
                    severity=severity,
                    frequency=frequency,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    risk_color=risk_color,
                    risk_description=risk_description
                )
                db.session.add(new_risk)
                db.session.commit()

                # Redirect to mitigation page (for any risk level)
                return redirect(url_for('mitigation', risk_level=risk_level))
        except ValueError:
            risk_score = "Invalid input. Please enter valid integers."

    return render_template(
        'index.html',
        risk_score=risk_score,
        risk_level=risk_level,
        risk_color=risk_color,
        risk_description=risk_description
    )

@app.route('/mitigation')
def mitigation():
    risk_level = request.args.get('risk_level', 'High')
    strategies = get_mitigation_strategies(risk_level)
    return render_template('mitigation.html', risk_level=risk_level, strategies=strategies)

@app.route('/chart', methods=['GET'])
@login_required
def chart():
    risk_level_filter = request.args.get('risk_level', 'All')
    date_filter = request.args.get('date_filter', '')

    query = Risk.query
    if risk_level_filter and risk_level_filter != 'All':
        query = query.filter_by(risk_level=risk_level_filter)
    if date_filter == 'last_30':
        threshold = datetime.now() - timedelta(days=30)
        query = query.filter(Risk.date_submitted >= threshold)

    filtered_risks = query.all()

    # Prepare arrays for the charts: scores, labels, and colors.
    risk_scores = [r.risk_score for r in filtered_risks] if filtered_risks else []
    risk_labels = [f"Entry {i+1}" for i in range(len(filtered_risks))] if filtered_risks else []
    risk_colors = [r.risk_color for r in filtered_risks] if filtered_risks else []

    return render_template(
        'chart.html',
        risk_scores=risk_scores,
        risk_labels=risk_labels,
        risk_colors=risk_colors,
        selected_risk_level=risk_level_filter,
        selected_date_filter=date_filter
    )

@app.route('/export_csv')
@login_required
def export_csv():
    risks = Risk.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Likelihood', 'Impact', 'Severity', 'Frequency', 'Risk Score', 'Risk Level', 'Mitigation Strategies', 'Risk Description', 'Date Submitted'])
    for r in risks:
        writer.writerow([
            r.id,
            r.likelihood,
            r.impact,
            r.severity,
            r.frequency,
            r.risk_score,
            r.risk_level,
            get_mitigation_strategies(r.risk_level),
            r.risk_description,
            r.date_submitted.strftime("%Y-%m-%d %H:%M:%S") if r.date_submitted else ''
        ])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=RiskReport.csv'
    return response

@app.route('/download_report')
@login_required
def download_report():
    risks = Risk.query.all()
    html_string = render_template(
        'report.html',
        risks=risks,
        current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        get_mitigation_strategies=get_mitigation_strategies
    )
    pdf_file = HTML(string=html_string).write_pdf()
    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename="RiskReport.pdf"'
    return response

# ---------------------------
# Authentication Routes
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out. Please log in again.", "info")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
