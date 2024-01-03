# 将微信读书划线和笔记同步到Notion


本项目通过Github Action每天定时同步微信读书划线到Notion。

预览效果：https://book.malinkang.com

> [!WARNING]  
> 请不要在Page里面添加自己的笔记，有新的笔记的时候会删除原笔记重新添加。


## 使用

使用文档：https://malinkang.com/posts/weread2notion/

热力图使用文档：https://malinkang.com/posts/github_heatmap/

## 捐赠

如果你觉得本项目帮助了你，请作者喝一杯咖啡，你的支持是作者最大的动力。本项目会持续更新。

![](./asset/WechatIMG27.jpg)

## 问题解答

1. 如果发现数据没有同步，请点击Action查看运行状态。红色表示失败，绿色代表成功，如果有失败的点击去查看详情，检查值是否填写正确
2. Categories is expected to be select. 这个是模板设置的问题，将模板中的Categories修改为Multi-select类型
3. 模板中的属性解释
    * BookName：书名
    * BookId：书Id
    * Sort：主要用于增量同步没啥实际意义
    * Cover：封面
    * Author：作者
    * Status：状态
    * ReadingTime：阅读时长
    * Date：读完日期
    * Rating：评分
    * URL：网页链接
    * Categories：分类
    * Progress：阅读进度


## 微信群
> [!WARNING]  
> 微信群已满，加我备注微信读书，我拉你进群。
> 也可以加TG群：https://t.me/wereadnotion

 ![image](./asset/WechatIMG24.jpg)
