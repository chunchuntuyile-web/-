# -该项目仅用于展示,学习使用
(注明：项目由gemini协助在两天时间内完成)（前端界面并未实现布局优化）
实际功能如下：
1.语音翻译
2.在线视频实时翻译
3.语音聊天室

前端界面展示：

<img width="667" height="423" alt="image" src="https://github.com/user-attachments/assets/d5279b7d-d55c-4767-8852-22be3ad7e4d4" />

点击右上角对应的切换，就可以到不同的用户

<img width="666" height="369" alt="image" src="https://github.com/user-attachments/assets/a4d93380-aca2-4005-a534-ee89e5ced8d2" />

比较简陋，但是内部功能挺全的（主要是写完之后懒得优化）
这里演示使用管理员登录（管理员账号密码写死了账号admin，密码：admin123，也可以在后端改，好吧，反正我觉得管理员就应该是固定密码，要不怎么突出管理权限这个等级呢）

这里还有个直观的数据大盘，就是用来凑数的（当然，大盘仅管理员登录可见）

<img width="596" height="459" alt="image" src="https://github.com/user-attachments/assets/f5d4faea-211f-42a0-8794-865f5bee2126" />


功能模块展示：
1.语音翻译

<img width="658" height="475" alt="image" src="https://github.com/user-attachments/assets/91cf2867-19be-44ed-8090-8119f9de99ac" />

具体就是点击麦克风输入，然后对着正在录音（一定是正在录音的那个，设置里面看清楚）的麦克风说话，可以将200多种语言翻译成以下四种

<img width="604" height="112" alt="image" src="https://github.com/user-attachments/assets/c7e8f3b3-fb1f-45e5-a90e-6a4918e57704" />

只有以下四种是因为我还做了TTS（语音合成），就是翻译之后，然机器读一遍，但是我这个基于微软的语音包，下载挺慢的，时间比较紧，所以就加了4种

然后可以在最下面找到历史记录

<img width="645" height="402" alt="image" src="https://github.com/user-attachments/assets/b266c073-5d2c-4aa2-bc93-402c0b1808ca" />

这里面储存的是用户翻译的记录（不同普通用户只能看到自己翻译的，但是管理员可以看到所有人翻译的）

2.在线视频实时翻译
点击功能模块上的

<img width="679" height="89" alt="image" src="https://github.com/user-attachments/assets/92384523-9f88-430e-a997-1f1fac6a4a36" />

紧接着会弹出请求共享的一个页面（这里推荐使用比较新的浏览器，例如：chorme，像旧版本的firefox是无法共享音频的）

最好选整个屏幕，然后统一右下角的共享系统音频，当然，标签页也可以

之后会弹出一个悬浮窗口（可以置顶在页面上）

<img width="1045" height="352" alt="image" src="https://github.com/user-attachments/assets/6a7a4b9f-4ce6-488e-9cb6-8e39ccc8a6e0" />

（就好比如我现在正在写，旁边就是它，不局限于系统页面）

视频随便中一个演示下

<img width="1823" height="716" alt="image" src="https://github.com/user-attachments/assets/34d2345e-e07c-47bd-86ad-047e78bc557d" />

就比如这个youtubu上的广告，你可以看到他确实在翻译，而且他还记录历史翻译记录，还可以在功能模块哪里实时切换四种语言，想关闭它，点×就好了

3.语音聊天室

功能模块如下：

<img width="623" height="531" alt="image" src="https://github.com/user-attachments/assets/7be09133-911b-42bc-8e2a-cdafde8a07cd" />

两个不同的用户可以通过输入相同的房间号进行聊天（以user1和user3来演示）

user1heuser3都加入房间号1

现在用user3在房间内说一句话（我说了一句之后，又重新加入房间，历史会被清除，下面会看到）

<img width="608" height="523" alt="image" src="https://github.com/user-attachments/assets/e9b40494-d6dc-4ac2-bdcc-4f553a9fc013" />

现在回到user1的界面

<img width="611" height="533" alt="image" src="https://github.com/user-attachments/assets/a961d4a7-7b2d-4a40-a7e1-b2c05b2c3264" />

可以看到user1正确的接受了user3的消息，同时也可以看到在user3界面中被清除的那句话
当然这个也是支持目标语言切换的

整体项目就是这样，时间比较紧，我个人理解的是，这样还行。

最后就是一些使用AI的心得吧：
反正我用AI的时候都不是让AI直接把一个东西整体发给我，而是一步一步来

我的理解是AI读取上下文的能力还是比较有限的，如果问少一点，AI对于这个东西的关联性就更强，提出的解决方案就会更详细，目的更明确

这就好比一个人，你让他从一大篇文章里找你提出的问题，和你给他一句话，而且这句话就是问题，这完全就是两码事

前者，可能他会找一堆问题出来，然后问你是哪个，但是他的聊天字数有比较有限，他只能省略许多，然后只提问题

但你要是后者，那我知道这就是问题，完了它还可以再向你提出一些解决方案啥的（还不用一下思考那么多，专心处理一件事，效率确实会高不少）

还有就是你要做一件事的时候，一定要从基本开始，你比如你想写一个项目，你可以让AI帮你写一个最基本的框架（前端，后端，数据库）

然后你可以一代一代版本却更迭功能，没有必要一上来就把你想要的功能全写上，让他一键傻瓜生成，这样不保险没法纠错，而且也避免不了AI的欺骗性

说到欺骗性，确实，就好比如豆包，我感觉整个就是个说谎的艺术家，编个谎话还有理有据的，不管AI怎样，你这个人一定要目标明确，需求一定要准确

好多AI，用到现在，我个人觉得综合能力强一点的就是gemini了

当然，要是硬实力够的话，我的建议是不要用订阅版的，直接上google AI studio上用token计费那种的，相对来是可以调参的还是好（我还是学生，实力就那样，懂得都懂了😢）

使用订阅版时，一个对话窗口还是用来处理一整个项目某个部分就好，就好比一个对话写项目代码，再新建一个处理文档之类的，比较清晰

最后注明：该项目可能存在繁冗代码，也可能存在功能问题，见谅了啊🙏





