* =====================================================================
*  FinFET pMOS + Embedded SiGe S/D — Stress Transfer Efficiency 추출 — Sentaurus Device
*
*  ★★★ 이 파일도 처음부터 지어낸 게 아니라 TODO 골격이다. 아직 실제
*  Sentaurus 에서 검증되지 않았다 — 반드시 실제 Sentaurus 에서 테스트할 것. ★★★
*
*  파일명 이력: bcat_sdevice.cmd(예전 BCAT 프로젝트 잔재, 내용 무관)
*  → finfet_sdevice.cmd (2026-08-04 개명, 이름은 유지). 구조 스크립트는
*  finfet_sde.scm → finfet_sprocess.scm 으로 개명됨(2026-08-05, STE 전환).
*
*  ============================ 시작 방법 ============================
*  1. Sentaurus FinFET_14nm 예제(Munkang Choi, Synopsys, 2013)의 SDevice
*     커맨드 파일을 그대로 이 파일 위치에 복사해 온다. 지금 내용은
*     자리표시자이니 덮어써도 된다.
*  2. 아래 TODO 항목 순서대로 수정한다.
*  ★ 격자점마다 바뀌는 것은 구조 파일(@tdr@, Ge%/FR 반영)뿐이어야 한다.
*    이 파일의 물리 모델·추출 설정은 모든 격자점에서 동일해야 한다 —
*    안 그러면 STE 지도가 거짓말이 된다 (기존 BCAT 프로젝트의 규칙 그대로 승계).
* =====================================================================

File {
   Grid      = "@tdr@"
   Parameter = "@parameter@"
   Plot      = "@tdrdat@"
   Current   = "@plot@"
   Output    = "@log@"
}

* ---------------------------------------------------------------------
*  TODO-ELECTRODE : 원본 예제의 Electrode 이름을 그대로 가져올 것.
*  finfet_sprocess.scm 의 컨택 이름과 반드시 일치해야 한다.
*  ★ 이 서브구조엔 게이트 재질이 없다(params.yaml geometry.gate_material_present:
*    false) — 원본 예제에 게이트 관련 전극이 없다면 이 블록 자체가 필요
*    없을 수 있다. 원본을 열어 확인할 것.
* ---------------------------------------------------------------------
Electrode {
*  { Name="source"    Voltage=0.0 }
*  { Name="drain"     Voltage=0.0 }
*  { Name="substrate" Voltage=0.0 }
}

* =====================================================================
*  TODO-STRESS-EXTRACT : 응력 텐서 출력을 확인/보강하는 지점
*
*  README.md/params.yaml 확인 결과, 이 예제는 StressELXX/YY/ZZ 필드를
*  ★이미 doping 명령으로 출력하고 있다 — 추출 자체는 새로 만들 필요 없이
*  TODO-BASE(finfet_sprocess.scm)에서 예제 원본을 그대로 복사해 오면
*  이 파일에도 대응하는 Physics/Plot 설정이 이미 있을 가능성이 높다.
*  이 파일을 원본으로 덮어쓴 뒤, 아래 항목만 확인할 것:
*    1. StressELXX/YY/ZZ 가 Plot 블록에 실제로 포함돼 있는지
*    2. 이 값이 GPa 단위인지 다른 단위(Pa, dyn/cm^2 등)인지 — analysis/config.yaml
*       의 STE 계산이 이 단위를 전제로 한다
*  ★ 이 프로젝트는 결함(전위) 모델 유무를 더 이상 확인하지 않는다 —
*    People-Bean/Luryi-Suhir 결함 경계 프레이밍을 폐기했기 때문이다
*    (README.md 참고). 이 Physics 블록은 순수하게 응력 필드 추출용이다.
* =====================================================================
Physics {
*  TODO: 원본 예제의 Stress/Strain 관련 키워드 그대로 사용 (지어내지 않는다)

   Mobility (
      * TODO: 원본 예제에 이동도 모델이 있다면 그대로 유지. STE 지표는
      * 이동도가 아니라 응력 비율이므로 이 블록이 필수는 아닐 수 있다 —
      * 원본 예제 구성에 따라 결정.
      DopingDependence
      HighFieldSaturation
      Enormal
   )
}

Plot {
   eDensity  hDensity
*  TODO-STRESS-PLOT : StressELXX/YY/ZZ 가 이미 있는지 확인, 없으면 원본
*  예제의 정확한 키워드로 추가할 것 (지어내지 않는다)
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
*  TODO-SOLVE : 응력 추출 시퀀스
*
*  이 서브구조엔 게이트 재질이 없고(순수 응력 계산용), 원본 예제가
*  Mechanical 전용 노드를 따로 두는지 확인할 것. 전기적 바이어스 없이
*  구조 응력만 뽑는 것으로 충분할 가능성이 높다 — 정확한 Solve 문법은
*  원본 예제를 보고 결정할 것. 지어내지 말 것.
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
