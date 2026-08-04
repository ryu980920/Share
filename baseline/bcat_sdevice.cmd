* =====================================================================
*  FinFET + Embedded SiGe S/D — 응력/이동도 추출 — Sentaurus Device
*
*  ★★★ 이 파일도 처음부터 지어낸 게 아니라 TODO 골격이다. ★★★
*  파일명이 bcat_sdevice.cmd 인 이유는 bcat_sde.scm 과 동일 (레포 구조 재사용).
*
*  ============================ 시작 방법 ============================
*  1. FinFET_14nm/22nm 예제의 SDevice 커맨드 파일을 그대로 이 파일 위치에
*     복사해 온다. 지금 내용은 자리표시자이니 덮어써도 된다.
*  2. 아래 TODO 항목 순서대로 수정한다.
*  ★ 격자점마다 바뀌는 것은 구조 파일(@tdr@)뿐이어야 한다. 이 파일의
*    물리 모델·바이어스는 모든 격자점에서 동일해야 한다 — 안 그러면
*    등고선이 거짓말이 된다 (기존 BCAT 프로젝트의 규칙 그대로 승계).
* =====================================================================

File {
   Grid      = "@tdr@"
   Parameter = "@parameter@"
   Plot      = "@tdrdat@"
   Current   = "@plot@"
   Output    = "@log@"
}

* ---------------------------------------------------------------------
*  TODO-ELECTRODE : 원본 예제의 Electrode 이름/Workfunction 을 그대로 가져올 것.
*  bcat_sde.scm 의 컨택 이름과 반드시 일치해야 한다.
* ---------------------------------------------------------------------
Electrode {
*  { Name="gate"      Voltage=0.0  Workfunction=??? }   * TODO: params.yaml materials.gate_workfunction_eV 확정 후 반영
*  { Name="source"    Voltage=0.0 }
*  { Name="drain"     Voltage=0.0 }
*  { Name="substrate" Voltage=0.0 }
}

* =====================================================================
*  TODO-STRESS-PHYSICS : 응력/변형(strain) 계산을 켜는 지점
*
*  Sentaurus Device 의 Stress 관련 물리는 보통 아래 형태 중 하나로 켠다
*  (정확한 키워드는 설치 버전 SDevice User Guide 의 "Mechanical Stress"
*  또는 "Strain" 장에서 확인할 것 — 지어내지 말 것):
*    Physics { Stress ( ... ) }               또는
*    Math { -Stress ... }                     또는
*    별도의 MechanicalSolve 섹션
*
*  ★ 확인해야 할 것 (docs/technical-notes.md 4절 항목 3 과 동일):
*    이 Stress 섹션에 전위결함(소성 완화) 예측 모델이 기본 포함돼 있는지.
*    포함 안 돼 있다고 확인되면(현재 가정), People-Bean/Luryi-Suhir 경계선을
*    analysis/contour.py 에서 별도로 오버레이하는 하이브리드 방법론이
*    유일한 선택지가 된다 — 이 파일에서 결함을 억지로 흉내내려 하지 말 것.
* =====================================================================
Physics {
*  TODO: Stress/Strain 관련 키워드 (원본 예제 또는 User Guide 확인 후 채울 것)

   Mobility (
      * TODO: 응력 의존 이동도 모델. 보통 "Stress" 또는 "PiezoResistance"
      * 관련 서브키워드가 필요하다 (미확인 — User Guide 확인 필수).
      DopingDependence
      HighFieldSaturation
      Enormal
   )
}

Plot {
   eDensity  hDensity
*  TODO-STRESS-PLOT : 응력 텐서 성분을 Plot 에 반드시 추가할 것
*  (보통 Stress/Vector 또는 개별 성분 xx/yy/zz 형태 — User Guide 확인)
   eMobility hMobility
}

Math {
   Extrapolate
   Derivatives
   RelErrControl
   Digits       = 5
   Notdamped    = 100
   Iterations   = 20
   Method       = Blocked
   ExitOnFailure
   Number_of_Threads = 4
}

* =====================================================================
*  TODO-SOLVE : 응력/이동도 추출 시퀀스
*
*  순수 구조 응력만 필요하면 전기적 바이어스 없이 Mechanical 솔브만으로
*  충분할 수도 있고(원본 예제가 Mechanical 전용 노드를 따로 두는지 확인),
*  이동도 향상률까지 Id-Vg 로 보려면 기존 BCAT 프로젝트의 Quasistationary
*  스윕 패턴을 참고해 게이트/드레인을 스윕한다.
*  ★ 어느 쪽이 필요한지, 그리고 정확한 Solve 문법은 원본 예제를 보고
*    결정할 것 — 지어내지 말 것.
* =====================================================================
Solve {
*  TODO: 원본 예제의 Solve 시퀀스를 그대로 가져와 채울 것
}

* =====================================================================
*  수렴 실패 시 (기존 BCAT 프로젝트 규칙 승계)
*   - 대처 순서: MinStep 낮추기 → Notdamped 늘리기 → Iterations 늘리기
*                → 그래도 안 되면 Method 변경
*   - ★ 수렴을 위해 물리 모델을 끄는 것은 금지. 그 격자점만 물리가 달라진다.
*     정 안 되면 Issue 를 열고 팀 전체가 같은 설정을 쓰도록 합의한 뒤 바꾼다.
* =====================================================================
