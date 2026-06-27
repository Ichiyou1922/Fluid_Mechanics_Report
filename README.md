# Fluid_Mechanics_Report

ドローン用プロペラの**揚力（回転軸 +Z 方向の推力 \(F_z\)）のみ**を最大化する設計課題．
効率・トルク・騒音・強度・製造性・形状の自然さは，揚力と競合する場合は**一切無視してよい**．
3 つの形状（Case A / B / C）を設計し，同一条件の CFD で揚力を比較する．

## リポジトリの目的
1. ドローン用プロペラの揚力を最大化すること（**揚力のみ**を最大化し，それ以外の一切の
   パラメータは無視する）．
2. Python API による 3D ソリッドの生成と STEP ファイルの出力（A/B は FreeCAD，
   C は Autodesk Inventor）．
3. CFD によるメッシュ・境界条件等の設定と推力計算（OpenFOAM で予備検証し，**最終評価は
   Autodesk CFD**）．

## 制約条件
1. プロペラは**直径 10 cm，高さ 6 cm の円筒内**に収まること．
2. 回転数は **100 rpm** とする．
3. プロペラは **2 ケース以上**作成して比較する．
4. うち 1 つは既存の参考文献・技術を考慮しない，**CLAUDE が最適と思う完全独自形状**とする
   （形状の不自然さや揚力以外の数値は考慮しない．人間に理解不能な形状でも構わない）．

## 報告要件（[reports/](reports/) 以下にマークダウンで）
各プロペラについて，以下を順に明記する．
1. 設計のコンセプト（何に着目して比較するのか）．
2. 計算条件（Re などの相似則パラメータ，境界条件，メッシュなど）．
3. 考察（揚力などの結果，流れ場の可視化，参考文献との比較）．
4. まとめ．
5. 参考文献．

> 注：OpenFOAM の設定は **Autodesk CFD へ流用可能**なものとし，移行手順を
> [reports/10_autodesk_cfd.md](reports/10_autodesk_cfd.md)，3 ケース統一の CFD 設定を
> [scripts/cfd_setup.md](scripts/cfd_setup.md) に記す．

---

## ワークフロー

```
A / B :  FreeCAD (Python API, Linux)  ─STEP─▶  OpenFOAM 12 (MRF, 予備検証)  ┐
                                                                            ├─▶  Autodesk CFD 2027
C     :  Autodesk Inventor (COM API, Windows)  ─STEP─▶  （予備検証は省略）  ┘     （A/B/C 同一設定で最終評価）
```

- **形状生成（A/B）**：[scripts/propeller_gen.py](scripts/propeller_gen.py)（FreeCAD ヘッドレス）で
  NACA4 断面を半径方向にロフトし，円形パターン＋ハブと融合して STEP/STL を出力．
- **形状生成（C）**：[scripts/caseC_inventor.py](scripts/caseC_inventor.py)（**Autodesk Inventor 2025
  COM API**，Windows）で，**本テンプレートを一切用いず**一から設計・生成する．当初想定の Fusion は
  当該環境に未導入のため Inventor を採用した．
- **CFD（予備）**：OpenFOAM 12 の MRF（凍結ロータ）で A/B の定常推力を評価（[reports/00_method.md](reports/00_method.md)）．
- **CFD（最終）**：**Autodesk CFD 2027** で **A/B/C を完全に同一設定**で評価する
  （[scripts/cfd_setup.md](scripts/cfd_setup.md)）．座標系は全工程で **Z 軸 = 回転軸 = 推力方向**．

## ケース一覧

