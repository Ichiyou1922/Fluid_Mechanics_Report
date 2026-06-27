# Autodesk CFD 2027 — Case A / B / C 統一セットアップ手順

本書は **Case A・B・C を完全に同一条件**で Autodesk CFD 2027 にかけ、推力 \(F_z\) を
公平比較するための準備・設定書である。設計対応表は [reports/10_autodesk_cfd.md](../reports/10_autodesk_cfd.md)、
共通の物理条件は [reports/00_method.md](../reports/00_method.md)、各形状は
[reports/caseA.md](../reports/caseA.md) / [caseB.md](../reports/caseB.md) / [caseC.md](../reports/caseC.md)
を参照。

> **比較の鉄則**：3 ケースで変えてよいのは「読み込む形状 STEP」だけ。材料・回転数・境界条件・
> メッシュ方針・ソルバ・乱流モデル・収束判定はすべて同一にする。

---

## 0. ハードウェア方針（GPU について）

- **Autodesk CFD のソルバは CPU 専用。GPU 高速化は非対応**（公式：CPU のみ、GPU は使わない）。
  本 PC の GPU（NVIDIA RTX 4050 Laptop, VRAM 6 GB）は**描画・ポスト処理にのみ**寄与し、
  解析時間短縮には使えない。⇒ VRAM 6 GB は解法上の制約にならない。
- 速度を決めるのは **CPU コア数（ソルバは 2ⁿ コアを利用：2/4/8/16…）と RAM**。
  目安 **約 2 GB RAM / 100 万要素**。Solve 設定でコア数を 2ⁿ の最大に設定する。
- 参考：Autodesk, *Hardware Recommendation for Autodesk CFD*（CPU-only solver, 2ⁿ cores,
  ~2 GB/1M elements）。

## 1. 入力形状（mm, Z=回転軸）

| ケース | STEP | 掃引直径 | 軸方向範囲 z [mm] | 中心 z |
|---|---|---|---|---|
| A | [geometry/caseA/caseA.step](../geometry/caseA/caseA.step) | 96.0 mm | −10 … +10 | 0 |
| B | [geometry/caseB/caseB.step](../geometry/caseB/caseB.step) | 90.8 mm | −8 … +8 | 0 |
| C | [geometry/caseC/caseC.step](../geometry/caseC/caseC.step) | 98.0 mm | 0 … +58 | +29 |

座標系は全ケース共通（Z=回転軸=推力方向）。インポート後の座標変換は不要。

## 2. 計算領域（プロペラ＋静止外箱の 2 ボリューム）

[scripts/cfd_domain_inventor.py](cfd_domain_inventor.py) が **プロペラ＋外箱の入れ子 2 ソリッド**で
`<case>_cfd.step` を出力する。**外箱寸法は全ケース共通。中心 z のみ形状中心に追従**。

| ボリューム | 形状 | 寸法（A/B/C 共通部） | 軸方向範囲（ケース別） |
|---|---|---|---|
| 静止外箱（Static fluid） | 直方体 | **X,Y = ±180 mm** | **Z = 中心 ±300 mm**：A/B `−300…+300` / C `−271…+329` |

> **回転円筒は廃止した**（旧 OpenFOAM-MRF の `rotor` セルゾーンの名残）。Autodesk CFD では
> 回転を**プロペラ固体に与え**、CFD が周囲空気を回すので回転流体ボリュームは不要（§4）。
> プロペラ近傍を細かくしたい場合は、CFD 側で**シリンダーのメッシュ細分化“領域”**（ジオメトリ実体
> ではない）を追加すればよい（§6）。

## 3. マテリアル

| 対象 | 材料 |
|---|---|
| 流体（外箱） | **Air**（ρ=1.225 kg/m³, μ=1.81×10⁻⁵ Pa·s, ν≈1.5×10⁻⁵ m²/s） |
| プロペラ・スピンドル | Solid（任意・剛体。構造は本課題では無視） |

## 4. 回転運動（Motion）— **非定常・プロペラに付与**

