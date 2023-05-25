from login_get_kite import get_kite
from toolkit.fileutils import Fileutils

sec_dir = "../../../confid/"
yaml_file = "zerodha.yaml"
kwargs = Fileutils().get_lst_fm_yml(sec_dir + yaml_file)
addend = {"api_type": "zerodha", "sec_dir": sec_dir}
kwargs.update(addend)
kite = get_kite(**kwargs)
print(kite.profile)
