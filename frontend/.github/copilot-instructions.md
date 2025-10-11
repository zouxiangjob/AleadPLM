# Copilot Instructions for BOM Frontend (Vue 3 + Vite)

## 项目架构与核心约定
- 本项目为基于 Vue 3 + Vite 的前端，采用单页应用（SPA）结构，主入口为 `src/App.vue`，页面通过 `vue-router` 切换。
- 主要业务组件为 `src/components/BOMTreeTable.vue`，负责 BOM（物料清单）树与表格的增删改查。
- API 请求统一通过 `src/api/index.js`（axios 实例，baseURL 指向本地后端）。
- UI 框架为 Element Plus，所有弹窗、表格、按钮等均用其组件实现。

## 关键目录与文件
- `src/components/BOMTreeTable.vue`：核心业务组件，包含 BOM 树、表格、弹窗、交互逻辑。
- `src/api/index.js`：axios 封装，所有 API 调用均应通过此实例。
- `src/router/index.js`：路由配置，默认路由指向 BOMTreeTable。
- `src/main.js`：应用入口，注册 Element Plus、路由等。
- `vite.config.js`：Vite 配置，开发端口 5173。

## 主要开发模式与约定
- 组件开发采用 `<script setup>` 语法糖，推荐组合式 API。
- 所有 API 调用建议封装为 async 函数，错误通过 Element Plus 的 `ElMessage` 反馈。
- 弹窗确认操作统一用 `ElMessageBox.confirm`。
- 表格数据与树数据均为响应式（ref），通过 API 拉取并同步。
- 组件样式采用 scoped CSS，布局主容器类为 `.bom-container`，卡片间距通过 `gap` 控制。

## 常用开发命令
- 启动开发环境：`npm run dev`
- 打包生产环境：`npm run build`
- 预览生产包：`npm run preview`

## 典型交互流程
- 加载页面时自动请求产品及 BOM 数据，渲染树和表格。
- "增加"按钮弹出选择产品弹窗，确认后通过 API 更新 BOM。
- "移去"按钮支持多选，弹窗确认后批量删除 BOM 关系。
- 所有数量输入均支持 3 位小数，使用 `el-input-number` 控件。

## 代码风格与特殊约定
- 变量、方法命名以小驼峰为主，API 数据字段与后端保持一致。
- 组件间通信主要通过 props 和事件（本项目目前为单组件主导）。
- 若需扩展页面，建议新增组件并通过路由管理。

## 外部依赖与集成
- 依赖 Element Plus、axios、vue-router。
- 后端 API 地址默认 `http://127.0.0.1:8000/api/`，如需更改请修改 `src/api/index.js`。

---
如需了解更多约定，请参考 `src/components/BOMTreeTable.vue` 及 `src/api/index.js` 的具体实现。
