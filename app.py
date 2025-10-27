from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Flask App deployed successfully on AWS Elastic Beanstalk!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