授業資料 `Exercise05.pdf` は回転翼を**非定常解析（Transient）**で解く。本書もこれに統一する。

- ⚠️ **回転運動は流体には適用できない。プロペラ（ソリッド）に適用する**（資料 2.2 もプロペラを
  ボリューム選択して付与）。Autodesk CFD は「ソリッドに回転運動 → 周囲流体を非定常で回す」方式。
- 対象：**プロペラ本体（内側ソリッド）**。これにより回転円筒流体は不要（§2 で廃止）。
- 回転軸 **+Z（0,0,1）**、回転中心 **(0,0,0)**、初期位置 0 deg（3 ケース共通）。
- **一定角速度＝10.472 rad/s**（＝100 rpm＝100×2π/60）。
  - ⚠️ 授業資料の `628 rad/s` は **100 rps** 用。本プロジェクトの制約は **100 rpm** なので
    **10.472 rad/s** を使う。
- 過渡（Transient）で解く。時間刻み等は §7。

## 5. 境界条件

| 面 | 設定 |
|---|---|
| 外箱の全外面 | **Pressure = 0 Pa (gauge)**（開放・ホバリング想定） |
| プロペラ・スピンドル壁 | 既定 **no-slip** 壁 |
| 回転⇔静止 界面 | CFD が自動生成（インターフェース） |

## 6. メッシュ（3 ケース同一方針）

- 自動メッシュが基本。プロペラ近傍を細かくしたい場合のみ **CFD 側でシリンダーの細分化“領域”**
  （ジオメトリ実体ではない／局所メッシュ 0.25 cm，Y 角度 90°）を任意で追加（必須でない）。
- **薄翼（厚さ ≈1 mm）の細分化は cm 入力ではなく「自動サイズ細分割」で行う**：種類「自動」のまま
  **☑ サーフェス細分割**を ON（必要なら ☑ ギャップ細分割も）、「サイズ調整」スライダーで
  **予想要素数 ≈ 数百万（1〜5M）**に追い込む。
  - 実績：**サイズ調整 0.4 ＋ サーフェス細分割 ON ≈ 92 万要素**（妥当な初期値）。
  - **粗すぎ（≈20 万）は翼が解けず NG**。**細かすぎ（数千万）は RAM 不足/数日で NG**
    （**RAM ≈ 2 GB/100 万要素**。例：2,975 万要素 ≈ 60 GB → 不可）。
  - per-surface の cm 指定はこの版では実用的に出ないため使わない。
- 同一のサイズ調整値・チェック内容を 3 ケースで使用。まずは完走優先（板厚 3 要素に拘らず数百万）。
  3 ケース同一なら相対比較（A/B/C の優劣）は成立する。

## 7. ソルバ設定 — **非定常（Transient）/ Incompressible**

授業資料準拠で**非定常解析**。時間刻みは 100 rpm 用に再計算（資料の 100 rps 値を 60 倍にスケール）。

| 項目 | 値（100 rpm） | 資料（100 rps） |
|---|---|---|
| 解析モード | **非定常解析** | 非定常解析 |
| 時間刻み幅 dt | **0.006 s**（1 回転 0.6 s を 100 分割） | 0.00005 s |
| 終了時刻（Stop Time） | **−1**（時間で止めない） | 0.04 s |
| 実行する時間ステップ数 | **400**（＝0.006×400＝2.4 s＝4 回転） | 800 |
| 次から継続（Continue from） | **t0（最初）** | — |
| 内部反復係数 | **5**（資料は 1 だが発散したため増やす） | 1 |
| 保存間隔（結果） | **0.03 s**（20/回転）、「次に基づく」＝秒 | 0.0005 s |

> ⚠️ **step 0 で即「正常終了」する既知不具合の対策**：**終了時刻＝−1**・**実行ステップ数＝400**・
> **次から継続＝t0**・**インテリジェント解析制御＝無効**の 4 点を必ず揃える。前回結果からのリスタートだと
> 残りステップ 0 で止まるため、t0 から解き直す。詳細は [reports/11_autodesk_cfd_gui.md](../reports/11_autodesk_cfd_gui.md) §6。

