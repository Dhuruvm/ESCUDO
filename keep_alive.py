
from flask import Flask
from threading import Thread
import time

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>ESCUDO Discord Bot - Keep Alive</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    display: inline-block;
                }
                .status { color: #4CAF50; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛡️ ESCUDO Discord Bot</h1>
                <p class="status">✅ Bot is Online and Active</p>
                <p>Keep-alive server is running successfully!</p>
                <p><small>This page keeps the bot alive on Replit</small></p>
            </div>
        </body>
    </html>
    '''

@app.route('/status')
def status():
    return {
        'status': 'online',
        'message': 'ESCUDO Discord Bot is running',
        'timestamp': int(time.time())
    }

@app.route('/ping')
def ping():
    return 'pong'

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
