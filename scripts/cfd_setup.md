# Autodesk CFD 2027 — Case A / B / C 統一セットアップ手順

本書は **Case A・B・C を完全に同一条件**で Autodesk CFD 2027 にかけ、推力 \(F_z\) を
公平比較するための準備・設定書である。設計対応表は [reports/10_autodesk_cfd.md](../reports/10_autodesk_cfd.md)、
共通の物理条件は [reports/00_method.md](../reports/00_method.md)、各形状は
[reports/caseA.md](../reports/caseA.md) / [caseB.md](../reports/caseB.md) / [caseC.md](../reports/caseC.md)
を参照。

> **比較の鉄則**：3 ケースで変えてよいのは「読み込む形状 STEP」と「回転領域円筒の軸方向範囲
> （形状高さに追従）」だけ。材料・回転数・境界条件・メッシュ方針・ソルバ・乱流モデル・収束
> 判定はすべて同一にする。

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

## 2. 計算領域（回転領域＋静止外箱）

CFD 上で 2 つの流体ボリュームを作る（CAD プリミティブで作成、または CFD の Void Fill）。
**半径・外箱寸法は全ケース共通。回転領域の軸方向のみ形状中心に追従**させる。

| ボリューム | 形状 | 寸法（A/B/C 共通部） | 軸方向範囲（ケース別） |
|---|---|---|---|
| 回転領域（Rotating） | 円筒, 軸=Z, 中心(0,0) | **半径 56 mm** | 形状中心 ±35 mm：A `−35…+35` / B `−35…+35` / C `−6…+64` |
| 静止外箱（Static） | 直方体 | **X,Y = ±180 mm** | **Z = 中心 ±300 mm**：A/B `−300…+300` / C `−271…+329` |

> 回転円筒は OpenFOAM の `rotor` セルゾーン（R56, 中心 ±35）と一致。Case C は背が高い
> （58 mm）ため、円筒軸長を形状中心 z=29 まわりに ±35 へ平行移動して全段を覆う。
> 半径 56 mm は 3 ケースとも翼端（最大 49.5 mm）を十分内包する。

## 3. マテリアル

| 対象 | 材料 |
|---|---|
| 流体（回転領域・外箱） | **Air**（ρ=1.225 kg/m³, μ=1.81×10⁻⁵ Pa·s, ν≈1.5×10⁻⁵ m²/s） |
| プロペラ・スピンドル | Solid（任意・剛体。構造は本課題では無視） |

## 4. 回転領域（Rotating Region）

- 上記円筒に **Rotating Region** を割り当て。
- **回転速度 100 rpm、軸 +Z、軸線は原点を通る**（3 ケース共通）。
- 定常＝**MRF 相当**（Steady State）を使用（過渡スライディングは使わない）。

## 5. 境界条件

| 面 | 設定 |
|---|---|
| 外箱の全外面 | **Pressure = 0 Pa (gauge)**（開放・ホバリング想定） |
| プロペラ・スピンドル壁 | 既定 **no-slip** 壁 |
| 回転⇔静止 界面 | CFD が自動生成（インターフェース） |

## 6. メッシュ（3 ケース同一方針）

- 自動メッシュ ＋ **翼面の局所細分化**。薄翼（厚さ ≈1.0–1.6 mm）に **板厚方向 最低 3 要素**
  （最小セル ≈ 0.47 mm、OpenFOAM level4 相当）。
- 回転領域円筒に体積細分化。
- 同一の細分化レベル・成長率を 3 ケースで使用。Case C は翼が 98 枚と多いため要素数が
  最大（数百万〜）になる見込み。**RAM ≈ 2 GB/100 万要素**で必要メモリを見積もる。

## 7. ソルバ設定

- **Steady State / Incompressible**。
- 乱流：**SST k-ω**。Re≈500 と低いので、**層流（Laminar）でも再計算して感度確認**（A/B/C すべて）。
- Solve のコア数を **2ⁿ の最大**に設定（GPU 設定は無い）。
- 収束：壁面力 \(F_z\) のモニタが平坦化するまで（残差も併用）。

## 8. 結果抽出

- **Wall Calculator** をプロペラ＋スピンドル壁面に適用：
  - **推力** \(=\) 力ベクトルの **Z 成分** \(|F_z|\)
  - **トルク** \(=\) モーメントの **Z 成分** \(M_z\)
- 推力係数 \(C_T = |F_z|/(\rho n^2 D^4)\)、\(\rho=1.225, n=1.667\,\mathrm{rev/s}, D=\) 掃引直径。
- 3 ケースの \(|F_z|\) を [reports/summary.md](../reports/summary.md) の表に記入し相対比較。
  **SST と層流の両方**で A→B→C の優劣順が一致するかを確認する。

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

[scripts/cfd_run.py](cfd_run.py) が A/B/C をこの API で一括処理する雛形（同一設定、回転中心のみ
ケース別）。**数か所（turbulence enum、Motion 生成、外周面 BC の面選択、Vector の添字、単位）は
Script Editor 内で `print(dir(...))` 等で実値を確認してから確定**すること（`# CONFIRM` 印）。
API で賄えない面選択等は GUI で補ってよい。`Results.WallResults` で \(F_z, M_z\) を 3 ケース
バッチ抽出すれば比較を再現可能にできる。

## 10. 再現手順（概要）

```text
1) 形状生成（既出）
   - A/B: scripts/run_freecad.sh + scripts/gen_case.py（Linux 側）→ geometry/caseX.step
   - C  : python scripts/caseC_inventor.py（Windows/Inventor）→ geometry/caseC/caseC.step
2) Autodesk CFD 2027 起動 → New（各ケース）
3) caseX.step をインポート → §2 の回転円筒＋外箱を作成（軸方向のみケース別）
4) §3 材料 Air → §4 Rotating 100rpm +Z → §5 BC（外周 0 Pa）
5) §6 メッシュ（翼面 3 要素）→ §7 Solve（Steady, SST k-ω, 2ⁿ コア）
6) §8 Wall Calculator で |Fz|, Mz 抽出 → summary.md に記入
7) 層流でも再計算（§7）して優劣順の頑健性を確認
```
