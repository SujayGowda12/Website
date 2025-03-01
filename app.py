from flask import Flask, render_template, request, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
from datetime import datetime, timedelta
from weasyprint import HTML
import csv
from io import StringIO
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure the database (using SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///risk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
    file_path = db.Column(db.String(200))  # New field for file path
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

# Create database tables at startup within an application context
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
            description = request.form.get('description', '')  # Get detailed description

            # Validate that each value is between 1 and 5
            if not all(1 <= v <= 5 for v in [likelihood, impact, severity, frequency]):
                risk_score = "Invalid input. Please enter integers between 1 and 5."
            else:
                risk_score = calculate_risk_score(likelihood, impact, severity, frequency)
                risk_level, risk_color, risk_description = calculate_risk_level(risk_score)

                # Handle file upload
                file_path = None
                if 'file' in request.files:
                    file = request.files['file']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)

                new_risk = Risk(
                    likelihood=likelihood,
                    impact=impact,
                    severity=severity,
                    frequency=frequency,
                    risk_score=risk_score,
                    risk_level=risk_level,
                    risk_color=risk_color,
                    risk_description=description,  # Save detailed description
                    file_path=file_path  # Save file path
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

@app.route('/chart', methods=['GET'])
def chart():
    # Get filtering parameters from query string (GET parameters)
    risk_level_filter = request.args.get('risk_level', 'All')
    date_filter = request.args.get('date_filter', '')

    # Build the query
    query = Risk.query

    # Filter by risk level if not "All"
    if risk_level_filter and risk_level_filter != 'All':
        query = query.filter_by(risk_level=risk_level_filter)

    # Filter by date if specified (e.g., "last_30")
    if date_filter == 'last_30':
        threshold = datetime.now() - timedelta(days=30)
        query = query.filter(Risk.date_submitted >= threshold)

    filtered_risks = query.all()

    # Prepare data for the chart
    risk_labels = [f"Entry {i+1}" for i in range(len(filtered_risks))]
    likelihood_data = [r.likelihood for r in filtered_risks]
    impact_data = [r.impact for r in filtered_risks]
    severity_data = [r.severity for r in filtered_risks]
    frequency_data = [r.frequency for r in filtered_risks]

    # Calculate risk level counts
    risk_level_counts = {
        'Low': Risk.query.filter_by(risk_level='Low').count(),
        'Medium': Risk.query.filter_by(risk_level='Medium').count(),
        'High': Risk.query.filter_by(risk_level='High').count()
    }

    return render_template(
        'chart.html',
        risk_labels=risk_labels,
        likelihood_data=likelihood_data,
        impact_data=impact_data,
        severity_data=severity_data,
        frequency_data=frequency_data,
        risk_level_counts=risk_level_counts,
        selected_risk_level=risk_level_filter,
        selected_date_filter=date_filter
    )

@app.route('/export_csv')
def export_csv():
    risks = Risk.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Likelihood', 'Impact', 'Severity', 'Frequency', 'Risk Score', 'Risk Level', 'Risk Description', 'File Path', 'Date Submitted'])
    for r in risks:
        writer.writerow([
            r.id,
            r.likelihood,
            r.impact,
            r.severity,
            r.frequency,
            r.risk_score,
            r.risk_level,
            r.risk_description,
            r.file_path,
            r.date_submitted.strftime("%Y-%m-%d %H:%M:%S") if r.date_submitted else ''
        ])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=RiskReport.csv'
    return response

@app.route('/download_report')
def download_report():
    risks = Risk.query.all()
    html_string = render_template(
        'report.html',
        risks=risks,
        current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    pdf_file = HTML(string=html_string).write_pdf()
    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename="RiskReport.pdf"'
    return response

if __name__ == '__main__':
    app.run(debug=True)