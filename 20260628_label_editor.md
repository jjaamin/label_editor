# Label Editor 작업 내역 — 2026-06-28

## 구현된 기능 및 버그 수정

### 1. EdgeSAM ONNX 전환 (Magic Wand)
- Python 3.13에서 mmcv/mmdet `pkgutil.ImpImporter` 오류 → `onnxruntime` 기반으로 완전 교체
- `labeler/sam_worker.py` 전면 재작성: encoder/decoder ONNX 모델 로드, GPU/CPU 자동 선택
- `download_weights.py` 재작성: `edge_sam_3x_encoder.onnx`, `edge_sam_3x_decoder.onnx` 다운로드
- GPU 없는 PC: `pip install onnxruntime` (CPU 동작)
- GPU PC: `pip install onnxruntime-gpu==1.20.1` (CUDA 12.x + cuDNN 9)
- PyTorch 번들 `cudnn64_9.dll` PATH 자동 추가로 cuDNN 별도 설치 불필요
- `requirements.txt` 업데이트

### 2. Magic Wand 아이콘 개선
- Windows 10에서 🪄 (Unicode 13.0) 미지원 → QPainter로 직접 그린 아이콘으로 교체
- 보라색 지팡이 + 8방향 무지개 광선 + 금색 중심 원

### 3. `[` / `]` 키 — Magic Wand 마스크 후보 선택
- Magic Wand 모드에서 `[` / `]`로 3개 SAM 마스크 후보 순환 (1/3 ~ 3/3)
- 브러시 모드에서는 기존대로 브러시 크기 조절

### 4. LabelMe 좌표 보존
- 기존: 저장 시 mask → findContours → approxPolyDP 단순화로 좌표 손실
- 수정: `Annotation.original_polygons` 필드 추가
  - LabelMe JSON 로드 시 원본 좌표 보존
  - Draw 툴로 그린 폴리곤: 찍은 좌표 그대로 저장
  - 컨트롤포인트 드래그 후: 편집된 좌표 저장
  - 브러시 편집 시: `original_polygons = None` → 마스크에서 추출
- fallback 추출: `CHAIN_APPROX_NONE` + approxPolyDP 제거 → 고밀도 전체 픽셀 저장

### 5. JSON 자동 로딩 / 자동 저장 제어
- 자동 로딩: 폴더 열 때 JSON 있으면 자동 로드, 이미지 전환 시 per-image 지연 로딩
- 자동 저장 제거: 명시적 `Ctrl+S` 또는 "Save to Folder…"로만 저장
- 빈 어노테이션 JSON 생성 방지: 어노테이션 없는 이미지는 JSON 파일 미생성

### 6. Pan (H) 토글
- `H` 첫 번째: 현재 도구 저장 후 Pan 모드 진입
- `H` 두 번째: 저장된 이전 도구로 복귀

### 7. 이미지 목록 JSON 아이콘 표시
- 우측 이미지 목록에 JSON 존재 여부를 파란 문서 아이콘으로 표시
- 폴더 열기 / 저장 / 로드 시 자동 갱신

### 8. 종료 시 저장 확인 다이얼로그
- 기존: "Discard unsaved changes?" (Yes/No)
- 수정: **Save / Discard / Cancel** 3버튼으로 변경
- 닫기 및 새 폴더 열기 시 모두 적용

### 9. 레이블 재선택 버그 수정
- 편집 후 Enter/Esc 누르면 같은 레이블 클릭 시 `currentRowChanged` 미발생 문제
- `_on_edit_cleared`에 `setCurrentRow(-1)` 추가로 해결

### 10. 브러시 모드 컨트롤포인트 동작 개선
- 브러시 모드 진입 시 컨트롤포인트 dots: 작고 흐리게 표시 (위치 참고용)
  - 외곽선: 노란색 반투명 (alpha 110), 반지름 4
  - 내부: 시안 반투명 (alpha 50)
- 브러시 모드에서 컨트롤포인트 드래그 완전 비활성화
- Space 임시 Pan: 브러시 모드에서도 정상 동작 (기존 버그 수정)

### 11. 컨트롤포인트 크기 조정
- 편집 모드(IDLE) 기준 반지름 5 → 3으로 축소

### 12. 브러시 크기 단축키 가변 스텝
- `[` / `]` 키 스텝:
  - 1 ~ 30: 간격 1
  - 31 ~ 60: 간격 2
  - 61 ~ 88: 간격 4

---

## 변경된 파일

| 파일 | 변경 내용 |
|---|---|
| `labeler/sam_worker.py` | EdgeSAM ONNX 추론으로 전면 재작성 |
| `labeler/canvas.py` | Magic Wand 개선, 컨트롤포인트 스타일, Space 팬 버그 수정, 좌표 보존 |
| `labeler/window.py` | Pan 토글, JSON 아이콘, 저장 다이얼로그, 레이블 버그 수정, 가변 스텝 |
| `labeler/mask_manager.py` | `Annotation.original_polygons` 필드, CHAIN_APPROX_NONE |
| `labeler/coco_io.py` | 좌표 보존 저장/로드, 빈 JSON 생성 방지 |
| `download_weights.py` | ONNX 모델 다운로드로 재작성 |
| `requirements.txt` | onnxruntime 추가 |
| `README.md` | 사용 설명서 신규 작성 |
| `FEATURES.md` | 기능 요약 페이지 신규 작성 |

---

## Git 커밋 목록

| 커밋 | 내용 |
|---|---|
| `d8188f1` | Restore JSON auto-load on folder open and image navigation |
| `184d38b` | Toggle pan mode with H key — second press returns to previous tool |
| `858b570` | Preserve polygon point precision on save — no simplification for drawn/dragged polygons |
| `ed608a9` | Show JSON document icon in image list when annotation file exists |
| `30b848e` | Fix label re-selection after edit; hide contour dots in brush mode |
| `522a3ac` | Show Save/Discard/Cancel dialog on close or folder switch with unsaved changes |
| `3a0315e` | Use CHAIN_APPROX_NONE for full-density contour extraction |
| `348594c` | Skip writing JSON for images with no annotations |
| `1d0f022` | Add user manual (README.md) in Korean |
| `d130796` | Replace index.html with FEATURES.md |
| `f57c976` | Fix Space temporary pan in Brush mode |
| `caf619a` | Disable contour point dragging in Brush mode |
| `0911415` | Show faint small dots in brush mode — visible reference, not draggable |
| `8be6aa1` | Variable brush size step: 1 (≤30), 2 (≤60), 4 (>60) |
| `00be24a` | Brush mode dots: yellow outline, cyan fill, smaller size |
| `04a7d86` | Increase brush mode dot radius to 4 |
| `c9471c6` | Reduce contour control point radius from 5 to 3 |
