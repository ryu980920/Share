* =====================================================================
*  BCAT Id-Vg 시뮬레이션 — Sentaurus Device
*  GIDL(BTBT) 포함. 선형/포화 2회 스윕으로 Vth·SS·DIBL·Ion·GIDL 전부 추출.
*
*  ★★ 골격이다. Phase 0에서 설치된 버전의 SDevice User Guide로 문법 검증할 것.
*      TODO-MODEL 표시 지점이 검증 대상.
*
*  ★ 격자점마다 바뀌는 것은 구조 파일(@tdr@)뿐이다.
*    이 파일의 물리 모델·바이어스는 25개 격자점 전부 동일해야 한다.
*    여기를 혼자 고치면 그 사람의 격자점만 다른 값이 나오고, 등고선이 거짓말이 된다.
* =====================================================================

File {
   Grid      = "@tdr@"
   Parameter = "@parameter@"
   Plot      = "@tdrdat@"
   Current   = "@plot@"
   Output    = "@log@"
}

Electrode {
   { Name="gate"      Voltage=0.0  Workfunction=4.8 }   * 텅스텐. params.yaml 과 일치
   { Name="source"    Voltage=0.0 }
   { Name="drain"     Voltage=0.0 }
   { Name="substrate" Voltage=0.0 }
}

Physics {
   AreaFactor = 1

   Mobility (
      DopingDependence
      HighFieldSaturation
      Enormal
   )

   EffectiveIntrinsicDensity ( OldSlotboom )

   Recombination (
      SRH ( DopingDependence )
      Auger
      * ---- GIDL 의 핵심 ----------------------------------------
      * TODO-MODEL: 아래 3종 중 하나를 선택. C 담당이 3종 다 돌려 근거를 만든다.
      *   Band2Band ( Model = NonlocalPath )   ← 기본값. 동적 비국소 경로
      *   Band2Band ( Model = Hurkx )
      *   Band2Band ( Model = Schenk )
      Band2Band ( Model = NonlocalPath )
   )
}

* 밴드갭 협소화 — 고농도 S/D 에서 필요
Physics ( Material = "Silicon" ) {
   EffectiveIntrinsicDensity ( BandGapNarrowing (OldSlotboom) )
}

Plot {
   eDensity  hDensity
   eCurrent/Vector  hCurrent/Vector  TotalCurrent/Vector
   ElectricField/Vector  Potential  SpaceCharge
   Doping  DonorConcentration  AcceptorConcentration
   BandGap  ConductionBandEnergy  ValenceBandEnergy
   eBand2BandGeneration  hBand2BandGeneration      * ← GIDL 발생 위치 시각화용. 반드시 켤 것
   SRHRecombination
}

Math {
   Extrapolate
   Derivatives
   RelErrControl
   Digits       = 5
   ErrRef(electron) = 1e10
   ErrRef(hole)     = 1e10
   Notdamped    = 100
   Iterations   = 20
   Method       = Blocked
   SubMethod    = ParDiSo
   ExitOnFailure
   * 3D 병렬. 각자 PC 코어 수에 맞게 조정 (결과에는 영향 없음)
   Number_of_Threads = 4
}

* =====================================================================
*  Solve — 선형(Vd=0.1V) / 포화(Vd=1.0V) 두 번의 Id-Vg
* =====================================================================
Solve {
   * --- 초기해 ---
   Coupled ( Iterations=100 ) { Poisson }
   Coupled { Poisson Electron Hole }

   * ================= 1) 선형영역: Vd = 0.1 V =========================
   Quasistationary (
      InitialStep=0.05 MaxStep=0.1 MinStep=1e-5
      Goal { Name="drain" Voltage=0.1 }
   ) { Coupled { Poisson Electron Hole } }

   NewCurrentPrefix = "IdVg_lin_"
   * Vg: 0 -> -1.0 V  (GIDL 구간)
   Quasistationary (
      InitialStep=0.02 MaxStep=0.02 MinStep=1e-6
      Goal { Name="gate" Voltage=-1.0 }
   ) { Coupled { Poisson Electron Hole } }
   * Vg: -1.0 -> +2.8 V  (서브스레숄드 ~ 온상태)
   Quasistationary (
      InitialStep=0.01 MaxStep=0.02 MinStep=1e-6
      Goal { Name="gate" Voltage=2.8 }
   ) { Coupled { Poisson Electron Hole } }

   * 게이트 원위치
   Quasistationary (
      InitialStep=0.05 MaxStep=0.1 MinStep=1e-5
      Goal { Name="gate" Voltage=0.0 }
   ) { Coupled { Poisson Electron Hole } }

   * ================= 2) 포화영역: Vd = 1.0 V =========================
   Quasistationary (
      InitialStep=0.05 MaxStep=0.1 MinStep=1e-5
      Goal { Name="drain" Voltage=1.0 }
   ) { Coupled { Poisson Electron Hole } }

   NewCurrentPrefix = "IdVg_sat_"
   Quasistationary (
      InitialStep=0.02 MaxStep=0.02 MinStep=1e-6
      Goal { Name="gate" Voltage=-1.0 }
   ) { Coupled { Poisson Electron Hole } }
   Quasistationary (
      InitialStep=0.01 MaxStep=0.02 MinStep=1e-6
      Goal { Name="gate" Voltage=2.8 }
   ) { Coupled { Poisson Electron Hole } }
}

* =====================================================================
*  수렴 실패 시 (기획서 5-2절)
*   - 강한 전계 조건(낮은 Vg + 높은 Vd)에서 자주 발생한다
*   - 대처 순서: MinStep 낮추기 → Notdamped 늘리기 → Iterations 늘리기
*                → 그래도 안 되면 Method=Blocked / SubMethod=Ils 시도
*   - ★ 수렴을 위해 물리 모델을 끄는 것은 금지. 그 격자점만 물리가 달라진다.
*     정 안 되면 Issue 를 열고 팀 전체가 같은 설정을 쓰도록 합의한 뒤 바꾼다.
* =====================================================================
