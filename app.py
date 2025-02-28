from flask import Flask, render_template, request

app = Flask(__name__)

# Enhanced risk calculation function
def calculate_risk_score(likelihood, impact, severity, frequency):
    # Define weights for each factor
    likelihood_weight = 0.4
    impact_weight = 0.3
    severity_weight = 0.2
    frequency_weight = 0.1

    # Calculate weighted risk score
    risk_score = (
        (likelihood * likelihood_weight) +
        (impact * impact_weight) +
        (severity * severity_weight) +
        (frequency * frequency_weight)
    )
    return risk_score

# Function to determine risk level, color, and description
def calculate_risk_level(risk_score):
    if risk_score <= 2:  # Adjusted from 3 to 2
        return "Low", "green", "Minimal impact, unlikely to occur."
    elif risk_score <= 4:  # Adjusted from 7 to 4
        return "Medium", "yellow", "Moderate impact, possible occurrence."
    else:
        return "High", "red", "Severe impact, highly likely to occur."

@app.route('/', methods=['GET', 'POST'])
def index():
    risk_score = None
    risk_level = None
    risk_color = None
    risk_description = None

    if request.method == 'POST':
        try:
            # Get form inputs
            likelihood = int(request.form['likelihood'])
            impact = int(request.form['impact'])
            severity = int(request.form['severity'])
            frequency = int(request.form['frequency'])

            # Validate inputs (ensure they are between 1 and 5)
            if not all(1 <= value <= 5 for value in [likelihood, impact, severity, frequency]):
                risk_score = "Invalid input. Please enter integers between 1 and 5."
            else:
                # Calculate risk score, level, color, and description
                risk_score = calculate_risk_score(likelihood, impact, severity, frequency)
                risk_level, risk_color, risk_description = calculate_risk_level(risk_score)

        except ValueError:
            risk_score = "Invalid input. Please enter valid integers."

    return render_template(
        'index.html',
        risk_score=risk_score,
        risk_level=risk_level,
        risk_color=risk_color,
        risk_description=risk_description
    )

if __name__ == '__main__':
    app.run(debug=True)