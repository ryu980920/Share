;; =====================================================================
;;  BCAT 3D 구조 생성 — Sentaurus Structure Editor (Scheme)
;;  차세대반도체 경진대회 / DBCAT x Elevated S/D 결합 최적화
;;
;;  ★★ 이 파일은 "골격"이다. Phase 0에서 반드시 검증·보정할 것. ★★
;;      TODO-GEOM 표시 지점은 논문 Fig.1 단면과 대조해 수치를 확정한다.
;;      설치된 Sentaurus 버전의 SDE User Guide로 문법을 확인한다.
;;
;;  스윕 변수는 딱 두 개. Workbench가 @...@ 를 치환한다.
;;    @DBCAT@ : 질화막 두께 [nm]           (24 / 30 / 36 / 42 / 48)
;;    @NMULT@ : S/D 도핑 배수 [-]          (0.30 / 0.50 / 0.70 / 0.85 / 1.00)
;;  ※ 다른 값을 격자점마다 바꾸지 말 것. 바꾸면 두 변수의 효과가 섞인다.
;; =====================================================================

(sde:clear)
(sde:set-process-up-direction "+z")

;; ---------------------------------------------------------------
;;  1. 파라미터  (baseline/params.yaml 과 반드시 일치시킬 것)
;; ---------------------------------------------------------------
(define DBCAT   (/ @DBCAT@ 1000.0))   ; 질화막 두께 [um]  ★스윕 X
(define NMULT   @NMULT@)              ; 도핑 배수   [-]   ★스윕 Y

(define Lg        0.020)   ; 게이트 길이 20 nm
(define Drec      0.120)   ; 리세스 깊이 120 nm
(define Tox       0.005)   ; 게이트 산화막 5 nm
(define Wfin      0.030)   ; TODO-GEOM: 핀 폭 — 논문에서 확인
(define Xj        0.040)   ; TODO-GEOM: 접합 깊이 — 논문에서 확인
(define Wdev      0.100)   ; y 방향 소자 폭
(define Tsub      0.300)   ; 기판 두께
(define Lsd       0.050)   ; S/D 영역 길이

(define Nch       1.0e18)  ; 채널 도핑 (p)
(define Nsd_base  1.0e20)  ; S/D 피크 도핑 기준값 (n)
(define Nsd       (* Nsd_base NMULT))   ; ★ 여기서 도핑 스윕이 적용된다

;; ---------------------------------------------------------------
;;  2. 실리콘 기판
;; ---------------------------------------------------------------
(sdegeo:create-cuboid
  (position (- 0 Lsd) 0 (- 0 Tsub))
  (position (+ Lg Lsd) Wdev 0)
  "Silicon" "R.Substrate")

;; ---------------------------------------------------------------
;;  3. 리세스 트렌치 식각  (새들핀 채널 형성)
;;     TODO-GEOM: 새들핀 형상(핀이 트렌치 바닥에서 돌출)은
;;                트렌치를 판 뒤 핀 부분을 다시 채우는 2단계로 구현한다.
;; ---------------------------------------------------------------
(sdegeo:create-cuboid
  (position 0 0 (- 0 Drec))
  (position Lg Wdev 0)
  "Silicon" "R.TrenchCut")
(sdegeo:bool-subtract (list (find-body-id (position (/ Lg 2) (/ Wdev 2) (- 0 (/ Drec 2))))))

;; 새들핀 복원 (트렌치 중앙에 핀 형태로 실리콘을 남김)
(sdegeo:create-cuboid
  (position 0 (- (/ Wdev 2) (/ Wfin 2)) (- 0 Drec))
  (position Lg (+ (/ Wdev 2) (/ Wfin 2)) 0)
  "Silicon" "R.SaddleFin")

;; ---------------------------------------------------------------
;;  4. 게이트 산화막 (리세스 내벽 + 핀을 감쌈)
;; ---------------------------------------------------------------
(sdegeo:create-cuboid
  (position (- 0 Tox) (- 0 Tox) (- 0 (+ Drec Tox)))
  (position (+ Lg Tox) (+ Wdev Tox) 0)
  "SiO2" "R.GateOx")
;; TODO-GEOM: 위 큐보이드에서 실리콘과 겹치는 부분을 bool-subtract 로 제거해
;;            실제 산화막 껍질만 남길 것. SDE 의 bool-subtract2 사용 권장.

