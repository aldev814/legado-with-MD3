#!/usr/bin/env python3
"""Require both products from identical source, version and signing identity before publishing."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def merge(packages, output):
    metadata = []
    for product in ['core', 'comic']:
        directory = packages / ('ireader-build-' + product)
        item = json.loads((directory / f'metadata-{product}.json').read_text())
        if item.pop('product') != product:
            raise ValueError('Product metadata mismatch')
        metadata.append(item)
    if metadata[0] != metadata[1]:
        raise ValueError('Products differ in source, version or certificate')
    for name in ['patched-source.bundle', 'ireader-patches.zip']:
        if (packages / 'ireader-build-core' / name).read_bytes() != (packages / 'ireader-build-comic' / name).read_bytes():
            raise ValueError('Product provenance differs: ' + name)
    plan = metadata[0]
    output.mkdir(parents=True, exist_ok=False)
    for product in ['core', 'comic']:
        directory = packages / ('ireader-build-' + product)
        expected = {f"legado-{plan['release_tag']}-{product}-{abi}.apk" for abi in ['universal', 'arm64-v8a', 'armeabi-v7a']}
        if {p.name for p in directory.glob('*.apk')} != expected:
            raise ValueError('Incomplete APK set for ' + product)
        for name in sorted(expected | {f'mapping-{product}.txt'}):
            shutil.copyfile(directory / name, output / name)
    for name in ['patched-source.bundle', 'ireader-patches.zip']:
        shutil.copyfile(packages / 'ireader-build-core' / name, output / name)
    (output / 'build-metadata.json').write_text(json.dumps(plan, indent=2) + '\n')
    (output / 'RELEASE_NOTES.md').write_text(f'''基于上游正式版 [{plan['upstream_tag']}]({plan['upstream_url']})，应用掌阅水波纹补丁第 {plan['patch_revision']} 次修订。

- 正文翻页动画增加“掌阅水波纹”，仅兼容掌阅 SmartOS 4+ 显示；支持旋转及独立三档速度，默认不启用。
- 独立包名 `{plan['application_id']}`，名称“阅读”，可与原版及阅读·D 共存；首次使用可通过应用内备份/恢复迁移。
- core 为基础包，comic 包含本地漫画引擎；同版本、同签名，应用内更新仅检查本 fork 并匹配当前产品。
- 首次安装不确定架构时选 universal。后续本 fork 版本使用同一固定签名，可覆盖升级。
- 两个产品通过单元测试、lint、架构检查和 Release/R8 构建后才发布；R8 mapping 按产品分别附带。

源码与签名指纹见 build-metadata.json，文件校验见 SHA256SUMS，补丁配方见 ireader-patches.zip。设备实际刷新表现仍取决于掌阅固件。
''')
    with (output / 'SHA256SUMS').open('w') as sums:
        for path in sorted(output.iterdir()):
            if path.name not in ['SHA256SUMS', 'patched-source.bundle']:
                sums.write(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n')
    print('Verified both products:', plan['release_tag'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('packages', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    merge(args.packages.resolve(), args.output.resolve())
