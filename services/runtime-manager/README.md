# RuntimeManager

`RuntimeManager` 是 crewclaw runtime 的内部容器执行层


## 项目边界

负责：
- 创建、启动、停止、删除 runtime 容器
- 目录初始化与挂载前置准备
- 连接共享网络并返回容器内部访问地址
- 暴露容器状态（`creating | running | stopped | error | deleted`）

不负责：
- 生成业务 ID（如 `runtimeId`、`volumeId`）
- 业务真相持久化
- 普通用户配置管理
- 浏览器直接访问接口