| ケース | 設計コンセプト | 生成方法 | 掃引径 / 高さ |
|---|---|---|---|
| **Case A** | 慣例的な 3 枚翼・準等ピッチ（基準形状） | FreeCAD テンプレート（[caseA.json](scripts/caseA.json)） | 96.0 / 20 mm |
| **Case B** | CLAUDE 独自：8 枚・翼端拡大（逆テーパー）の高ソリディティ・ロータ．動圧 ∝(ωr)² が翼端で最大という着眼で \(r^2 c\) を最大化 | FreeCAD テンプレート（[caseB.json](scripts/caseB.json)） | 90.8 / 16 mm |
| **Case C** | **テンプレート不使用の完全独自形状**：「r² 重み体積カスケード塔」．第一原理（推力/面積 ∝ r²，かつ r² 重みに軸方向 z が現れない＝高さはタダ）から，強キャンバ逆テーパー翼を **14 枚 × 7 段**積層し，高さ 60 mm をフル活用．掃引円板の約 5 倍の揚力面を内包 | **Autodesk Inventor COM API**（[caseC_inventor.py](scripts/caseC_inventor.py)） | 98.96 / 58 mm |

詳細レポート：[caseA.md](reports/caseA.md) / [caseB.md](reports/caseB.md) / [caseC.md](reports/caseC.md)，
共通手法 [00_method.md](reports/00_method.md)，総括 [summary.md](reports/summary.md)，
Autodesk 移行 [10_autodesk_cfd.md](reports/10_autodesk_cfd.md)．

## 現在の状態

