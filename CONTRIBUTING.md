# 贡献与维护

[← 总目录](README.md)

请提供条目编号、具体问题和能支持修正的原始来源。不要上传真实个人账户、医疗资料、证件或案件细节。没有公开依据的个人经验可作为选题线索，但不能直接改成事实建议。

## 内容源与生成文件

编辑 `sources/guide.json`，然后使用 Python 3.10 或更高版本运行：

```sh
python tools/test_validation.py
python tools/build.py
python tools/validate.py
```

`book/*.md`、`sources/README.md`、`docs/ADAPTATION.md`、`README.md` 和 `assets/data.js` 由构建器生成，不要只改这些文件。`sources/upstream.json` 保存原始条目编号和固定版本，后续升级上游时必须重新核对对照表。

来源记录必须有真实访问日期、读取范围和能支持的具体内容。新来源应使用未占用的 ID；既有条目 ID 保持稳定，方便读者链接和两个语言版本以后共享事实记录。

## 本地阅读器

```sh
python -m http.server 4187 --bind 127.0.0.1
```

打开 `http://127.0.0.1:4187/`。检查中文和英文搜索、章节及地区过滤、展开正文、引用链接、重置筛选、浏览器前进后退以及窄屏显示。网站不读取用户账户、不上传搜索内容，不使用分析追踪。

## 发布前

结构校验通过后，仍须阅读变更涉及的来源并核对正文。请在变更中说明法律或政策生效时间、适用资格、费用口径和例外。法规和医学建议的重大变动应接受相关专业人士复核。

GitHub Pages 可从 `main` 分支根目录发布。无需安装网站依赖，仓库根目录的 `.nojekyll` 保留。
