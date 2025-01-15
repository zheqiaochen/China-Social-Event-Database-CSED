## China Social Event Database (CSED)

China Social Event Database (CSED) is a timeline-based event aggregation and analysis tool designed to record daily social dynamics and online public opinion.

The development of China Social Event Database (CSED) stems from two questions:
1. What is happening in China every day?
2. What information are people receiving on the Chinese internet?

Most social media or political science studies seem to focus more on specific events rather than the overall distribution of information. Therefore, I hope to aggregate and analyze data at the event level through this project.

### Features:

1. Automatically aggregates information daily and displays it in a timeline format.
2. ~~Government response detection, entries with yellow stars contain government responses.~~ (This feature exists in code but is not displayed in frontend)
3. Click on post titles to jump to original Weibo posts.
4. Good support for both mobile and desktop platforms.

### Future Plans:

1. Provide data download page or API interface.
2. Add more features like event classification, event mapping, etc.
3. Add more data sources like WeChat Official Accounts, Douyin, etc.
4. ~~Open source (Sorry the code quality isn't great, didn't want to open source before thorough review)~~

### Quick Start:

Four preparations are needed before deployment:
1. Find a Weibo crawler software and complete related configuration. I use [weibo-crawler](https://github.com/dataabc/weibo-crawler). Configure userlist and config.json and crawl the data you need
2. Install Node.js and npm locally
3. Install MongoDB locally
4. Get your own OpenAI API key

#### Step 1
```bash
# Clone the repository
git clone https://github.com/zheqiaochen/China-Social-Event-Database-CSED.git

# Enter the project directory
cd China-Social-Event-Database-CSED

# Install dependencies
pip install -r requirements.txt
npm install
```

#### Step 2

Configure backend/config.json, replace MONGO_URI and API_KEY
Configure frontend/server.py, replace MONGO_URI
Configure api/events.py, replace MONGO_URI

#### Step 3
```bash
# Start backend server
python "backend/main.py"

# Run the following commands in order

# Summary
curl -X POST http://0.0.0.0:8888/api/process/summary
# Embedding
curl -X POST http://0.0.0.0:8888/api/process/embedding
# Clustering
curl -X POST http://0.0.0.0:8888/api/cluster/hdbscan
# Generate cluster titles
curl -X POST http://0.0.0.0:8888/api/cluster/titles

# Run the following command to delete data (default deletes data older than 7 days that failed to be clustered)
curl -X POST http://0.0.0.0:8888/api/process/delete_old

# After running, you can start the frontend to see the effect
npm run dev
```

I am currently a student and do not have enough time to maintain and develop this project. If you are interested, feel free to drop me an email. You can find the contact information on this page: [About](https://zheqiaoc.com/about/).
