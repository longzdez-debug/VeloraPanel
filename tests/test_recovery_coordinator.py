from velora.recovery_coordinator import RecoveryCoordinator


def test_recovery_escalates_and_limits():
    c=RecoveryCoordinator(max_recoveries=2)
    a=c.observe("stuck",4.0,0.9,10.0)
    b=c.observe("stuck",4.0,0.9,20.0)
    d=c.observe("stuck",4.0,0.9,30.0)
    assert a and a.level==1 and a.action=="micro_correction"
    assert b and b.level==2 and b.action=="local_replan"
    assert d and d.level==6 and d.action=="navigation_reset"


def test_low_localization_escalates_to_relocalize():
    c=RecoveryCoordinator(max_recoveries=3)
    d=c.observe("stuck",4.0,0.2,10.0)
    assert d and d.action=="relocalize" and d.level>=4
