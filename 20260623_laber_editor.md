# Label Editor 작업 내역 — 2026-06-23

## 구현된 기능

### 1. Faint Label View (V 단축키)
- V 키로 label 오버레이 투명도를 토글
- 일반 모드: opacity **0.8**
- Faint 모드: opacity **0.22**
- View 메뉴에 "Faint Label &View" 항목 추가 (V에 밑줄 표시)
- 이미지 이동 시에도 모드 유지

### 2. Gamma Curve (G 단축키)
- 신규 파일: `labeler/gamma_dialog.py`
  - `compute_lut(ctrl)` : scipy CubicSpline으로 256-element uint8 LUT 생성
  - `GammaCurveWidget` : 제어점 3개 고정(x=0/128/255), y축 드래그로 조정
  - `GammaCurveDialog` : 위젯 + Reset to Default + Close 버튼
- View 메뉴에 "Apply &Gamma" (G 단축키), "Gamma Curve Setting" 항목 추가
- G 키로 gamma on/off 토글
- 제어점 y값 3개를 QSettings에 저장 → 앱 재실행 시 복원
- canvas에 `set_gamma_lut()`, `set_gamma_enabled()`, `_apply_pixmap_gamma()`, `_gamma_apply()` 추가
  - `_gamma_apply`: QImage를 Format_RGB32로 변환 후 numpy LUT 적용

### 3. Labels 패널 개선
- `setMaximumHeight(140)` 제거 → 세로 공간 적응적으로 확장
- `rv.addWidget(lg, stretch=1)` 적용으로 사용 가능한 공간 자동 확장
- 새 annotation commit 시 해당 항목 위치로 자동 스크롤 (`scrollToItem`)

### 4. Labels 자동 정렬
- 새 annotation이 추가될 때마다 Classes 패널 순서 기준으로 자동 정렬
- `MaskManager.sort_by_category_order(cat_order)` 를 `_on_annotation_committed` 에서 호출

### 5. Change Label Class (콤보박스)
- Labels 패널 아래 QComboBox 추가
- label 선택 시 해당 annotation의 현재 클래스 표시
- 클래스 변경 → `change_annotation_category()` → `sort_by_category_order()` → 목록 갱신 → 동일 annotation 재선택
- `MaskManager`에 신규 메서드:
  - `change_annotation_category(ann_id, new_cat_id) -> bool`
  - `sort_by_category_order(cat_order: List[int])`

### 6. 브러쉬 크기 최대값 확장 및 단축키 버그 수정
- 최대 브러쉬 크기: 50 → **88**
- `[` / `]` 단축키 버그 수정
  - 기존: canvas `keyPressEvent`에서만 처리 → 다른 위젯에 포커스 시 동작 안 함
  - 수정: canvas에서 제거, window 레벨 `QAction` (WindowShortcut context)으로 이전
    → 포커스 위치와 무관하게 항상 동작
  - `_act_brush_dec` / `_act_brush_inc` QAction → slider.setValue → `_on_slider_changed` → `canvas.set_brush_size`

---

## 변경된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `labeler/gamma_dialog.py` | **신규** — GammaCurveWidget, GammaCurveDialog, compute_lut |
| `labeler/canvas.py` | faint/gamma API 추가, opacity 상수, brush size 88, `[`/`]` 제거 |
| `labeler/mask_manager.py` | `change_annotation_category`, `sort_by_category_order` 추가 |
| `labeler/window.py` | View 메뉴 항목, Labels 패널 레이아웃, 콤보박스, 정렬, 단축키 QAction |

---

## 최종 opacity 값

| 모드 | opacity |
|------|---------|
| 일반 | 0.8 |
| Faint | 0.22 |

---

## Git 커밋 목록

| 커밋 | 내용 |
|------|------|
| `16ca39a` | feat: faint mode (V), gamma curve (G), adaptive label panel, change label class |
| `f754735` | fix: brush size max 88, [ ] shortcuts work regardless of focus |
| `0baa185` | feat: sort Labels panel by class order on each new annotation |
| `deebc68` | ui: rename View menu items (Faint Label View, Gamma Curve Setting) |
| `e16c654` | ui: increase faint mode opacity 0.12 → 0.22 |
| `1eb4f15` | ui: set normal overlay opacity to 0.88 |
| `5df31f1` | ui: normal overlay opacity 0.88 → 0.8 |
