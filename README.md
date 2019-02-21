# Rose


---

    A prolongable, base on aiohttp, high-performance asynchronous server framwork

    This framwork was project once time i work for my studio.I publish it just wanna it can be better.
    Sure many people have done some similar work, but i want people can use it even he do not learn anything about python.
    Just like a game, if you want to expend the server, you can change the code of it, or put the mod into plugins folder, them it will work.

一个可拓展的，基于aiohttp的，高性能的异步服务器框架

这个框架是我有一次为我工作室做的项目。我发布它只是为了让它变的更好。
当然很多人已经已经做过类似的工作了，但我想让更多人能用上它，即使他不懂任何有关python的东西。
就像一个游戏，如果你想拓展这个服务器，你可以更改它的代码，或者将模组放入plugins目录，然后它就会生效。
[相关文档](https://www.showdoc.cc/167947744523387)

### **This just is a training program, please do care to apply it to the production environment**
### **这暂时只是个练手项目，请慎重应用于生产环境**

#### 开发日志

 - 2019.02.21 发现很久没更readme了，稍微说下过去的结果。在完善api的基础上做了不少插件，如翻译插件，hot-reload插件等，目前借助该框架在写一个ftp管理系统，所以暂缓了cms系统的编写（虽然写这东西没难度纯属时间的堆积）
 - 2018.10.09 重构了部分代码，并且整理了一个helper出来，之后一些主要的辅助函数会扔进去
 - 2018.10.01 深夜的时候，Rose拥有了自己的文档。
 - 2018.09.11 通过修改了一些代码来增加功能，同时优化了部分代码
 - 2018.09.01 更新了少许代码，在回到了学校之后咸鱼了很久，中间其实还commit了几次。这次主要更新了下jinja2模板函数的拓展和mongodb的搭建，之后会传结构的思维导图
 - 2018.08.15 更新昨晚写的worker，提高适用性
 - 2018.08.13 在做项目的空闲期间把路由的解析补完了，采取了类似c#的解析方法，比较美观一点，顺便做了rewrite，稍后把rewrite的防冲突补完
 - 2018.08.11 将暑假做的内容更新上github了，尝试把模组方法打包，然后把自己做的有关cmsmod的一部分放了上来。


#### 当前目标

- [x] 完成自定义拓展路由与规则解析
- [ ] cms底层api实现（暂缓）
- [x] 添加新线程支持woker
- [x] 添加新线程支持Timer定时任务
- [x] 参考asyncio.Queue的源码写了异步字典，用于ws
- [x] 完成hot-reload，监控文件变化，实时重载路由
- [ ] 完成Ftp管理系统，至少要做到能管理用户，打算的是配合filezilla server

### 技术架构

主要架构aiohttp+vue,ui采用element-ui

### requirements

暂无整理

### Notice

 - 若使用本项目，请注意阅读文档。文档更新不一定是最新的，但是基本有什么优化我都会及时重构插件，因此请以/server/plugins文件夹中较新的插件写法为准。开发过程中强烈推荐开启hot-reload插件（在config.ini中配置），只需要保存就可自动更新路由，可搭配gulp等自动刷新浏览器从而快速开发。

### 当前状态
求实习
在做师兄的项目，所以这个练手项目会咕咕咕一下，不过会把目标做完的
