# 简历管理系统复刻版

本项目复刻截图中的简历管理系统，包含：

- 后端：Java 21 + Spring Boot 3.5 + MyBatis + H2
- 前端：Vue 3 + Vite + Axios
- 功能：简历库筛选/分页/详情、状态统计、微信聊天机器人列表、初始化模拟数据

## 目录结构

```text
backend/   Spring Boot + MyBatis REST API
frontend/  Vue3/Vite 管理后台页面
```

## 本地启动

### 1. 启动后端

```bash
cd backend
./mvnw spring-boot:run
```

后端地址：`http://localhost:8080`

H2 控制台：`http://localhost:8080/h2-console`

- JDBC URL: `jdbc:h2:mem:resume_manager`
- User: `sa`
- Password: 空

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

前端地址：`http://localhost:5173`

## 常用 localhost 接口

```text
GET    http://localhost:8080/api/health
GET    http://localhost:8080/api/resumes?page=1&size=8
GET    http://localhost:8080/api/resumes/stats
GET    http://localhost:8080/api/resumes/{id}
POST   http://localhost:8080/api/resumes
PUT    http://localhost:8080/api/resumes/{id}
PATCH  http://localhost:8080/api/resumes/{id}/status
DELETE http://localhost:8080/api/resumes/{id}

GET    http://localhost:8080/api/chatbots?page=1&size=12
GET    http://localhost:8080/api/chatbots/{id}
POST   http://localhost:8080/api/chatbots
PATCH  http://localhost:8080/api/chatbots/{id}/status
```

简历筛选参数支持：`keyword`、`status`、`gender`、`education`、`communicationStatus`、`minAge`、`maxAge`、`page`、`size`。

## 已验证

```bash
cd backend && ./mvnw test
cd frontend && npm run build
```
# UserAPI1
A little REST API
