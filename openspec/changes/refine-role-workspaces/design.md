## Context
见proposal。当前401在request中提前统一抛未登录；App与Materials/Ask都含header；Tutor共用teacher/student并同用技能source/id。本次已重取2026-10-14课件全页、清单与原型OpenAPI，参考用户截图1/2/3/4/11的布局，不引入原型非本课应用。
## Goals / Non-Goals
目标：清晰角色流程和可验证交互；Non-goals见proposal。学生并行流与数据隔离必须保持。
## Decisions
- 单一App shell负责导航/身份/主题/登出，学生首页Tutor、教师首页Teacher；页面仅承载业务，不重复header。
- 教师工作台拆Teacher.tsx，技能列表＋独立编辑抽屉/新建表单；启停通过源文件的启用字段PUT，删除确认。学生Tutor保留每会话状态与AbortController，标签单焦点、并排可切换；切换资料页保持Tutor挂载。
- RequireStudent服务端保护四个conversation接口；更新处理器注解与测试，教师403是用户明确要求，比课程示例更窄。
- 登录401单独展示通用账号/密码错误，不走会话过期回调；仍不区分账号是否存在/限流。受保护401行为不变。
- 资料阅读两栏，分类由标题纯函数推导；ReactMarkdown不接rawHTML，详情/搜索用请求序号避免竞态；鉴权blob下载即时撤销对象URL。
- 图标为本地SVG组件、CSS主题变量与系统字体，避免装饰性AI位图/CDN依赖；移动端折叠列布局。
## Risks / Trade-offs
- 现有测试资料/智能体不会自动删；历史列表改成独立滚动并支持搜索缓解拥挤。
- 标题分类不是正式学科元数据，未匹配归其他；不添加未经确认的个人资料编辑。
- 关闭对话标签仅收起，不删记录；显式停止才取消请求。
## Migration Plan
无数据迁移；重新构建web/api，保留数据库和上传卷。长期主规约与旧归档不写回。
