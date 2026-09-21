from velora.storage import JsonStore
def test_atomic_store(tmp_path):
 s=JsonStore(str(tmp_path));s.save("x",{"ok":True});assert s.load("x",{})=={"ok":True}
