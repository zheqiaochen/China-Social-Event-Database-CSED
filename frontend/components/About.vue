<template>
  <div class="about-container">
    <div class="about-content">
      <h2 class="about-title">关于</h2>
      
      <section class="about-section">
        <h3>CSED Introduction</h3>
        <p> 中国社会事件数据库 (China Social Event Database) 第一次的数据采集开始于2024年的最后一天，上线于2025年1月3日，用于记录和展示中国社会事件以及相关的政府回应。</p>
        <a href="https://www.zheqiaoc.com/2025/01/07/中文csed" class="link">项目的中文介绍</a>
        <a style="margin-left: 20px"></a>
        <a href="https://www.zheqiaoc.com/2025/01/04/csed" class="link">English Introduction </a>
      </section>

      <section class="about-section">
        <h3>CSED Features</h3>
        <ul>
          <li>每天晚上系统会运行一次，更新当日最新社会事件</li>
          <li>项目为学术用途，您也可以将其当作一个新闻网站</li>
          <!-- <li>卡片中带有黄色星星表示该事件被中国国家机构回应</li> -->
          <li>项目还在完善中，结果不尽准确。运行方式、功能、包括本页面都会持续更新</li>
        </ul>
      </section>

      <section class="about-section">
        <h3>Contact</h3>
        <p>Zheqiao Chen</p>
        <p>Email: <a href="mailto:zheqiao.chen@columbia.edu" class="email-link">zheqiao.chen@columbia.edu</a></p>
        <p>Website: <a href="https://zheqiaoc.com" class="email-link">zheqiaoc.com</a></p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.about-container {
  height: calc(100vh - 100px);
  overflow-y: auto;
  padding: 10px;
  background-color: #fafafa;
}

.about-content {
  max-width: 700px;
  margin: 0 auto;
  background: #fff;
  padding: 20px 40px 20px 40px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.about-title {
  text-align: center;
  color: #202020;
  margin-bottom: 40px;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.about-section {
  margin-bottom: 40px;
}

.about-section h3 {
  color: #202020;
  margin-bottom: 24px;
  font-size: 18px;
  font-weight: 600;
  position: relative;
  padding-bottom: 5px;
}

.about-section p {
  color: #606266;
  line-height: 1.8;
  margin-bottom: 12px;
  font-size: 14px;
}

.about-section ul {
  list-style: none;
  padding-left: 0;
  margin: 16px 0;
}

.about-section li {
  color: #606266;
  line-height: 1.8;
  padding-left: 16px;
  position: relative;
  font-size: 14px;
  margin-bottom: 8px;
}

.about-section li:before {
  content: "•";
  color: #333;
  position: absolute;
  left: 0;
}

.email-link {
  color: #202020;
  text-decoration: none;
  position: relative;
  font-weight: 500;
  transition: color 0.3s ease;
  font-size: 14px;
}

.email-link:hover {
  color: #202020;
}

.link::after, .email-link::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 1px;
  bottom: -2px;
  left: 0;
  background-color: #202020;
  transform: scaleX(0);
  transition: transform 0.3s ease;
  transform-origin: left;
}

.link:hover::after, .email-link:hover::after {
  transform: scaleX(1);
}

.link, .email-link {
  color: #202020;
  text-decoration: none;
  position: relative;
  font-weight: 500;
  transition: color 0.3s ease;
  font-size: 14px;
}
</style> 
