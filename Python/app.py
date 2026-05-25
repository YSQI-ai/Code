from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '<h1>我的金融项目已成功运行！</h1><p>这是来自 Docker 容器的响应。</p>'

if __name__ == '__main__':
    # 注意：在 Docker 中 host 必须是 0.0.0.0，端口要和 Dockerfile 一致
    app.run(host='0.0.0.0', port=5000)