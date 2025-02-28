from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    risk_score = None
    if request.method == 'POST':
        try:
            likelihood = int(request.form['likelihood'])
            impact = int(request.form['impact'])
            risk_score = likelihood * impact
        except ValueError:
            risk_score = "Invalid input. Please enter valid integers."
    return render_template('index.html', risk_score=risk_score)

if __name__ == '__main__':
    app.run(debug=True)
