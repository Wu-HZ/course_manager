# 自动排课系统

基于 Django + Vue + OR-Tools CP-SAT 的智能排课系统

## 项目结构

```
course_manager/
├── backend/          # Django 后端
│   ├── config/       # Django 配置
│   ├── core/         # 核心数据模型
│   ├── scheduler/    # 排课引擎
│   ├── venv/         # Python 虚拟环境
│   ├── manage.py
│   └── seed_data.py  # 测试数据
└── frontend/         # Vue 前端
    ├── src/
    ├── package.json
    └── vite.config.js
```

## 功能特性

- **数据管理**: 教师、班级、课程、场地、出差分组管理
- **智能排课**: 基于 OR-Tools CP-SAT 约束求解器
- **硬约束**:
  - 周课时满足
  - 班级/教师时间互斥
  - 教师禁排日
  - 场地容量限制
  - 单日课程上限
  - 班会自动锁定
- **软约束优化**:
  - 语文数学上午优先
  - 连堂课连续排列
  - 课程均匀分布
- **课表展示**: 按班级/教师查看课表

## 快速开始

### 1. 后端启动

```bash
cd backend

# 确保虚拟环境已创建和依赖已安装
# venv 已存在,依赖已安装 (Django, djangorestframework, django-cors-headers, ortools)

# 启动开发服务器
venv\Scripts\python manage.py runserver
```

后端将运行在 http://127.0.0.1:8000

- 管理后台: http://127.0.0.1:8000/admin
  - 用户名: `admin`
  - 密码: `admin`

### 2. 前端启动

```bash
cd frontend

# 安装依赖 (首次运行)
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:5173

## 测试数据

已创建测试数据包括:
- 7 名教师 (张老师、李老师、王老师、赵老师、陈老师、刘老师、孙老师)
- 3 个班级 (一(1)班、一(2)班、一(3)班)
- 7 门课程 (语文、数学、英语、体育、音乐、美术、班会)
- 2 个出差分组 (周三组、周五组)
- 21 条授课分配

## 使用流程

1. **数据准备**
   - 访问数据管理页面录入/修改数据
   - 或使用 Django Admin 后台管理

2. **执行排课**
   - 进入"执行排课"页面
   - 设置求解时限
   - 点击"开始排课"
   - 等待排课完成

3. **查看课表**
   - 进入"课表查看"页面
   - 选择排课结果
   - 按班级或教师查看课表

## 时间片设置

- 周一至周四: 每天 6 节课 (上午 4 节, 下午 2 节)
- 周五: 4 节课 (上午 3 节, 第 4 节为班会)
- 总计: 28 个时间片/周

## 技术栈

### 后端
- Django 6.0.1
- Django REST Framework 3.16
- OR-Tools 9.15 (Google 优化工具)
- SQLite 数据库

### 前端
- Vue 3
- Element Plus (UI 组件库)
- Vue Router
- Pinia (状态管理)
- Axios

## API 端点

### 核心数据
- `/api/teachers/` - 教师 CRUD
- `/api/classes/` - 班级 CRUD
- `/api/subjects/` - 课程 CRUD
- `/api/locations/` - 场地 CRUD
- `/api/travel-groups/` - 出差分组 CRUD
- `/api/class-subject-teachers/` - 授课分配 CRUD

### 排课
- `POST /api/scheduler/run/` - 执行排课
- `GET /api/scheduler/results/` - 获取排课结果列表
- `GET /api/scheduler/results/{id}/` - 获取单个排课结果
- `POST /api/scheduler/results/{id}/activate/` - 激活排课结果
- `GET /api/scheduler/active/` - 获取当前激活的排课
- `GET /api/scheduler/results/{result_id}/class/{class_id}/` - 班级课表
- `GET /api/scheduler/results/{result_id}/teacher/{teacher_id}/` - 教师课表

## 排课约束说明

### 硬约束 (必须满足)
1. **H1 - 周课时**: 每班每课的周课时必须等于设定值
2. **H2 - 班级互斥**: 同一班级同一时间只能上一门课
3. **H3 - 教师互斥**: 同一教师同一时间只能教一个班
4. **H4 - 禁排日**: 教师在禁排日当天不排课
5. **H5 - 场地容量**: 同时使用同类场地的课程不超过容量限制
6. **H6 - 班会锁定**: 周五第 4 节自动锁定为班会课
7. **H8 - 单日上限**: 同课同班一天不超过设定上限

### 软约束 (优化目标)
1. **S1 - 上午优先**: 语文、数学等课程尽量安排在上午
2. **S2 - 连堂偏好**: 允许连堂的课程奖励相邻时间片
3. **S3 - 均匀分布**: 惩罚同一天排过多同一课程

## 故障排除

### 排课失败
- 检查是否所有班级都分配了课程和教师
- 检查禁排日设置是否合理
- 检查周课时总和是否超过可用时间片
- 查看错误信息了解具体原因

### 前端无法连接后端
- 确保后端已启动在 8000 端口
- 检查 CORS 设置
- 查看浏览器控制台错误信息

## 开发计划

### 已完成
- ✅ 核心数据模型
- ✅ OR-Tools 排课引擎
- ✅ RESTful API
- ✅ 前端页面框架
- ✅ 数据管理功能
- ✅ 排课执行和结果展示

### 待完善
- ⏳ 合班课功能 (框架已搭建)
- ⏳ 手动调课功能
- ⏳ 课表导出 (PDF/Excel)
- ⏳ 冲突检测和报告
- ⏳ 多周轮换展示

## 许可证

MIT License

## 作者

Claude Code - 自动排课系统实现
