from http.server import BaseHTTPRequestHandler
from pymongo import MongoClient
import json
from bson import json_util
import os
from dotenv import load_dotenv

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录路径
root_dir = os.path.dirname(current_dir)
# 加载根目录下的 .env 文件
load_dotenv(os.path.join(root_dir, '.env'))

# 数据库连接
def connect_to_db():
    client = MongoClient(os.getenv('MONGO_URI'))
    return client['weibo']['weibo']

# HTTP 处理类
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 连接数据库
            collection = connect_to_db()

            # 聚合管道 - 只获取事件基本信息
            pipeline = [
                {
                    "$match": {
                        "event_title": {"$exists": True},
                        "text": {"$exists": True},
                        "summary_embedding_cluster_label": {"$exists": True, "$ne": -1}
                    }
                },
                {"$sort": {"created_at": -1}},
                {
                    "$group": {
                        "_id": "$summary_embedding_cluster_label",
                        "event_title": {"$first": "$event_title"},
                        "latest_post": {
                            "$first": {
                                "created_at": "$created_at"
                            }
                        },
                        "posts_count": {"$sum": 1}
                    }
                }
            ]

            # 查询数据
            documents = list(collection.aggregate(pipeline, allowDiskUse=True))

            # 返回响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                "events": documents,
                "total_events": len(documents)
            }
            self.wfile.write(json_util.dumps(response).encode())

        except Exception as e:
            # 异常处理
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        # 处理 CORS 预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()