;; ---------------------------------------------------------------
;;  5. 텅스텐 게이트 — ★ DBCAT 이 여기서 결정된다
;;
;;     게이트 윗면 z = -DBCAT.
;;     DBCAT 이 클수록 게이트가 깊이 묻히고,
;;     표면(z=0)의 게이트-드레인 겹침이 줄어든다.  ← 이것이 우리 가설의 물리
;; ---------------------------------------------------------------
(sdegeo:create-cuboid
  (position 0 0 (- 0 Drec))
  (position Lg Wdev (- 0 DBCAT))       ; ★★ 게이트 상단 = -DBCAT
  "Tungsten" "R.Gate")

;; ---------------------------------------------------------------
;;  6. 질화막 캡  (게이트 위 ~ 표면. 두께가 곧 DBCAT)
;; ---------------------------------------------------------------
(sdegeo:create-cuboid
  (position 0 0 (- 0 DBCAT))
  (position Lg Wdev 0)
  "Si3N4" "R.NitrideCap")

;; ---------------------------------------------------------------
;;  7. Elevated Source / Drain  — ★ NMULT 가 여기에 적용된다
;; ---------------------------------------------------------------
(sdegeo:create-cuboid
  (position (- 0 Lsd) 0 0) (position 0 Wdev 0.030)
  "Silicon" "R.SourceElev")
(sdegeo:create-cuboid
  (position Lg 0 0) (position (+ Lg Lsd) Wdev 0.030)
  "Silicon" "R.DrainElev")

;; ---------------------------------------------------------------
;;  8. 도핑 프로파일
;; ---------------------------------------------------------------
(sdedr:define-constant-profile "P.Channel" "BoronActiveConcentration" Nch)
(sdedr:define-constant-profile-region "PL.Channel" "P.Channel" "R.Substrate")

(sdedr:define-gaussian-profile "P.SD"
  "ArsenicActiveConcentration"
  "PeakPos" 0 "PeakVal" Nsd            ; ★ Nsd = Nsd_base * NMULT
  "ValueAtDepth" 1e17 "Depth" Xj
  "Gauss" "Factor" 0.8)
(sdedr:define-analytical-profile-placement "PL.Source" "P.SD" "RefWin.Source" "Both" "NoReplace" "Eval")
(sdedr:define-analytical-profile-placement "PL.Drain"  "P.SD" "RefWin.Drain"  "Both" "NoReplace" "Eval")
;; TODO-GEOM: RefWin.Source / RefWin.Drain 참조 윈도우를 sdedr:define-refeval-window 로 정의할 것

;; ---------------------------------------------------------------
;;  9. 컨택  ★ 이름은 SDevice 의 Electrode 이름과 반드시 일치
;; ---------------------------------------------------------------
(sdegeo:define-contact-set "gate"      4 (color:rgb 1 0 0) "##")
(sdegeo:define-contact-set "source"    4 (color:rgb 0 1 0) "##")
(sdegeo:define-contact-set "drain"     4 (color:rgb 0 0 1) "##")
(sdegeo:define-contact-set "substrate" 4 (color:rgb 1 1 0) "##")
;; TODO-GEOM: 각 컨택을 해당 면(face)에 set-current-contact-set + define-3d-contact 로 할당

;; ---------------------------------------------------------------
;;  10. 메쉬  ★★ GIDL 결과의 신뢰성이 여기서 갈린다 ★★
;;
;;      GIDL 은 게이트-드레인 겹침부에 극도로 국소화된 표면 현상이다.
;;      전역 메쉬만 쓰면 BTBT 생성률이 과소평가되어 결과가 통째로 틀린다.
;;      이 국소 정밀화 박스는 절대 지우지 말 것.
;; ---------------------------------------------------------------
(sdedr:define-refinement-size "RS.Global" 0.020 0.020 0.020 0.005 0.005 0.005)
(sdedr:define-refinement-region "RR.Global" "RS.Global" "R.Substrate")

;; 겹침부 국소 정밀화 — 드레인 쪽 표면 코너, z = -DBCAT 근방
(sdedr:define-refeval-window "RW.Overlap" "Cuboid"
  (position (- Lg 0.015) 0 (- 0 (+ DBCAT 0.015)))
  (position (+ Lg 0.020) Wdev 0.005))
(sdedr:define-refinement-size "RS.Overlap" 0.002 0.010 0.001 0.0005 0.002 0.0002)
(sdedr:define-refinement-placement "RP.Overlap" "RS.Overlap" "RW.Overlap")

;; 채널 표면 정밀화
(sdedr:define-refinement-size "RS.Channel" 0.004 0.004 0.002 0.001 0.001 0.0005)
(sdedr:define-refinement-region "RR.Channel" "RS.Channel" "R.SaddleFin")

;; ---------------------------------------------------------------
;;  11. 빌드 & 저장
;; ---------------------------------------------------------------
(sde:build-mesh "snmesh" "-a -c boxmethod" "n@node@_msh")
(sde:save-model "n@node@_sde")
