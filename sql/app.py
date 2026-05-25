
from flask import Flask, render_template, jsonify, request
import pymysql
import datetime

app = Flask(__name__)

# 数据库连接配置
DB_CONFIG = {
    'host': '8.136.99.105',
    'user': 'root',
    'password': 'mysql_ysqi',
    'database': '宿舍管理系统',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def serialize_dates(data):
    """处理日期和时间类型的序列化，避免 JSON 报错"""
    for row in data:
        for key, value in row.items():
            if isinstance(value, datetime.datetime):
                row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, datetime.date):
                row[key] = value.strftime('%Y-%m-%d')
    return data

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

# ==================== 查询数据接口 (GET) ====================

@app.route('/api/students')
def get_students():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Student")
            students = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'data': serialize_dates(students)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/buildings')
def get_buildings():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Dormitory_Building")
            buildings = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'data': buildings})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/repairs')
def get_repairs():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Repair_Record")
            repairs = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'data': serialize_dates(repairs)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ==================== 插入数据接口 (POST) ====================

@app.route('/api/students', methods=['POST'])
def add_student():
    """处理前端提交的新学生数据"""
    try:
        # 获取前端发送的 JSON 数据
        data = request.json
        sno = data.get('Sno')
        sname = data.get('Sname')
        ssex = data.get('Ssex')
        dept = data.get('Dept')
        sclass = data.get('Sclass')
        phone = data.get('Phone')

        # 简单的验证
        if not sno or not sname:
            return jsonify({'status': 'error', 'message': '学号和姓名不能为空！'})

        # 写入数据库
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO Student (Sno, Sname, Ssex, Dept, Sclass, Phone, CheckInDate)
                VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
            """
            cursor.execute(sql, (sno, sname, ssex, dept, sclass, phone))
        conn.commit() # 必须 commit 才能真正保存到数据库
        conn.close()
        
        return jsonify({'status': 'success', 'message': '学生添加成功！'})
    except pymysql.err.IntegrityError:
        return jsonify({'status': 'error', 'message': '添加失败：学号可能已存在。'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("服务器正在启动... 请在浏览器中访问 http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