| 項目 | 状態 |
|---|---|
| Case A / B 形状・OpenFOAM 予備推力 | ✅ 完了（A: 1.94 µN，B: 2.92 µN，level3 同一条件） |
| Case C 形状（独自設計，Inventor） | ✅ 完了（D=98.96 mm，H=58 mm，1 つの連結ソリッド） |
| 各ケースのレポート | ✅ 完了 |
| Autodesk CFD の統一設定・ドメイン生成・自動化雛形 | ✅ 準備完了 |
| **Autodesk CFD による A/B/C の最終推力評価** | ⏳ **未実施**（ユーザ操作が必要．[下記手順](#autodesk-cfd-の実行手順ユーザ作業)参照） |

> Case C の絶対推力は CFD 実行後に確定する．設計メトリクス上は A/B（単段）を上回る \(F_z\) を
> 見込む（[caseC.md](reports/caseC.md)）．

## ディレクトリ構成

```
scripts/
  propeller_gen.py       FreeCAD パラメトリック生成器（A/B，STEP/STL）
  caseA.json / caseB.json  A/B の設計パラメータ
  gen_case.py            OpenFOAM MRF ケース一式を生成
  thrust.py              forces.dat から推力 F_z・トルク M_z を抽出
  run_freecad.sh         snap 版 FreeCAD をヘッドレス実行するラッパ
  render.py              （Linux）STL から形状スクリーンショット
  caseC_inventor.py      ★ Case C 生成器（Autodesk Inventor COM API，Windows）
  render_inventor.py     ★ STEP を Inventor で開き A/B/C のスクショを統一描画
  cfd_domain_inventor.py ★ CFD 用ドメイン（プロペラ＋回転円筒＋外箱）STEP を生成
  cfd_run.py             ★ Autodesk CFD 自動化雛形（Script Editor で実行）
  cfd_setup.md           ★ A/B/C 統一 CFD 設定・実 API マップ・手順
geometry/<case>/   生成された STEP / 形状情報(_info.json)（*.ipt と *_cfd.step は .gitignore）
cases/<case>/      OpenFOAM ケース（A/B の予備検証）
assets/            形状スクリーンショット（*_iso/_top/_side.png，A/B/C とも Inventor 描画）
reports/           マークダウンレポート
```
（★＝本フェーズで追加．Windows/Inventor + Autodesk CFD 用．）

## 再現手順

### A/B（Linux：FreeCAD + OpenFOAM）
```bash
scripts/run_freecad.sh scripts/propeller_gen.py scripts/caseA.json
python3 scripts/gen_case.py caseA --rpm 100 --nprocs 8 --level 4
cd cases/caseA && ./Allrun && cd -
python3 scripts/thrust.py cases/caseA
```

### C とスクショ・CFD ドメイン（Windows：Inventor）
```powershell
pip install pywin32
python scripts/caseC_inventor.py            # geometry/caseC/caseC.step + スクショ
python scripts/render_inventor.py caseA caseB   # A/B のスクショを Inventor で再描画
python scripts/cfd_domain_inventor.py       # geometry/<case>/<case>_cfd.step を生成
```

### Autodesk CFD の実行手順（ユーザ作業）

実ソルブは Autodesk CFD 2027（GUI）で行う．**クリック単位の詳細手順は
[reports/11_autodesk_cfd_gui.md](reports/11_autodesk_cfd_gui.md)**，設定の根拠は
[scripts/cfd_setup.md](scripts/cfd_setup.md)．要約：

本問題は **回転翼の非定常解析（Transient）**である（授業資料 `Exercise05.pdf` 準拠）．

1. **取り込み**：`geometry\<case>\<case>_cfd.step` を新規スタディに取り込む（入れ子3ボリューム：
   最内＝プロペラ，中間＝回転円筒，最外＝外箱）．
2. **材料**：プロペラ＝固体，円筒＝**空気**，外箱＝**空気**．
3. **境界条件**：外箱の外側6面に **圧力 0 Pa（ゲージ圧）**．壁は自動 no-slip．
4. **モーション**：**プロペラ本体（最内ソリッド）をボリューム選択**し **回転運動，軸 +Z（0,0,1），
   中心 (0,0,0)，一定角速度 10.472 rad/s**（＝100 rpm．授業資料の 628 rad/s は 100 rps 用）．
   回転は**流体ではなくプロペラに与える**（CFD が周囲流体を非定常で回す）．円筒流体は静止のまま細分化用．
5. **メッシュ**：自動→ボックス細分化 1 cm・**シリンダー細分化 0.25 cm（Y 角度 90°）**．
   薄翼は **☑サーフェス細分割**＋「サイズ調整」スライダーで **予想要素数 ≈ 数百万（1〜5M）**に追い込む
   （cm 入力不要．例：サイズ調整 0.4＋サーフェス細分割で約 92 万）．粗すぎは翼が解けず NG，
   数千万は RAM 不足で NG．**3ケース同一**設定．
6. **実行（非定常）**：解析モード＝**非定常解析**，**時間刻み 0.006 s・実行ステップ 400・内部反復 1・
   保存 0.03 s**．**終了時刻＝−1，次から継続＝t0，インテリジェント解析制御＝無効**（この 4 つが
   揃わないと step 0 で即「正常終了」する）．ソリューションコントロールで**非圧縮性**，乱流モデルは
   **SST k-ω**（低 Re・薄翼の剥離向け．既定の k-ε は不可）．
7. **結果（CSV）**：壁面計算機は使えない．`…\設計1\シナリオ1\シナリオ1_*****.csv` の
   **Hydraulic ForceZ（dyne）**を最終1回転で平均 →×10⁻⁵ で **推力 \(|F_z|\)** ［N］．
   TorqueZ（dyne-cm）×10⁻⁷ で **トルク \(M_z\)** ［N·m］．
8. **繰り返し**：B/C も同じ設定（変えるのは形状のみ）．低 Re なので**層流でも再計算**して優劣順を確認．

> 回転軸は Z なので**回転中心・トルク軸点は 3 ケースとも (0,0,0)** で良い．得られた \(|F_z|\) は
> [reports/summary.md](reports/summary.md) に記入する．自動化は形状取り込みまで API で確認済み
> （[scripts/cfd_run.py](scripts/cfd_run.py)）だが，材料以降は enum 非公開のため GUI 推奨．

## 必要環境

- **A/B 生成**：FreeCAD 1.x（snap 版 `freecad.cmd`），OpenFOAM 12（Foundation 版），Python3 + numpy/matplotlib．
- **C 生成・CFD 準備**：Windows + **Autodesk Inventor 2025**，Python 3 + **pywin32**．
- **最終 CFD**：**Autodesk CFD 2027**．
  - ★ **ソルバは CPU 専用**（GPU 高速化は非対応）．速度は CPU コア数（2ⁿ 並列）と RAM
    （約 2 GB/100 万要素）で決まる．GPU（VRAM）は描画のみ．
