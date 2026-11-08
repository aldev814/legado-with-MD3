# 掌阅水波纹自动补丁发布

上游为 `HapeLee/legado-with-MD3`，发布目标仅为 `aldev814/legado-with-MD3`。
默认分支 `main` 保存发布配方；补丁源码在各个 Release 标签中，自动化不合并上游 main，也不覆盖默认分支。

## 流程

- 每小时第 23 分钟检查上游最新的已发布正式 Release，不追踪 main、draft 或 prerelease。
- 支持 Actions → **iReader - Patch and release upstream stable** 手动运行；`upstream_tag` 留空取最新正式版。
- Gradle wrapper 保持上游下载地址和 SHA256，下载超时调整为 120 秒、重试 3 次，避免首次冷下载的 10 秒超时。
- 从检测时解析出的完整 commit SHA 检出上游，然后按顺序 `git apply --3way --index` 应用补丁；冲突即失败，不跳过补丁。
- core/comic 分别运行 JDK 21、完整 Debug 单元测试、lint、架构检查和 Release/R8 构建。每个产品单独 runner，单 worker，Kotlin 堆上限 6GB。
- 用固定签名签署并验证六个 APK：每个产品各 universal、arm64-v8a、armeabi-v7a；校验包名、版本名、versionCode、证书和 16KB ZIP 对齐。
- 两个产品必须具有相同源码、版本和签名，才创建 Release。附带两个产品各自的 R8 mapping、SHA256SUMS、构建元数据和补丁 ZIP。
- 标签指向实际打补丁后的独立源码快照，不包含上游工作流或其历史。GitHub 的源码 ZIP 即该快照。
- 已发布版本不覆盖、不强推标签；draft 可恢复。更新清单失败会在后续定时检查时重试。
- 只有发布和更新清单任务拥有仓库写权限。构建任务只读，签名 Secrets 只传给签名步骤。

配方分支 `codex/ireader-automation` 的 push 会完整构建验证并保留 Actions artifacts，但不会发布。
只有 `main` 才发布。其他工作流中的原作者条件、网站、Telegram、旧自动同步任务已从本 fork 的配方分支移除。

## 应用身份和更新

- 独立 `applicationId` 为 `io.legato.kazusa.ireader`，代码 namespace 仍为 `io.legado.app`；名称仍为“阅读”，没有 Debug 的 D 标记。
- 可与原版和阅读·D 共存。首次使用可通过应用内备份/恢复迁移数据。
- 独立包名不复用上游 Firebase 项目；显式禁用该能力并隐藏匿名统计开关。
- 应用内更新只检查本 fork；继续沿用 core/comic 和 CPU 架构筛选，不会更新成上游无补丁包。
- 使用配置中的公开证书指纹识别本 fork 的正式签名，以保证默认正式版更新频道可用。自动化仅发布正式版，更新频道请选择正式版。
- 首版为 `3.26.23-ireader.1`。同上游补丁修订递增为 `.2`、`.3`；下一个上游为 `3.26.24-ireader.1`，版本比较使用数值修订号。
- versionCode 为 `major*100000000 + minor*1000000 + patch*1000 + revision`；两个产品一致。支持 major 0..20、minor 0..99、patch 0..999、revision 1..999，超出即停止而不是溢出。
- 补丁、签名身份或构建行为变更后必须提高 `config.json` 的 `patch_revision`，不覆盖旧版。

## 固定签名

GitHub Repository secrets：`IREADER_KEYSTORE_BASE64` 和 `IREADER_KEYSTORE_PASSWORD`。

```sh
python3 .github/ireader/setup_signing.py --upload
```

脚本创建或复用 `~/.config/legado-ireader-signing/` 内的固定 PKCS12 密钥，alias 为 `ireader`。
私钥和密码不输出、不提交；目录权限 700，私有文件权限 600。请私下备份此目录，后续不要重新生成密钥。
脚本会拒绝覆盖残缺的已有密钥。公开证书 SHA256 必须同时匹配 `config.json` 和身份补丁，签名验证不匹配就停止。

## 配方维护与验证

`0001-smartos-water-ripple.patch` 是已验证正文水波纹改动，基于上游正式版 `3.26.23` / `35d013a0803931c333156d847ef1d1f3f324d83f`。
`0002-fork-identity.patch` 配置独立包名、更新仓库、正式证书以及 fork 版本比较测试。修订 2 适配上游 `3.26.24`：仅在 Firebase 搜索包装调用前增加能力条件，不重排开关内部代码，以减少后续上游 UI 变更造成的冲突。
`0003-upstream-footer-test.patch` 仅修正上游漫画页脚测试的三处页码查询：新版动画文字已将语义合并为 `1/57`，测试也按完整页码查询；原有位置、对齐和隐藏断言全部保留，不修改漫画功能。

```sh
python3 -m unittest discover -s .github/ireader/tests -v
go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/ireader-ci.yml .github/workflows/ireader-release.yml
git diff --check
```

在干净且完整历史的上游 Release 检出目录中验证补丁：

```sh
python3 /path/to/control/.github/ireader/prepare_source.py /path/to/source /path/to/release-plan.json
```

发布参数、补丁 SHA256、准确上游与配方及源码 commit、公开签名指纹都保存在 `build-metadata.json`。
补丁冲突后修改配方并增加修订号，再重新验证。不能删除测试或跳过 R8/签名检查来放行发布。

GitHub 定时任务只读取默认分支，可能延迟；长期不活跃的公共仓库可能暂停定时任务。
参考：[GitHub Actions schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。
