from velora.stats import StatsStore
def test_stats_record():
 s=StatsStore();s.record_match("a",xp_delta=100,win=True);assert s.get("a").xp==100 and s.get("a").wins==1
