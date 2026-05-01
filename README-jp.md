# Matplotlib to Originlab

> **このファイルは正本（日本語版）です。**
> 英語版（参照）は [README.md](README.md) を参照してください。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/y-marui/python-matplotlib-to-originlab/actions/workflows/ci.yml/badge.svg)](https://github.com/y-marui/python-matplotlib-to-originlab/actions/workflows/ci.yml)
[![Charter Check](https://github.com/y-marui/python-matplotlib-to-originlab/actions/workflows/check-charter.yml/badge.svg)](https://github.com/y-marui/python-matplotlib-to-originlab/actions/workflows/check-charter.yml)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/y-marui?style=social)](https://github.com/sponsors/y-marui)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-donate-yellow.svg)](https://www.buymeacoffee.com/y.marui)

matplotlib の Figure を OriginLab グラフに変換する。OriginLab のインストール状況に応じてローカル実行とリモート実行を自動切替する。

---

## Monorepo structure

```
matplotlib-to-originlab/
├── core/      matplotlib-to-originlab-core    ローカル実行エンジン（Windows + Origin）
├── client/    matplotlib-to-originlab         ユーザー向けクライアント（全OS）
├── remote/    matplotlib-to-originlab-remote  HTTP クライアント（サーバーモード用）
└── server/    matplotlib-to-originlab-server  Origin 実行ノード
```

各サブディレクトリに独自の README と `pyproject.toml` がある。

---

## Quick start

クライアントをインストール（ほとんどのユーザーはこれだけでよい）:

```bash
pip install matplotlib-to-originlab
```

使い方:

```python
import matplotlib.pyplot as plt
import matplotlib_to_originlab as mto

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [4, 5, 6], label="sample")
ax.set_xlabel("X")
ax.set_ylabel("Y")
plt.legend()

mto.run(fig, ax)  # OriginLab があればローカル実行、なければリモート実行
```

**Windows + OriginLab インストール済みの場合:** Origin を直接操作する。
**その他の環境:** `matplotlib-to-originlab-server` にジョブを転送する（`matplotlib_to_originlab_remote.configure()` でサーバー URL を設定）。

---

## Sample (matplotlib → Origin)

```python
import matplotlib.pyplot as plt
import matplotlib_to_originlab as mto
from astropy_extension.visualization import labeled_quantity_support
import astropy.units as u
import numpy as np

fig, ax = plt.subplots()

with labeled_quantity_support("$X$", "$M$"):
    xraw = np.linspace(-1, 1, 10)
    x = 10**xraw * u.m

    y = xraw * u.kg / u.s**2
    ax.plot(x, y, label="Model1")

    y = -xraw * 1e3 * u.g / u.s**2
    ax.plot(x, y, "o", markersize=10, label="Model2")

    yerr = np.array([0.1] * len(xraw)) * u.kg / u.s**2
    ax.errorbar(x, xraw * u.kg / u.s**2, fmt="o", yerr=yerr, label="Data", mfc="w")

    plt.xscale("log")
plt.legend()

mto.run(fig, ax, folder_name="Folder", workbook_name="Book", graph_name="Graph")
```

Python での Figure

![figure in python](sample/python.png)

Origin でのグラフ

![graph in origin](sample/origin.png)

---

## Architecture

```
[User Code]
    ↓
matplotlib-to-originlab  (client)
    ↓
┌──────────────────────────────────────┐
│  origin_available() == True          │
│    → matplotlib-to-originlab-core    │  (ローカル、Windows + OriginLab)
│                                      │
│  origin_available() == False         │
│    → matplotlib-to-originlab-remote  │  (HTTP クライアント)
└──────────────────────────────────────┘
    ↓ (リモートパスのみ)
matplotlib-to-originlab-server
    ↓
OriginLab
```

---

## Packages

| パッケージ | 役割 | PyPI |
|---|---|---|
| **matplotlib-to-originlab** | ユーザー向けクライアント（ここから始める） | 予定 |
| matplotlib-to-originlab-core | ローカル実行エンジン（Windows のみ） | なし（パス参照） |
| matplotlib-to-originlab-remote | HTTP クライアント（サーバーモード用） | 予定 |
| matplotlib-to-originlab-server | Origin 実行ノード（Windows のみ） | 予定 |

---

## Roadmap

詳細は [ROADMAP.md](ROADMAP.md) を参照:

- リモートトランスポート実装
- サーバー HTTP API
- フォントサイズ・軸ラベルの改善
- `errorbar` の `xerr` サポート
- PyPI 公開

---

## Origins

[jsbangsund/python_to_originlab](https://github.com/jsbangsund/python_to_originlab)（MIT）からのフォーク。

主な変更点:
- OriginEXT から `originpro` へ移行
- `astropy.units.Quantity` サポート追加
- `matplotlib.pyplot.errorbar` の `yerr` サポート追加
- client / core / remote / server に分離したモノレポ構造に再編

---

## License

MIT — [LICENSE](LICENSE) を参照。

---
*この文書には英語版 [README.md](README.md) があります。編集時は同一コミットで更新してください。*
