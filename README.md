**Click here for English version: [English](README_en.md)**

## 中国社会事件数据库（CSED）

![preview](/preview.png)

主页：[https://csed.zheqiaoc.com](https://csed.zheqiaoc.com)

中国社会事件数据库（CSED）是一个基于时间线的事件汇总和分析工具，旨在记录每日社会动态与网络舆情。

中国社会事件数据库的开发源于两个问题：
1. 中国每天在发生什么？
2. 民众每天在互联网上关注和接收哪些信息？

多数的传播学或政治学研究似乎更多关注特定事件的报道，而非整体的信息分布。因此，我希望可以通过这个项目，在事件的层次汇总数据，并进行分析。

### 这一项目有以下特点：

1. 每日自动汇总信息，以时间线的形式进行展示。
2. ~~政府回应检测，有小黄星的条目包含了政府的回应。~~(这一功能仅在代码中有，前端取消了)
3. 点击帖子标题可以跳转微博原帖。
4. 对移动端和桌面端都有较好的支持。

### 未来希望可以完成的事情：

1. 提供数据下载的页面或者API接口。
2. 增加更多的功能，如事件分类，事件地图等。
3. 增加更多的数据源，如公众号，抖音等。
4. ~~开源（抱歉代码写得太差，没仔细检查之前不好意思开源）~~

### 快速开始：

在部署前需要做四件准备工作：
1. 找到一个微博爬虫软件，并完成相关配置，我使用的是这个项目[weibo-crawler](https://github.com/dataabc/weibo-crawler)，配置userlist和config.json并爬取你需要的数据
2. 在本地安装好node.js和npm
3. 在本地安装好mongodb
4. 获取自己的Open AI API密钥

#### 第一步
```bash
# 把项目克隆到本地
git clone https://github.com/zheqiaochen/China-Social-Event-Database-CSED.git

# 进入项目目录
cd China-Social-Event-Database-CSED

# 安装依赖
pip install -r requirements.txt

# 安装依赖
npm run install
```

#### 第二步

在根目录新建一个.env文件，并且输入mongodb的连接地址（在本地的话默认为mongodb://localhost:27017/）和openai的api密钥，格式如下：

```
MONGO_URI=mongodb://localhost:27017/
API_KEY=sk-...
```

#### 第三步
```bash
# 启动后端服务器
python "backend/main.py"

# 按顺序运行以下指令

# 摘要
curl -X POST http://0.0.0.0:8888/api/process/summary
# embedding
curl -X POST http://0.0.0.0:8888/api/process/embedding
# 聚类
curl -X POST http://0.0.0.0:8888/api/cluster/hdbscan
# 获取聚类标题
curl -X POST http://0.0.0.0:8888/api/cluster/titles

# 如需删除数据运行（默认删除7天之前的未成功聚类数据）
curl -X POST http://0.0.0.0:8888/api/process/delete_old

# 如需归档数据运行（默认归档7天未活跃的事件）
curl -X POST http://0.0.0.0:8888/api/process/archive_inactive_events

# 运行完成之后可以启动前端看一看效果
npm run dev
```
之后可以通过cronjob每天自动运行

我目前正在上学，没有充足的时间进行后续开发维护，并且对编程知识了解有限。如果你对这一项目有兴趣和想法，欢迎通过邮件联系我，可以在[About](https://zheqiaoc.com/about/)页面找到我的邮箱。