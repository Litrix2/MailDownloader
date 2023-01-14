注意:本人的水平还处于初级阶段,因此代码质量可能比较低下.
___

# Mail Downloader
Mail Downloader是一个用于自动下载邮箱附件的程序,使用IMAP协议.

**版本:1.0**

**配置文件名:config.toml**

**使用前请关闭代理!**

## 特性
**目前支持QQ邮箱附件和163邮箱普通附件的下载;可获取163邮箱超大附件的下载链接;GMail暂不支持.**

支持搜索特定时间范围内的邮件;可切换自动/手动输入日期.

支持搜索特定类型邮件(全部/已读).

## 程序配置
- mail:配置邮箱数据
    - host:邮箱服务器主机名
    - address:邮箱地址
    - password:邮箱密码
        - 如有特殊规定,使用邮箱授权码
- allow_manual_input_search_time:允许手动输入搜索日期
- min_search_time:自动搜索起始日期
    - **仅在allow_manual_input_search_time为false时生效**
    - 若不需要,设为false
    - 若需要,设为\[年,月,日\]
- max_search_time:自动搜索截止日期   
    - **仅在allow_manual_input_search_time为false时生效**
    - 若不需要,设为false
    - 若需要,设为\[年,月,日\]
- only_search_unseen_mails:仅搜索未读邮件
    - 为false时,搜索全部邮件
    - 为true时,仅搜索未读邮件
- sign_unseen_tag_after_downloading:在邮件内附件全部下载成功后设置"已读"标签
- reconnect_max_times:邮箱断开连接后最大重连次数
- download_path:文件下载路径
    - **请使用绝对路径**

## 依赖库
- bs4
- rtoml