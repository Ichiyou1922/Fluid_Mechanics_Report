# 解析手法 — 共通設定（Case A / Case B 共通）

本ファイルは 2 ケースに共通する計算手法・条件をまとめる。各ケース固有の設計
コンセプトと結果は [caseA.md](caseA.md) / [caseB.md](caseB.md) を参照。

---

## 1. 問題設定

ドローン用プロペラの **揚力（推力, 回転軸方向の力）を最大化** することが唯一の
目的である。直径 100 mm × 高さ 60 mm の円筒内に収まり、回転数 100 rpm で運転する
という制約のもとで 2 形状を比較する。

| 項目 | 値 |
|---|---|
| 回転数 \(n\) | 100 rpm = 1.667 rev/s = 10.47 rad/s |
| 回転軸 | \(+Z\) 軸まわり |
| 包絡円筒 | 直径 100 mm, 高さ 60 mm |
| 作動流体 | 空気（20 ℃） |
| 密度 \(\rho\) | 1.225 kg/m³ |
| 動粘度 \(\nu\) | 1.5×10⁻⁵ m²/s |

座標系は **Z 軸 = 回転軸 = 推力方向**、X–Y がロータ面である。FreeCAD・OpenFOAM・
（最終的な）Autodesk CFD で同一の座標定義を用いる。

## 2. 相似則パラメータ

低速回転のため流れは非圧縮・低レイノルズ数である。代表値を以下に示す。

- **翼端速度** \(U_{tip} = \omega R = 10.47 \times 0.05 = 0.52\ \mathrm{m/s}\)（Mach ≈ 0.0015、完全非圧縮）
- **翼弦レイノルズ数**（翼端、代表翼弦 \(c\approx0.015\ \mathrm{m}\)）
  \[
  Re_c = \frac{U_{tip}\,c}{\nu} = \frac{0.52 \times 0.015}{1.5\times10^{-5}} \approx 5.2\times10^{2}
  \]
  → **Re ≈ 500 オーダー**。翼型まわりは層流〜遷移域であり、粘性の影響が大きい。
- **推力係数の見積り** \(C_T = T/(\rho n^2 D^4)\)。\(\rho n^2 D^4 = 1.225\times1.667^2\times0.096^4 \approx 2.9\times10^{-4}\) N。
  一般的な \(C_T = 0.05\text{–}0.15\) を当てはめると **T ≈ 1.5×10⁻⁵ – 4×10⁻⁵ N** が物理的な目安となる。

> 注: 100 rpm という低回転では絶対推力は数十 µN オーダーと極めて小さい。本課題は
> 「揚力のみを最大化」する相対比較が目的であり、絶対値の大小ではなく **2 形状間の差**
> に意味がある。

## 3. 計算手法：MRF（Multiple Reference Frame, 凍結ロータ）

回転翼まわりの定常解析として **MRF（凍結ロータ）法** を採用する。プロペラを内包する
円筒状セルゾーン `rotor`（半径 56 mm, 軸方向 ±35 mm）に回転の体積力（コリオリ＋遠心）を
与え、翼面は no-slip 壁として相対静止させる。メッシュは静止したまま定常場を解く。

- **選定理由**：(1) 定常で安定・低コスト、(2) **Autodesk CFD の「回転領域(Rotating Region)」
  と概念が 1:1 で対応** するため設定を流用しやすい（→ [10_autodesk_cfd.md](10_autodesk_cfd.md)）。
- スライディングメッシュ（非定常 AMI）に比べ翼の相対位置依存（時間平均）は捨象するが、
  単一ロータの定常推力評価には十分。

### ソルバ
- OpenFOAM 12、`foamRun` の `incompressibleFluid` ソルバ（定常 SIMPLE）。
- 乱流モデル：**k–ωSST RANS**（壁関数）。Re が低いため乱流生成は小さく、実質層流に
  近い挙動になるが、剥離を含む場の安定化のため RANS を用いる。

### 境界条件
| 場 | farField（外周） | propeller（翼・ハブ壁） |
|---|---|---|
| U | `pressureInletOutletVelocity` (0,0,0) | `noSlip` |
| p | `totalPressure` p0=0 | `zeroGradient` |
| k | `inletOutlet` | `kqRWallFunction` |
| ω | `inletOutlet` | `omegaWallFunction` |
| νt | `calculated` | `nutkWallFunction` |

静止空気中のホバリングを模擬するため、外周は全圧 0 の開放境界とし、ロータが誘起する
流入・流出を許容する。計算領域は ±180 mm（X,Y）× ±300 mm（Z）の直方体。

## 4. メッシュ

- 背景メッシュ `blockMesh`（一様六面体, ~7.5 mm）→ `snappyHexMesh` で翼表面に
  段階的細分化（surface refinement **level 4**, 最小セル ≈ 0.47 mm）。
- ロータ領域に体積細分化を追加。`topoSet`（`cylinderToCell`）で MRF 用 `rotor`
  セルゾーンを作成。
- 薄い翼（厚さ 0.9–1.6 mm）を解像するため **level 3（粗）と level 4（細）でメッシュ依存性**
  を確認した（各ケースの結果節を参照）。

## 5. 推力・トルクの評価

`forces` function object で翼・ハブ壁面（パッチ `propeller`）に働く圧力＋粘性力を積分する。

- **推力（揚力）** \(T = |F_z|\)（回転軸方向成分）
- **トルク** \(Q = M_z\)
- 収束は SIMPLE 残差（p, U, k, ω < 1×10⁻⁴）と \(F_z\) の定常化で判定。

## 6. 再現手順

```bash
# 1) 形状生成（FreeCAD, STEP/STL 出力）
scripts/run_freecad.sh scripts/propeller_gen.py scripts/caseA.json
python3 scripts/render.py caseA          # スクリーンショット assets/

# 2) OpenFOAM ケース生成
python3 scripts/gen_case.py caseA --rpm 100 --nprocs 8 --level 4

# 3) メッシュ＋求解（cases/caseA/）
cd cases/caseA && ./Allrun

# 4) 推力抽出
python3 scripts/thrust.py cases/caseA
```
