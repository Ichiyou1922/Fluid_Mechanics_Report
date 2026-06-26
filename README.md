# Fluid_Mechanics_Report

## リポジトリの目的
1. FreeCADによるドローン用プロペラの揚力を最大化する事が第一の目的（注意: ただ揚力のみを最大化すれば良く，それ以外の一切のパラメータを無視する）
2. PythonAPIを用いてFreeCADによる3Dソリッドの作成及びSTEPファイルの出力を行う．
3. OpenFOAMによるメッシュ, controlDict, velocityなどのDictionaryを作成及びCFD計算を行う．

## 制約条件
1. プロペラは直径10cm, 高さ6cmの円筒形内部に収まるものとする
2. 回転数は100rpmとする
3. プロペラは2ケース以上作成し比較する

## 追記事項
- 本リポジトリではOpenFOAMを用いてCFD解析を行うが，最終的にはAutodesk CFDを使用して解析を行う．そのため各設定をAutodesk CFDへ流用可能なものとすること．また設定の仕方をreports/以下にマークダウンで明記すること．
- 各プロペラに対して以下の事項をrepots/以下にマークダウンで明記すること
    1. 設計のコンセプト（何に着目して比較するのか）
    2. 計算条件（Reなどの流体相似則パラメータ，境界条件，メッシュなども含む）
    3. 考察（揚力などの計算結果，流れ場の可視化，参考文献との比較など）
    4. まとめ
    5. 参考文献
- プロペラのケースのうち一つは既存の参考文献や技術等を考慮しないCLAUDEが最適だと思うものにすること．すなわち形状の不自然さや揚力以外の数値を考慮しない，完全に独自のもので良い．人間に理解不能な形状でも構わない．

---

## ワークフロー

```
FreeCAD (Python API)         OpenFOAM 12 (MRF, 予備検証)        Autodesk CFD (最終)
  パラメトリック生成   ─STEP/STL─▶  メッシュ + 定常RANS  ──設定流用──▶  回転領域 + 定常RANS
  揚力最大化形状を設計          推力 F_z を抽出（予備比較）           最終的な推力評価
```

- **形状生成**：`scripts/propeller_gen.py`（FreeCAD ヘッドレス）で翼型断面（NACA4）を
  半径方向にロフトしてブレードを作り，円形パターン＋ハブと融合して STEP/STL を出力。
- **CFD（予備）**：OpenFOAM 12 の MRF（凍結ロータ）で定常推力を評価。設定は Autodesk CFD
  の回転領域へ 1:1 で流用可能（[reports/10_autodesk_cfd.md](reports/10_autodesk_cfd.md)）。
- **CFD（最終）**：Autodesk CFD。**Case C は別途 Windows 上で Autodesk Fusion API ＋
  Autodesk CFD API により，本テンプレート（パラメトリック生成器）を用いず一から設計・解析する。**

## ケース一覧

| ケース | 設計コンセプト | 生成方法 | CFD |
|---|---|---|---|
| **Case A** | 慣例的な 3 枚翼・準等ピッチ（基準形状） | FreeCAD テンプレート（[scripts/caseA.json](scripts/caseA.json)） | OpenFOAM MRF |
| **Case B** | CLAUDE 独自の揚力最大化案：8 枚・翼端拡大（逆テーパー）の高ソリディティ・ロータ。動圧 ∝(ωr)² が翼端で最大という着眼で r²·c を最大化 | FreeCAD テンプレート（[scripts/caseB.json](scripts/caseB.json)） | OpenFOAM MRF |
| **Case C** | **テンプレート不使用**。CLAUDE が一から（Autodesk Fusion/CFD API で）独自設計する揚力最大化形状 | Autodesk Fusion API（Windows） | Autodesk CFD |

各ケースの詳細レポートは [reports/](reports/) 以下：
[caseA.md](reports/caseA.md) / [caseB.md](reports/caseB.md) / 共通手法 [00_method.md](reports/00_method.md) /
Autodesk 移行 [10_autodesk_cfd.md](reports/10_autodesk_cfd.md)。

## ディレクトリ構成

```
scripts/        形状生成・ケース生成・レンダリング・後処理スクリプト
  propeller_gen.py   FreeCAD パラメトリックプロペラ生成器（STEP/STL）
  caseA.json/caseB.json  各ケースの設計パラメータ
  gen_case.py        OpenFOAM MRF ケース一式を生成
  render.py          STL から形状スクリーンショットを生成
  thrust.py          forces.dat から推力 F_z・トルク M_z を抽出
  run_freecad.sh     snap 版 FreeCAD をヘッドレス実行するラッパ
geometry/<case>/   生成された STEP / STL / 形状情報(_info.json)
cases/<case>/      OpenFOAM ケース（blockMesh+snappyHexMesh+MRF, foamRun）
assets/            形状スクリーンショット（*_iso/_top/_side.png）
reports/           マークダウンレポート
results/           推力などの集計
```

## 再現手順

```bash
# 形状生成 + スクリーンショット
scripts/run_freecad.sh scripts/propeller_gen.py scripts/caseA.json
python3 scripts/render.py caseA

# OpenFOAM ケース生成 → メッシュ＋求解 → 推力抽出
python3 scripts/gen_case.py caseA --rpm 100 --nprocs 8 --level 4
cd cases/caseA && ./Allrun && cd -
python3 scripts/thrust.py cases/caseA
```

## 必要環境

- FreeCAD 1.x（snap 版を `freecad.cmd` で利用）
- OpenFOAM 12（Foundation 版, `foamRun`/`snappyHexMesh`）
- Python 3 + numpy / matplotlib（スクリーンショット）
- （最終解析）Windows + Autodesk Fusion / Autodesk CFD