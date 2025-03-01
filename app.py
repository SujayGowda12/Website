from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure the database (using SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///risk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model to store risk entries
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

# Function to calculate the weighted risk score
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

# Function to determine risk level, color, and description based on the risk score
def calculate_risk_level(risk_score):
    if risk_score <= 2:
        return "Low", "green", "Minimal impact, unlikely to occur."
    elif risk_score <= 4:
        return "Medium", "yellow", "Moderate impact, possible occurrence."
    else:
        return "High", "red", "Severe impact, highly likely to occur."

# Create tables at startup (using an application context)
with app.app_context():
    db.create_all()

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

            # Validate inputs (must be between 1 and 5)
            if not all(1 <= value <= 5 for value in [likelihood, impact, severity, frequency]):
                risk_score = "Invalid input. Please enter integers between 1 and 5."
            else:
                # Calculate risk score and determine risk details
                risk_score = calculate_risk_score(likelihood, impact, severity, frequency)
                risk_level, risk_color, risk_description = calculate_risk_level(risk_score)

                # Create and save a new risk record
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

        except ValueError:
            risk_score = "Invalid input. Please enter valid integers."

    return render_template(
        'index.html',
        risk_score=risk_score,
        risk_level=risk_level,
        risk_color=risk_color,
        risk_description=risk_description
    )

# New route for the chart page
@app.route('/chart')
def chart():
    all_risks = Risk.query.all()
    risk_scores = [r.risk_score for r in all_risks]
    risk_labels = [f"Entry {i+1}" for i in range(len(all_risks))]
    return render_template('chart.html', risk_scores=risk_scores, risk_labels=risk_labels)

if __name__ == '__main__':
    app.run(debug=True)
