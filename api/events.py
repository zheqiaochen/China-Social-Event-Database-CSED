from http.server import BaseHTTPRequestHandler
from pymongo import MongoClient
import json
from bson import json_util
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
 
# 数据库连接
def connect_to_db():
    client = MongoClient('mongodb+srv://REDACTED@cluster0.cutgb.mongodb.net/')
    return client['weibo']['weibo']

# HTTP 处理类
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 连接数据库
            collection = connect_to_db()

            # 聚合管道
            pipeline = [
                {
                    "$match": {
                        "event_id": {"$exists": True},
                        "event_title": {"$exists": True},
                        "text": {"$exists": True},
                        "summary_embedding_cluster_label": {"$exists": True, "$ne": -1}
                    }
                },
                {"$sort": {"created_at": -1}},  # 按创建时间倒序排序
                {
                    "$group": {
                        "_id": "$event_id",
                        "event_title": {"$first": "$event_title"},
                        "posts": {
                            "$push": {
                                "id": "$id",
                                "text": "$text",
                                "screen_name": "$screen_name",
                                "attitudes_count": "$attitudes_count",
                                "comments_count": "$comments_count",
                                "reposts_count": "$reposts_count",
                                "created_at": "$created_at",
                                "response": {"$ifNull": ["$response", 0]}
                            }
                        }
                    }
                }
            ]

            # 查询数据
            documents = list(collection.aggregate(pipeline))

            # 返回响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                "events": documents,
                "total_events": len(documents)  # 直接返回实际事件数量
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