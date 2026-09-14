# 更新第三版，提高读书稳定程度，最大限量保持cookie有效时间，欢迎fork！

## 项目介绍 📚

这个脚本主要是为了在微信读书的阅读**挑战赛中刷时长**和**保持天数**。由于本人偶尔看书时未能及时签到，导致入场费打了水漂。网上找了一些，发现高赞的自动阅读需要挂阅读器模拟或者用ADB模拟，实现一点也不优雅。因此，我决定编写一个自动化脚本。通过对官网接口的抓包和JS逆向分析实现。

该脚本具备以下功能：

- **阅读时长调节**：默认 68 分钟，可通过仓库变量或手动运行参数调节。
- **定时运行**：可部署在 GitHub Actions 或服务器上，每天自动执行。
- **Cookie刷新**：每次运行会尝试刷新会话密钥；登录整体失效后仍需重新抓取 Cookie。
- **轻量化设计**：本脚本实现了轻量化的编写，部署服务器/GIthub action后到点运行，无需额外硬件。

***
## 操作步骤 🛠️

### 抓包准备

脚本逻辑还是比较简单的，`main.py`与`push.py`代码不需要改动。在微信阅读官网 [微信读书](https://weread.qq.com/) 搜索【三体】点开阅读点击下一页进行抓包，抓到`read`接口 `https://weread.qq.com/web/book/read`，如果返回格式正常（如：

```json
{
  "succ": 1,
  "synckey": 564589834
}
```
右键复制为Bash格式。

### 方法一：GitHub Actions（电脑关机也能运行）

1. 建议复制到只有自己能访问的仓库。不要把 Cookie 写进代码、Issue、提交记录或 Actions 日志。
2. 打开仓库 **Settings → Secrets and variables → Actions → Secrets**，新建 Repository secret：
   - 名称：`WXREAD_CURL_BASH`
   - 值：上面从 `read` 请求复制的完整 Bash cURL。程序只解析它，不会把它当作命令执行。
3. 可选：在同一页面的 **Variables** 新建 `READ_MINUTES`，值为 `1` 到 `80`。不配置时为 `68`。
4. 打开 **Actions → WeRead daily → Run workflow** 进行一次手动验证。手动运行时也可临时填写分钟数。

工作流会按 `Europe/Brussels` 时区每天 07:00 触发，并自动适配夏令时。GitHub 定时任务可能因平台负载而延迟，并不保证分秒准时。公开仓库连续 60 天没有活动时，GitHub 可能自动停用定时工作流，需要到 Actions 页面重新启用。工作流权限仅为 `contents: read`，依赖和官方 Actions 均已固定版本；未使用第三方 keepalive、DNS 改写或通知服务。

Cookie 属于账户登录凭据。即使放在 GitHub Secret 中也应限制仓库协作者、谨慎审查后续代码变更；失效后需要重新抓取并替换该 Secret。

### 视频教程

[![视频教程](https://github.com/user-attachments/assets/ec144869-3dbb-40fe-9bc5-f8bf1b5fce3c)](https://www.bilibili.com/video/BV1kJ6gY3En3/ "点击查看视频")


### 方法二： 服务器运行（docker部署）

- 在你的服务器上有Python运行环境即可，使用`cron`定义自动运行。
- 或者通过docker运行，将抓到的bash命令在 [Convert](https://curlconverter.com/python/) 转化为Python字典格式，复制需要的headers与cookies即可（data不需要）。

steps1：克隆这个项目：`git clone https://github.com/findmover/wxread.git`<br>
steps2：通过环境变量配置 `WXREAD_CURL_BASH` 和可选的 `READ_MINUTES`；不要把 Cookie 写进镜像或源码<br>
steps3：进入目录使用镜像构建容器：
`docker rm -f wxread && docker build -t wxread . && docker run -d --name wxread -v $(pwd)/logs:/app/logs --restart always wxread`<br>
steps4：测试：`docker exec -it wxread python /app/main.py`

***
## Attention 📢

1. **签到次数调整**：只需签到完成挑战赛可以将`num`次数从120调整为2，每次`num`为30秒，200即100分钟。
   
2. **解决阅读时间问题**：对于issue中提出的“阅读时间没有增加”，“增加时间与刷的时间不对等”建议保留`config.py`中的【data】字段，默认阅读三体，其它书籍自行测试。

3. **GitHub Action部署/本地部署**：统一通过环境变量传入登录信息；不要在 `config.py` 中保存 Cookie。

4. **推送**：pushplus推送偶尔出问题，猜测是GitHub action环境问题，增加重试机制。并增加wxpusher的极简推送方式。


***
## 字段解释 🔍

| 字段 | 示例值 | 解释 |
| --- | --- | --- |
| `appId` | `"wbxxxxxxxxxxxxxxxxxxxxxxxx"` | 应用的唯一标识符。 |
| `b` | `"ce032b305a9bc1ce0b0dd2a"` | 书籍或章节的唯一标识符。 |
| `c` | `"0723244023c072b030ba601"` | 内容的唯一标识符，可能是页面或具体段落。 |
| `ci` | `60` | 章节或部分的索引。 |
| `co` | `336` | 内容的具体位置或页码。 |
| `sm` | `"[插图]威慑纪元61年，执剑人在一棵巨树"` | 当前阅读的内容描述或摘要。 |
| `pr` | `65` | 页码或段落索引。 |
| `rt` | `88` | 阅读时长或阅读进度。 |
| `ts` | `1727580815581` | 时间戳，表示请求发送的具体时间（毫秒级）。 |
| `rn` | `114` | 随机数或请求编号，用于标识唯一的请求。 |
| `sg` | `"bfdf7de2fe1673546ca079e2f02b79b937901ef789ed5ae16e7b43fb9e22e724"` | 安全签名，用于验证请求的合法性和完整性。 |
| `ct` | `1727580815` | 时间戳，表示请求发送的具体时间（秒级）。 |
| `ps` | `"xxxxxxxxxxxxxxxxxxxxxxxx"` | 用户标识符或会话标识符，用于追踪用户或会话。 |
| `pc` | `"xxxxxxxxxxxxxxxxxxxxxxxx"` | 设备标识符或客户端标识符，用于标识用户的设备或客户端。 |
| `s` | `"fadcb9de"` | 校验和或哈希值，用于验证请求数据的完整性。 |
