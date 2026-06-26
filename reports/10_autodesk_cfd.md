# Autodesk CFD への移行ガイド

本プロジェクトの検証は OpenFOAM 12（MRF 凍結ロータ）で行うが、**最終的な解析は
Autodesk CFD** で実施する。両者は「回転領域を持つ非圧縮定常 RANS」という同じ枠組みで
あり、設定は 1:1 で対応づけられる。本ガイドは OpenFOAM 設定を Autodesk CFD に
読み替えるための対応表と手順を示す。

---

## 0. 設定の対応（早見表）

| 項目 | OpenFOAM 12（本リポジトリ） | Autodesk CFD |
|---|---|---|
| 形状入力 | `geometry/<case>/<case>.step`（mm） | 同一 STEP をインポート |
| 流体 | `physicalProperties`: ρ=1.225, ν=1.5e-5 | Material = **Air**（既定値で一致） |
| 回転 | `MRFProperties`: cellZone `rotor`, axis (0 0 1), ω=100 rpm | **Rotating Region**, 軸 +Z, 100 rpm |
| 回転領域形状 | `searchableCylinder`/`cylinderToCell`（R56 mm, ±35 mm） | 同寸の円筒ボリュームを作成し Rotating 指定 |
| 解析種別 | 定常 `simpleFoam`/`incompressibleFluid` | **Steady State**, Incompressible |
| 乱流 | k–ωSST | **SST k-ω**（または低 Re 流れにつき層流も検討） |
| 外周境界 | `totalPressure` p0=0 / `pressureInletOutletVelocity` | 外箱表面に **Pressure = 0 (gauge)** |
| 結果（推力） | `forces` function object の \(F_z\) | **Wall Calculator** → 壁面力の Z 成分 |
| トルク | `forces` の \(M_z\) | Wall Calculator → モーメント Z |

> 座標系は全工程で **Z 軸 = 回転軸 = 推力方向** に統一している。STEP もこの向きで
> 出力されるため、インポート後に座標変換は不要。

## 1. ジオメトリの準備

1. `geometry/caseX/caseX.step` をそのまま Autodesk CFD（または上流の Fusion/Inventor）に
   インポートする。単位は **mm**。
2. プロペラを内包する **円筒ボリューム（回転領域）** を作成する。
   - 寸法：半径 56 mm、軸方向 −35〜+35 mm（OpenFOAM の `rotor` ゾーンと同一）。
   - この円筒とプロペラの差を「回転流体領域」、外側を「静止流体領域」とする
     （Autodesk CFD は外箱を自動で空気充填、または明示的に外箱を作成）。
3. 外部流体領域（静止）：±180 mm × ±300 mm 程度の直方体（OpenFOAM 領域と同等）。

## 2. マテリアル

- プロペラ：Solid（任意。剛体・断熱でよい。構造は本課題では無視）。
- 流体：**Air**（ρ=1.225 kg/m³, μ=1.81×10⁻⁵ Pa·s → ν≈1.5×10⁻⁵ m²/s）。

## 3. 回転領域（Rotating Region）

- 上記円筒ボリュームに **Rotating Region** を割り当てる。
- 回転速度 **100 rpm**、回転軸 **+Z**（軸線はモデル原点を通る）。
- Autodesk CFD の Rotating Region は内部的に MRF（定常）／スライディング（過渡）を
  選択できる。本検証と整合させるため **定常＝MRF 相当** を用いる。

## 4. 境界条件

| 面 | 設定 |
|---|---|
| 外箱の全外面 | Pressure = 0 Pa (gauge)（開放、ホバリング想定） |
| プロペラ壁・ハブ | 既定の no-slip 壁（指定不要） |
| 回転領域と静止領域の界面 | Autodesk CFD が自動でインターフェース生成 |

## 5. メッシュ

- 自動メッシュ + **翼面の局所細分化（Mesh Enhancement / Refinement Region）**。
- 薄翼（厚さ 0.9–1.6 mm）を **板厚方向に最低 3 要素** 入るよう細分化する
  （OpenFOAM の level 4 ≈ 0.47 mm 相当）。
- 回転領域円筒にも体積細分化を適用。

## 6. 解析設定

- **Steady State**、Incompressible、Turbulence = **SST k-ω**
  （Re≈500 と低いため、剥離が支配的でなければ **Laminar** での再計算も比較推奨）。
- 収束は壁面力 \(F_z\) のモニタが定常化するまで。

## 7. 結果抽出（推力・トルク）

- **Wall Calculator** をプロペラ壁面に適用し、力ベクトルの **Z 成分 = 推力**、
  モーメントの **Z 成分 = トルク** を読む。
- OpenFOAM の `forces` 出力（`postProcessing/forces/.../forces.dat`）と突き合わせて
  検証する。MRF 同士であれば同オーダー（数 µN）で一致するはずである。

## 8. 既知の差異・注意

- Autodesk CFD と OpenFOAM では壁関数・低 Re 補正・界面処理が異なるため、推力の
  絶対値は数十 % ずれ得る。**2 形状間の優劣（相対比較）** は両ソルバで一致することを
  確認するのが本検証の主眼。
- 低 Re（≈500）では乱流モデル依存が出やすい。**層流 vs SST k-ω** の感度を必ず確認する。
- 単位系（mm vs m）に注意。OpenFOAM では STL を 0.001 倍して m に変換している
  （`Allrun` 内 `surfaceTransformPoints "scale=(0.001 0.001 0.001)"`）。Autodesk CFD は
  mm のまま扱えるが、力の単位（N）と長さの整合を最終確認すること。
