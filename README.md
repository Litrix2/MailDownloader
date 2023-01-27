注意:本人的水平还处于初级阶段,因此代码质量可能比较低下.

___

# Mail Downloader 1.4.0-Beta
Mail Downloader是一个用于自动下载邮箱附件的程序,使用IMAP协议.

**使用前请关闭代理!**

## 特性
- **支持所有邮箱普通附件、QQ邮箱超大附件、163邮箱和126邮箱超大附件、新浪邮箱超大附件、网易邮箱大师超大附件的下载.**
    - **注意: 本程序无法走代理,因此受国家与地区的影响,某些邮箱无法连接.**
- 可一次性操作多个邮箱.
- 支持搜索特定时间范围内的邮件;可切换自动/手动输入日期.
- 支持搜索特定类型邮件(全部/已读/未读).
- 多线程处理,减少下载时间.
- 在下载附件出现问题时有较好的处理能力.

## 运行
Mail Downloader 需要配置文件才能正常运行.仓库中提供一个示例配置文件,可以以此为参考进行配置.

### 加载配置
对于一般情况,只需要将配置文件更名为 config.toml,并放在程序的同一目录下,程序打开时会自动加载.

如果你想选择不同的文件来加载,则需要在终端中打开程序并输入选项:

        mail_downloader.py -c your_config.toml -r
- 选项 -c 为配置文件路径.
- 选项 -r 为指定配置文件路径相对于程序; 如果没有此选项,则配置文件路径相对于终端工作目录.
    - 当输入的路径为绝对路径时,将不受此选项的影响.
    - 配置中也有类似的选项,其方式与此相同.
    
## 程序测试环境
- Windows 10 专业版 22H2 64位
- Python 3.11.1

## 第三方库
- bs4
- lxml
- rtoml
- pytz
___

# 更新日志
## 1.4.0
- **警告**
    - **从以前的版本更新至此版本必须更新配置文件.**
    - **日志会在本地记录你的邮箱名、部分邮件信息,请注意保护隐私!**

- 新增操作: 工具
    - 新增工具: 列出邮箱文件夹
- 新增功能: 静默下载模式
    - 开启时,自动执行下载操作,不会询问任何信息,且在操作结束后自动退出.
- 新增功能: 日志
- 新增: 可分邮箱选择检索的邮箱文件夹
    - 要查看文件夹的名称,请使用 "列出邮箱文件夹"工具.
- 新增功能: 过滤器
    - 支持根据发件人名称、发件人邮箱地址、邮件主题分邮箱进行过滤.
- 新增功能: 分类
    - 可根据MIME-TYPE与文件名对附件选择不同下载文件夹.
- 改进: 现在支持搜索已读邮件
- 改进: 现在可设置下载时显示和记录的邮件信息
    - 支持设置是否显示与记录邮箱名称、邮件主题与时间、附件的MIME-TYPE.
- 优化: 优化时间处理方式
- 其他bug修复

## 1.3.1
- 新增: 重新显示附件下载总数
- 修改: 更改线程信息显示方式,现在只在变动时刷新
- 修复: 时间处理错误的问题
- 修复: 文件回滚机制错误的问题
- 修复: 邮件标记错误的问题
- 修复: 线程抢占任务时存在冲突的问题
- 修复: "测试连接"命令结果显示重复的问题

## 1.3.0
- **警告**
    - **从以前的版本更新至此版本必须更新配置文件.**
- **注意**
    - **受多线程影响,强制退出后下载临时文件(*.tmp)可能无法全部自动删除,请手动删除.**

- 新增: 现在处理邮件使用多线程方式
- 新增配置: thread_count
    - 说明: 处理邮件的线程数量.
    - 适量配置.
- 修改: 受多线程影响,更改下载附件输出方式

## 1.2.5
- 修复: 自动输入日期天数无法正常读取的问题

## 1.2.4
**警告: 从以前的版本更新至此版本必须更新配置文件.**

- 修改: 更改配置中部分选项名称
- 修复: 附件下载失败并回滚后文件下载数量可能错误的问题

## 1.2.3
**警告: 从以前的版本更新至此版本必须更新配置文件.**

- 新增配置: rollback_when_download_failed
    - 说明: 当邮件中任意附件下载失败时,删除该邮件中所有已下载的附件.
    - 该功能非新增功能.
- 紧急修复: 输出附件下载问题时出现错误

## 1.2.2 
- 新增: 添加对新浪邮箱的超大附件下载支持
- 修复: 在某些情况下超大附件文件名解析错误的问题

## 1.2.1
- 新增: 显示附件全部不存在或过期的邮件
    - 如果sign_unseen_tag_after_downloading为true,则提示是否设置"已读"标签.
- 新增: 现在会处理下载失败的超大附件

## 1.2
- 新增: 添加对163邮箱、126邮箱、网易邮箱大师的超大附件下载支持
- 新增: 遇到无法下载的超大附件时会显示错误代码与原因
    - 已删除的与已过期的超大附件不会显示.

## 1.1
- 新增功能: 测试连接
- 新增功能: 清屏
- 新增: 可选择是否标记有无法直接下载的附件的邮件
- 新增: 显示邮件发送时间
- 优化邮件下载逻辑.
- 修复部分Bug.
