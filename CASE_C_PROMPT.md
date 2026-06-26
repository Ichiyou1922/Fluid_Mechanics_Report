# Case C ハンドオフ・プロンプト（Windows 上の Claude Code 用）

> 以下のコード塊全体を、**Windows 上で起動した Claude Code の最初のプロンプト**として
> そのまま貼り付けてください。リポジトリ（本 `Fluid_Mechanics_Report`）を Windows 側に
> clone した状態で実行することを想定しています。

---

```text
あなたは Windows 上で動く Claude Code です。流体力学レポート課題の「Case C」を担当します。
このリポジトリ（Fluid_Mechanics_Report）には既に Case A / Case B が実装済みです。
まず README.md・CLAUDE.md・reports/ 以下（特に reports/summary.md と
reports/10_autodesk_cfd.md）・scripts/caseA.json・scripts/caseB.json を読み、
座標系・単位・制約・既存の設計指針を把握してから着手してください。

═══════════════════════════════════════════════════════════════════
■ 0. ゴールと絶対制約（厳守）
═══════════════════════════════════════════════════════════════════
- 目的：ドローン用プロペラの「揚力（=回転軸方向の推力 Fz）だけ」を最大化する。
  効率・トルク・騒音・強度・製造性・形状の自然さは【一切無視してよい】。
- 制約：
  1) 直径 ≤ 100 mm かつ 軸方向高さ ≤ 60 mm の円筒内に収まること
  2) 回転数 100 rpm
  3) 既存 Case A/B と比較できること
- 座標系・単位（A/B と統一）：Z 軸 = 回転軸 = 推力方向、X–Y がロータ面。長さは mm。
- Case C は【本リポジトリのパラメトリック生成器（scripts/propeller_gen.py）を使わない】。
  Autodesk Fusion API で“一から”自由に形状を設計すること。NACA ロフトの枠に縛られない、
  自由曲面・多段・スクープ状など、人間に理解不能な形状でも構わない。

═══════════════════════════════════════════════════════════════════
■ 1. 既存成果（Case A/B）と、それを踏まえた Case C 設計方針
═══════════════════════════════════════════════════════════════════
OpenFOAM(MRF) 予備解析の結論（同一メッシュ比較）：
- Case A（慣例3枚翼）        : 推力 1.94 µN
- Case B（独自・翼端拡大8枚翼）: 推力 2.92 µN（+50%）← 揚力で勝利
判明した揚力最大化の指針：
  (a) 動圧 ∝ (ωr)² は翼端で最大 → 翼面積を【翼端に集中】（逆テーパー）
  (b) 包絡円筒内で干渉しない限り【ソリディティ（総翼面積/枚数）を最大化】
  (c) 低 Re(≈500) でも高 CL を得るため【強キャンバ】
さらに Case C で攻めるべき未活用の自由度：
  (d) A/B は軸方向を 16–20 mm しか使っていない。【高さ 60 mm をフルに使う】
      （例：軸方向に積み重ねた多段ロータ、背の高いスクープ/アルキメデス螺旋状の
      面で空気を軸方向に大量に押し出す形状）
  (e) 自由曲面（ロフト枠に縛られない湾曲・可変断面）で各翼素を失速直前の高 CL に保つ
Case C は (a)–(e) を出発点に、Fusion で自由設計して A/B を上回る揚力を狙うこと。
（最終的な優劣判定は Autodesk CFD の結果で行う。）

═══════════════════════════════════════════════════════════════════
■ 2. 環境確認（まず最初に実行）
═══════════════════════════════════════════════════════════════════
PowerShell で以下を確認し、無ければインストール手順を案内・実施すること。

# Autodesk Fusion（旧 Fusion 360）の有無
Get-ChildItem "$env:LOCALAPPDATA\Autodesk\webdeploy\production" -Recurse -Filter "Fusion*.exe" -ErrorAction SilentlyContinue | Select-Object FullName
# Autodesk CFD の有無
Get-ChildItem "C:\Program Files\Autodesk" -Directory -ErrorAction SilentlyContinue | Where-Object Name -like "CFD*"
# Python（後処理・スクリプト用）
python --version

未インストールの場合：
- Fusion：Autodesk アカウントでサインインし、Autodesk のインストーラ（Fusion クライアント）
  を取得して導入。個人用ライセンス/体験版が利用可能。インストールは対話/オンライン形式で、
  サイレント自動化は基本不可。ユーザーにサインインと導入を依頼してよい。
- Autodesk CFD：Autodesk アカウントから CFD のインストーラを取得して導入（体験版あり）。
  ライセンス認証が必要。ユーザーに依頼してよい。
- いずれも「インストール済みか」「サインイン済みか」を必ず先に確認し、未了ならユーザーに
  具体的な操作を依頼してから先へ進むこと（勝手に長時間ブロックしない）。

═══════════════════════════════════════════════════════════════════
■ 3. 使用 API と重要な注意点
═══════════════════════════════════════════════════════════════════
[A] Autodesk Fusion API（形状生成 → STEP 出力）
- 言語：Python。Fusion の「Scripts and Add-Ins（Shift+S）」から Script として実行、
  または Add-In 化。エントリは `def run(context):`。
  典型：
    import adsk.core, adsk.fusion, traceback
    app = adsk.core.Application.get()
    ui  = app.userInterface
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
- 形状作成：sketches → loftFeatures / sweepFeatures（自由曲面）、
  circularPattern（円形パターン）、combine（ブーリアン融合）。
- ★【単位の罠】Fusion API の長さ内部単位は「センチメートル(cm)」。
  100 mm を数値で渡すときは 10.0。混乱回避のため可能な限り
  `adsk.core.ValueInput.createByString('100 mm')` を使うこと。
- STEP 出力：
    em = design.exportManager
    opts = em.createSTEPExportOptions(r'<repo>\geometry\caseC\caseC.step', body)
    em.execute(opts)
- ★ Fusion API は基本的に「起動中の Fusion アプリ内」で動く（完全ヘッドレスは非対応）。
  Fusion を起動した状態でスクリプトを走らせる前提で設計すること。
- 正確な最新 API は、インストール先の API ヘルプ／Autodesk Fusion API リファレンス
  （公式 docs）で必ず確認。context7 も活用してよい。【憶測で API を呼ばない】。

[B] Autodesk CFD API / 自動化（解析）
- Autodesk CFD には自動化用の API／バッチ機能がある。ただし API の網羅範囲・呼び出し形式は
  バージョン依存のため、【まずインストール先の Help 内「Autodesk CFD API リファレンス」
  および公式 docs で実際の API を確認】してから使うこと。
- API で自動化できない工程は GUI 操作で補い、自動化可能な部分（材料・回転領域・境界条件・
  メッシュ・実行・結果抽出）を API/スクリプト化する方針でよい。
- 設定の中身は reports/10_autodesk_cfd.md に OpenFOAM との対応表付きで既述。これを“仕様”
  として CFD 側を構築すること（回転領域=MRF相当、定常、SST k-ω、外周 0 Pa、Air）。

═══════════════════════════════════════════════════════════════════
■ 4. 実験方法（手順）
═══════════════════════════════════════════════════════════════════
1) 設計：Fusion API で Case C 形状を生成（§1 の指針、§0 の制約）。
   - 生成後に bounding box を取得し、直径 ≤ 100 mm・高さ ≤ 60 mm を【プログラムで検証】。
   - geometry/caseC/caseC.step を出力。スクリーンショットを assets/caseC_*.png に保存
     （Fusion のビューを保存、または STEP/STL を Python で render）。
2) 解析前処理（Autodesk CFD、reports/10_autodesk_cfd.md 準拠）：
   - STEP を取り込み、プロペラを内包する円筒（半径 56 mm, 軸 ±35 mm 目安。形状が高い場合は
     高さに合わせ拡大）を「回転領域(Rotating Region)」に設定。回転 100 rpm, 軸 +Z。
   - 外部静止流体ボックス（±180 mm × ±300 mm 目安）。Material = Air。
   - 境界：外箱外面 = Pressure 0 Pa (gauge)。プロペラ壁 = no-slip。
   - 解析種別 = Steady State / Incompressible。乱流 = SST k-ω。
     ★ Re≈500 と低いので【Laminar でも再計算して感度確認】（A/B レポートの注意点）。
3) メッシュ：自動メッシュ + 翼面局所細分化（板厚方向に最低 3 要素、OpenFOAM level4≈0.47mm 相当）。
   回転領域円筒にも細分化。
4) 実行：壁面力 Fz をモニタしながら収束まで。
5) 結果抽出：Wall Calculator でプロペラ壁の【力 Z 成分 = 推力】、【モーメント Z = トルク】。
   推力係数 Ct = |Fz| / (ρ n² D⁴), ρ=1.225, n=1.667 rev/s, D=掃引直径。
6) 比較・反復：Case A/B（reports/summary.md の表）と同じ土俵で比較。Fz が A/B を上回るよう
   形状（翼端面積・ソリディティ・キャンバ・軸方向高さの使い方）を反復改良。

═══════════════════════════════════════════════════════════════════
■ 5. 成果物・規約・レポート（A/B と統一）
═══════════════════════════════════════════════════════════════════
- geometry/caseC/caseC.step（mm, Z=回転軸）, assets/caseC_iso/top/side.png
- 設計スクリプト：scripts/caseC_fusion.py（Fusion API）, CFD 自動化スクリプト（あれば）
- reports/caseC.md を【次の 5 構成】で日本語記述：
  1. 設計のコンセプト（何に着目し、A/B と何を比較するのか。テンプレート不使用の独自性）
  2. 計算条件（Re 等の相似則, 境界条件, メッシュ, 回転領域）
  3. 考察（推力・トルク・Ct, 流れ場可視化, A/B との比較, 参考文献との対比）
  4. まとめ
  5. 参考文献
- reports/summary.md の比較表に Case C 行を追記。
- 制約充足（D≤100, H≤60, 100rpm）を明記。
- 作業完了後、変更を git にコミット（OpenFOAM 同様、巨大な中間データは .gitignore 済みの
  方針に倣い、CFD の大容量結果はコミットしない。STEP・スクリプト・レポート・図は残す）。

═══════════════════════════════════════════════════════════════════
■ 6. 進め方の注意
═══════════════════════════════════════════════════════════════════
- 形状の絶対推力は µN オーダーで数値ノイズを含む。重要なのは A/B/C の【相対比較】。
- API の正確な呼び出しは必ず公式 docs / ローカル Help で確認（憶測しない）。
- インストールやサインインなど人手が要る所はユーザーに具体的に依頼する。
- 不明点・設計判断が割れる所はユーザーに確認してから進める。
```

---

## このプロンプトの使い方（人間向けメモ）

1. Windows 側に本リポジトリを clone（または同期）する。
2. その作業ディレクトリで Claude Code を起動する。
3. 上のコードブロック内テキストを丸ごと最初のメッセージとして貼り付ける。
4. 必要に応じて、Fusion / Autodesk CFD のサインイン・ライセンス認証を先に済ませておくと
   スムーズ（未了でも Claude が検出して依頼してくる）。