- ソリューションコントロール：**インテリジェント解析制御は無効**、流れは**非圧縮性**。
- **乱流モデルは安定性優先で「まず層流（Laminar）」**。Re≈500 は物理的にほぼ層流で、最も安定かつ妥当。
  - **SST k-ω** は低 Re・剥離に強い長所があるが**ソース項が硬く発散しやすい**（実測：SST＋内部反復1 で
    step 66 発散）。**層流で完走を確認してから SST 版を追加**で回し、優劣順の頑健性を見る（A/B/C すべて）。
  - **k-ε** は壁関数前提で薄翼の低 Re・剥離に弱く不適（既定でも使わない）。
- **発散対策（効く順）**：①内部反復 1→5（必要なら 10）②層流にする ③dt 0.006→0.003（800 ステップ）
  ④最終手段で圧縮性。発散ケースの**そのまま再開は再発散**しやすいので t0 から解き直す（資料 3.3 注記）。
- Solve のコア数を **2ⁿ の最大**に（GPU 設定は無い）。
- ⚠️ 実行ダイアログで**実行ステップ数が 400** であることを必ず確認。1〜0 だと一瞬で「完了」表示が出て計算されない。

## 8. 結果抽出 — **CSV（壁面計算機は使えない）**

授業資料 3.4 に「壁面計算はできないようだ」と明記。力学情報は時系列 CSV に保存される：

```
…\<アセンブリ名>\設計 1\シナリオ 1\シナリオ 1_******.csv
```

列：実行時間，…，回転軸まわり流体トルク，**流体力（X, Y, Z）**，流体トルク（X, Y, Z）。

- **推力**：**Hydraulic ForceZ（dyne）** を**最終 1 回転分（1.8〜2.4 s）で平均** →**×10⁻⁵** で \(|F_z|\)［N］。
- **トルク**：**Hydraulic TorqueZ（dyne-cm）** を同区間で平均 →**×10⁻⁷** で \(M_z\)［N·m］。
- 推力係数 \(C_T = |F_z|/(\rho n^2 D^4)\)、\(\rho=1.225, n=1.667\,\mathrm{rev/s}, D=\) 掃引直径。
- 3 ケースの \(|F_z|\) を [reports/summary.md](../reports/summary.md) の表に記入し相対比較。
  **乱流と層流の両方**で A→B→C の優劣順が一致するかを確認する。

## 9. 自動化 — CFD Python API（[scripts/cfd_run.py](cfd_run.py)）

