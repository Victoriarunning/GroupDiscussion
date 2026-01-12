from flask import Flask, request, jsonify
from datetime import time, datetime
from statement_keeper import get_statements

app = Flask(__name__)


@app.route('/get_statement', methods=['GET'])
def get_statement():
    """获取指定时间范围内的语句"""
    start_time = request.args.get('start')
    end_time = request.args.get('end')

    if not start_time or not end_time:
        return jsonify({"error": "start and end time parameters are required"}), 400

    try:
        start = datetime.strptime(start_time, "%H:%M:%S").time()
        end = datetime.strptime(end_time, "%H:%M:%S").time()

        result = get_statements(start, end)

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
