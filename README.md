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

### **This just is a training program, please do not apply to the production environment**
### **这暂时只是个练手项目，请不要应用于生产环境**

#### 开发日志

 - 2018.10.09 重构了部分代码，并且整理了一个helper出来，之后一些主要的辅助函数会扔进去
 - 2018.10.01 深夜的时候，Rose拥有了自己的文档。
 - 2018.09.11 通过修改了一些代码来增加功能，同时优化了部分代码
 - 2018.09.01 更新了少许代码，在回到了学校之后咸鱼了很久，中间其实还commit了几次。这次主要更新了下jinja2模板函数的拓展和mongodb的搭建，之后会传结构的思维导图
 - 2018.08.15 更新昨晚写的worker，提高适用性
 - 2018.08.13 在做项目的空闲期间把路由的解析补完了，采取了类似c#的解析方法，比较美观一点，顺便做了rewrite，稍后把rewrite的防冲突补完
 - 2018.08.11 将暑假做的内容更新上github了，尝试把模组方法打包，然后把自己做的有关cmsmod的一部分放了上来。

#### 当前目标

- [x] 完成自定义拓展路由与规则解析
- [ ] cms底层api实现
- [x] 添加新线程支持woker

### 技术架构

主要架构aiohttp+vue,ui采用element-ui

### requirements

暂无整理

### Notice

 - ~~如果你需要在jinja2模板中使用异步函数，请参考[这篇文章](https://www.zybuluo.com/zxc854560673/note/1276920)（我写的 ~~新版已经使用helper覆盖掉模块了，不需要自己修改源码

### 当前状态
求实习
在做师兄的项目，所以这个练手项目会咕咕咕一下，不过会把目标做完的
