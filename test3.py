import ollama
 
# 流式输出
def api_generate(text:str):
  print(f'提问：{text}')
  prompt = """
        请帮我简要汇总下边文章的主要内容，并给出文章的tags。结果输出为json格式，其中内容汇总的key为summary，tags的key为tags。
        # javascript - 一行代码搞定禁用web开发者工具 - 南城FE - SegmentFault 思否

Created: August 5, 2024 12:15 PM
Status: Not started

在如今的互联网时代，网页源码的保护显得尤为重要，特别是前端代码，几乎就是明文展示，很容易造成源码泄露，黑客和恶意用户往往会利用浏览器的开发者工具来窃取网站的敏感信息。为了有效防止用户打开浏览器的Web开发者工具面板，今天推荐一个不错的npm库，可以帮助开发者更好地保护自己的网站源码，本文将介绍该库的功能和使用方法。

## 功能介绍

npm库名称：`disable-devtool`，github地址：`github.com/theajack/disable-devtool`。从f12按钮，右键单击和浏览器菜单都可以禁用Web开发工具。

> 🚀 一行代码搞定禁用web开发者工具
> 

该库有以下特性:

- 支持可配置是否禁用右键菜单
- 禁用 f12 和 ctrl+shift+i 等快捷键
- 支持识别从浏览器菜单栏打开开发者工具并关闭当前页面
- 开发者可以绕过禁用 (url参数使用tk配合md5加密)
- 多种监测模式，支持几乎所有浏览器（IE,360,qq浏览器,FireFox,Chrome,Edge…）
- 高度可配置、使用极简、体积小巧
- 支持npm引用和script标签引用(属性配置)
- 识别真移动端与浏览器开发者工具设置插件伪造的移动端，为移动端节省性能
- 支持识别开发者工具关闭事件
- 支持可配置是否禁用选择、复制、剪切、粘贴功能
- 支持识别 eruda 和 vconsole 调试工具
- 支持挂起和恢复探测器工作
- 支持配置ignore属性，用以自定义控制是否启用探测器
- 支持配置iframe中所有父页面的开发者工具禁用

## 使用方法

使用该库非常简单，只需按照以下步骤进行操作：

### 1.1 npm 引用

推荐使用这种方式安装使用，使用script脚本可以被代理单独拦截掉从而无法执行。

```
npm i disable-devtool
```

```
import DisableDevtool from 'disable-devtool';

DisableDevtool(options);
```

### 1.2 script方式使用

```
<script disable-devtool-auto src\='https://cdn.jsdelivr.net/npm/disable-devtool'\></script\>
```

或者通过版本引用:

```
<script disable-devtool-auto src\='https://cdn.jsdelivr.net/npm/disable-devtool@x.x.x'\></script\>

<script disable-devtool-auto src\='https://cdn.jsdelivr.net/npm/disable-devtool@latest'\></script\>
```

### 1.3 npm 方式 options参数说明

options中的参数与说明如下，各方面的配置相当完善。

```
interface IConfig {
    md5?: string;
    url?: string;
    tkName?: string;
    ondevtoolopen?(type: DetectorType, next: Function): void;
    ondevtoolclose?(): void;
    interval?: number;
    disableMenu?: boolean;
    stopIntervalTime?: number;
    clearIntervalWhenDevOpenTrigger?: boolean;
    detectors?: Array<DetectorType\>;
    clearLog?: boolean;
    disableSelect?: boolean;
    disableCopy?: boolean;
    disableCut?: boolean;
    disablePaste: boolean;
    ignore?: (string|RegExp)\[\] | null | (()=>boolean);
    disableIframeParents?: boolean;
    timeOutUrl?:
}

enum DetectorType {
  Unknown = -1,
  RegToString = 0,
  DefineId,
  Size,
  DateToString,
  FuncToString,
  Debugger,
  Performance,
  DebugLib,
};
```

### 1.4 script 方式使用属性配置

```
<script
    disable-devtool-auto
    src\='https://cdn.jsdelivr.net/npm/disable-devtool'
    md5\='xxx'
    url\='xxx'
    tk-name\='xxx'
    interval\='xxx'
    disable-menu\='xxx'
    detectors\='xxx'
    clear-log\='true'
    disable-select\='true'
    disable-copy\='true'
    disable-cut\='true'
    disable-paste\='true'
></script\>
```

### 1.5 事件监听

ondevtoolopen 事件的回调参数就是被触发的监测模式。可以在 ondevtoolopen 里执行业务逻辑，比如做数据上报、用户行为分析等。

```
DisableDevtool({
    ondevtoolopen(type, next){
        alert('Devtool opened with type:' + type);
        next();
    }
});
```

### 1.6 md5 与 tk 绕过禁用

该库中使用 key 与 md5 配合的方式使得开发者可以在线上绕过禁用。

流程如下：

先指定一个 key a（该值不要记录在代码中），使用 md5 加密得到一个值 b，将b作为 md5 参数传入，开发者在访问 url 的时候只需要带上url参数 ddtk=a，便可以绕过禁用。

disableDevtool对象暴露了 md5 方法，可供开发者加密时使用：

```
DisableDevtool.md5('xxx');
```

更多细节可查阅官方文档，中文文档地址：`https://github.com/theajack/disable-devtool/blob/master/README.cn.md`

## 最后

尽管该库可以有效地禁用浏览器的开发者工具面板，但仍然需要注意以下几点：

- 该库只能禁用开发者工具的面板，无法阻止用户通过其他途径访问网页源码。因此，建议结合其他安全措施来保护网站。
- 禁用开发者工具可能会对网站的调试和维护造成一定的困扰。需要调试线上代码的时候可以使用上述1.6绕过禁用进行调试。
- 该库仅适用于现代浏览器，对于一些较旧的浏览器可能存在兼容性问题。在使用前请确保测试过兼容性。

为了进一步加强网页源码的安全性，我们可以采取以下额外措施：

- **加密敏感代码**，使用加密算法对关键代码进行加密，以防止非授权访问和修改。
- **使用服务器端渲染**，将网页的渲染过程放在服务器端，只返回最终渲染结果给客户端，隐藏源代码和逻辑。
- **定期更新代码**，定期更新代码库以充分利用新的安全特性和修复已知漏洞。

保护网页源码的安全性对于Web开发至关重要。通过使用npm库`disable-devtool`，并结合其他安全措施，我们可以有效地降低用户访问和修改源代码的风险。但是绝对的安全是不存在的，因此定期更新和加强安全性措施也是必要的。

"""

 
  content = ollama.generate(
    stream=False,
    model='qwen2:7b',
    prompt=prompt
  )
  print(content)
 
 
if __name__ == '__main__':
  # 流式输出
  api_generate(text='天空为什么是蓝色的？')
 
  # 非流式输出
#   content = ollama.generate(model='gemma2:27b', prompt='天空为什么是蓝色的？')
#   print(content)