Autodesk CFD には SWIG 製 Python API が同梱：`C:\Program Files\Autodesk\CFD 2027\Python\CFD\`
（`Setup.py`, `Results.py` ＋ `_*.pyd`）。

> **実行環境の制約（重要・実測で確認）**：この `.pyd` は CFD の **Python 3.13** 向けビルド。
> - 外部の **Python 3.13**（`C:\Python313`）に `os.add_dll_directory(<CFD root>)` ＋
>   `sys.path` に `<CFD>\Python` を追加すれば，**`import CFD.Setup` / `CFD.Results` は成功する**
>   （クラス `DesignStudy`, `WallResults` 等にアクセス可）。Python 3.8 では ABI 非互換で不可。
> - **ただし `Setup.DesignStudy.Create()` を外部プロセスで呼ぶと 0xC0000005（アクセス違反）で
>   即クラッシュ**する。API は `DSE`（Design Study Environment＝アプリのメインウィンドウ）に
>   依存し，**CFD 本体が初期化したアプリ文脈が必須**（ヘッドレス用の Initialize/connect は無い）。
> - ⇒ **完全ヘッドレス自動化は不可**。`cfd_run.py` は **Autodesk CFD 本体を起動した状態で，
>   その内蔵 Script Editor（CFDScriptEditor）から実行**する（その文脈なら import 済みで駆動可）。
>   外部から駆動する COM 等の口は無い。ソルバは CPU 専用（§0）。

### 実 API マップ（`Setup.py` / `Results.py` から抽出。憶測ではなく実メソッド名）

| 工程 | 呼び出し |
|---|---|
| スタディ生成＋STEP取込 | `ds = Setup.DesignStudy.Create(); ds.createFrom("caseX_cfd.step")` |
| シナリオ取得 | `scn = ds.getActiveScenario()` |
| パーツ列挙（体積で prop/cyl/box 同定） | `scn.parts(pl)`, `part.volume()`, `part.boundingBox()` |
| 材料（空気） | `air = scn.getMaterial("Air"); part.applyMaterial(air)` |
| 回転領域 | `scn.applyMotion(m)`（`Motion`: `setAxisOfRotation(0,0,1)`, `setCenterOfRotation(...)`） |
| 境界条件 | `scn.applyBoundaryCondition(bc, entities, ent_type)` |
| メッシュ | `scn.automaticSize(); scn.mesh()`（局所細分化は `Mesh.meshEnahancement()`） |
| ソルブ設定 | `scn.turbulence = <enum>; scn.iterations = N` |
| 実行・待機 | `scn.run(); scn.wait()` |
| 結果（推力・トルク） | `wr = Results.WallResults(res); wr.select(prop); wr.setTorqueAxisDirection(0,0,1); wr.setTorqueAxisPoint(0,0,zc); wr.calculate(); wr.force(); wr.torque()` |

### 実測で確認できたこと（Script Editor 内）

- **ジオメトリ取込は `createFrom()` ではなく `ds.createStudyFromAsmTranslator(step, studyName)`**。
  `createFrom()` は `ValueError: sequence.index` で失敗する（拡張子非依存）。ASM トランスレータ
  経由なら成功し，`<case>_cfd.step` の入れ子ソリッドがパーツとして入る（現行は **2 パーツ**：
  内側=プロペラ，外側=外箱。旧版は円筒入り 3 パーツだった）。`part.volume()` は 0 を返すので，
  パーツ識別は `part.boundingBox()` の大小で行う（小=prop，大=box）。
- `scn.turbulence='On'`（既定），別途 `scn.turbModel` で乱流モデルを選ぶ。`scn.iterations=100`（既定）。
- **`getMaterial('Air')` は None**。材料は `scn.materialOfType(...)` / `Material.Create(...)` で生成する。

### 自動化の限界（重要）

`turbModel` / 材料タイプ / `BoundaryCondition.pressureType` などの **enum 値は SWIG ラッパに
定数として公開されておらず C++ 側にのみ存在**する（公開は `Units.CFDU_PRESSURE` 等ごく一部）。
従って完全自動化には**未公開の整数 enum を総当たりで特定**する必要があり，現実的でない。
**材料・回転・BC・乱流モデルの設定は GUI（ドロップダウン）で行うのが確実**（§1–§8）。
[scripts/cfd_run.py](cfd_run.py) は API 構造の参考雛形として残す（`createStudyFromAsmTranslator`
で取込までは確認済み）。`Results.WallResults`（`force()`/`torque()`）での結果抽出は API でも可。

## 10. 再現手順（概要）

```text
1) 形状生成（既出）
   - A/B: scripts/run_freecad.sh + scripts/gen_case.py（Linux 側）→ geometry/caseX.step
   - C  : python scripts/caseC_inventor.py（Windows/Inventor）→ geometry/caseC/caseC.step
2) Autodesk CFD 2027 起動 → New（各ケース）
3) <case>_cfd.step をインポート（プロペラ＋外箱の2ボリューム。回転円筒は無し）
4) §3 材料 Air → §5 BC（外周 0 Pa）→ §4 回転運動 10.472 rad/s（=100rpm）+Z をプロペラに付与
5) §6 メッシュ（自動＋サーフェス細分割で数百万）→ §7 Solve（非定常 dt0.006/400step/内部反復5, まず層流, 2ⁿ コア）
6) §8 CSV の Hydraulic ForceZ(dyne) を最終1回転で平均 →×10⁻⁵ で |Fz| → summary.md に記入
7) SST k-ω でも再計算（§7）して優劣順の頑健性を確認
```
